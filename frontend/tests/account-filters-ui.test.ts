// RF28 (e-mail sob demanda na Conta) e RF24 (filtros das Sugestões), com React em jsdom e HTTP fictício.
import assert from "node:assert/strict"
import { test, type TestContext } from "node:test"
import { mountReact, src } from "./helpers/react-harness.ts"

const user = { id: "qa", name: "Fixture", genres: ["RPG"], themes: ["Fantasia"], anchorIds: ["101", "102", "103"],
  hardware: { cpuId: "CPU fixture", gpuId: "GPU fixture", ramGb: 16, os: "Windows", windowsVersion: "11" }, catalogVersion: "steam-v2" }
const hardware = { source: "neo4j", score_version: "manual_v1",
  CPU: [{ id: "CPU fixture", name: "CPU fixture", vendor: "Fixture", performance_score: 10, score_version: "manual_v1" }],
  GPU: [{ id: "GPU fixture", name: "GPU fixture", vendor: "Fixture", performance_score: 20, score_version: "manual_v1" }] }

function game(id: string, title: string) {
  return { id, title, genres: ["RPG"], themes: ["Fantasia"], themes_status: "classified", developer: "Fixture", year: 2026,
    image_url: null, summary: "Fixture", price_text: null, store_url: "https://example.invalid/fixture",
    source: { collected_at: "2026-11-13T00:00:00Z", source_url: "https://example.invalid/fixture" },
    platforms: { Windows: { native_support: true, minimum: null, recommended: null },
      Linux: { native_support: false, minimum: null, recommended: null }, macOS: { native_support: false, minimum: null, recommended: null } } }
}
function match(id: string, title: string, meets: "recommended" | "minimum" | null, ok: boolean | null = true) {
  const checks = ["Processador", "Placa de vídeo", "Memória RAM", "Sistema operacional"].map((label) => ({ label, ok, detail: "Fixture." }))
  const compatibility = ok === false ? "incompatible" : meets ? "compatible" : "needs_review"
  return { game: game(id, title), affinity: 60, reasons: [], preferredGenres: ["RPG"], anchorMatches: [], checks, compatibility, meets,
    compatible: ok !== false && Boolean(meets), estimated: false, anchor: false,
    assessments: { minimum: { available: true, checks, compatibility }, recommended: { available: true, checks, compatibility } } }
}

async function mount(t: TestContext, route: string, element: string, handler: (path: string, options: any) => Response | Promise<Response>) {
  const ui = await mountReact(t, {
    source: `
      import React from 'react';import {createRoot} from 'react-dom/client';
      import {MemoryRouter,Routes,Route,useLocation} from 'react-router-dom';
      import {SessionProvider} from ${src("context/SessionContext.tsx")};
      import {CatalogProvider} from ${src("context/CatalogContext.tsx")};
      import {Account} from ${src("pages/Account.tsx")};
      import {Recommendations} from ${src("pages/Recommendations.tsx")};
      export {React,createRoot};export const probe={};
      function Probe(){probe.location=useLocation();return null}
      export function Harness(){return <SessionProvider><CatalogProvider><MemoryRouter initialEntries={[${JSON.stringify(route)}]}>
        <Probe/><Routes><Route path=${JSON.stringify(route)} element={<${element}/>}/></Routes></MemoryRouter></CatalogProvider></SessionProvider>}
    `,
    fetch: handler,
  })
  await ui.settle()
  const click = async (label: string) => {
    const target = ui.button(label)
    assert(target, `botão "${label}" não encontrado`)
    await ui.click(target)
    await ui.settle()
  }
  const type = async (input: HTMLInputElement, value: string) => { await ui.type(input, value); await ui.settle() }
  return { m: ui.m, dom: ui.dom, requests: ui.log, button: ui.button, click, type, settle: ui.settle }
}

test("RF28: a Conta só busca o e-mail quando a pessoa clica em Mostrar, e Ocultar esconde de novo", { timeout: 20000 }, async (t) => {
  const ui = await mount(t, "/app/conta", "Account", (path) => {
    if (path === "/api/auth/me") return Response.json(user)
    if (path === "/api/hardware") return Response.json(hardware)
    if (path === "/api/games") return Response.json({ items: [], issues: [], source: "neo4j" })
    if (path === "/api/me/interactions") return Response.json({ items: [] })
    if (path === "/api/me/account") return Response.json({ email: "fixture@example.invalid" })
    throw new Error("Requisição inesperada: " + path)
  })
  const line = () => document.querySelector(".account-email")!.textContent!
  assert(!ui.requests.includes("GET /api/me/account"), "o e-mail não pode ser pedido ao abrir a tela")
  assert(!document.body.textContent!.includes("fixture@example.invalid"))
  assert.match(line(), /Mostrar/)

  await ui.click("Mostrar")
  assert.equal(ui.requests.filter((item) => item === "GET /api/me/account").length, 1)
  assert.match(line(), /fixture@example\.invalid/)

  await ui.click("Ocultar")
  assert(!document.body.textContent!.includes("fixture@example.invalid"))
  assert.match(line(), /Mostrar/)
})

test("RF28: falha ao buscar o e-mail mostra o aviso e mantém o e-mail escondido", { timeout: 20000 }, async (t) => {
  const ui = await mount(t, "/app/conta", "Account", (path) => {
    if (path === "/api/auth/me") return Response.json(user)
    if (path === "/api/hardware") return Response.json(hardware)
    if (path === "/api/games") return Response.json({ items: [], issues: [], source: "neo4j" })
    if (path === "/api/me/interactions") return Response.json({ items: [] })
    if (path === "/api/me/account") return Response.json({ detail: "Sessão expirada. Entre novamente." }, { status: 401 })
    throw new Error("Requisição inesperada: " + path)
  })
  await ui.click("Mostrar")
  assert.equal(document.querySelector('.account-panel [role="alert"]')?.textContent, "Sessão expirada. Entre novamente.")
  assert.match(document.querySelector(".account-email")!.textContent!, /Mostrar/)
})

test("RF24: filtros por nome e por situação dos requisitos nas Sugestões", { timeout: 20000 }, async (t) => {
  const anchors = user.anchorIds.map((id) => game(id, `Âncora ${id}`))
  const result = {
    items: [match("201", "Alpha Quest", "recommended"), match("202", "Beta Racer", "minimum"), match("203", "Gamma Quest", "minimum")],
    pending: [match("204", "Delta Quest", null, null)],
    excluded: [match("205", "Omega Block", null, false)],
    anchors, issues: [], source: "neo4j",
    calculation: { engine_version: "rules_v1", minimum_affinity: 28, score_version: "manual_v1", hardware_sha256: "f", curation_sha256: "f" },
  }
  const ui = await mount(t, "/app/recomendacoes", "Recommendations", (path) => {
    if (path === "/api/auth/me") return Response.json(user)
    if (path === "/api/hardware") return Response.json(hardware)
    if (path === "/api/games") return Response.json({ items: anchors, issues: [], source: "neo4j" })
    if (path === "/api/recommendations") return Response.json(result)
    throw new Error("Requisição inesperada: " + path)
  })
  await ui.click("Buscar sugestões")
  const count = () => document.querySelector(".count")!.textContent
  const titles = () => [...document.querySelectorAll(".game-card-shell h3")].map((item) => item.textContent)
  const excludedOpen = () => (document.querySelector("details.excluded") as HTMLDetailsElement | null)?.open ?? null
  assert.equal(count(), "Exibindo 5 de 5 resultados.")
  assert.deepEqual(titles(), ["Alpha Quest", "Beta Racer", "Gamma Quest", "Delta Quest"])

  // Nome: ignora maiúsculas e acentos e vale para todas as seções.
  await ui.type(document.querySelector(".flt-name input") as HTMLInputElement, "QUÉST")
  assert.equal(count(), "Exibindo 3 de 5 resultados.")
  assert.deepEqual(titles(), ["Alpha Quest", "Gamma Quest", "Delta Quest"])
  assert.equal(ui.m.probe.location.search, "?q=QU%C3%89ST")

  // Situação combinada com o nome.
  await ui.click("Apenas mínimos atendidos")
  assert.equal(count(), "Exibindo 1 de 5 resultados.")
  assert.deepEqual(titles(), ["Gamma Quest"])
  assert.equal(ui.button("Apenas mínimos atendidos")!.getAttribute("aria-pressed"), "true")

  await ui.click("Validação pendente")
  assert.deepEqual(titles(), ["Delta Quest"])

  // Sem nome: "Com restrições" abre a lista de jogos com restrição.
  await ui.type(document.querySelector(".flt-name input") as HTMLInputElement, "")
  await ui.click("Com restrições")
  assert.equal(count(), "Exibindo 1 de 5 resultados.")
  assert.deepEqual(titles(), [])
  assert.equal(excludedOpen(), true)
  assert(document.querySelector("details.excluded")!.textContent!.includes("Omega Block"))

  await ui.click("Recomendados atendidos")
  assert.deepEqual(titles(), ["Alpha Quest"])

  // Filtro sem resultado mostra a mensagem própria; "Todos" volta à lista inteira.
  await ui.type(document.querySelector(".flt-name input") as HTMLInputElement, "zzz")
  assert(document.body.textContent!.includes("Nenhum jogo encontrado com esses filtros."))
  await ui.type(document.querySelector(".flt-name input") as HTMLInputElement, "")
  await ui.click("Todos")
  assert.equal(count(), "Exibindo 5 de 5 resultados.")
  assert.equal(ui.m.probe.location.search, "")
})

test("não curtir salva na hora, o card cai e só depois sai da lista", { timeout: 20000 }, async (t) => {
  const anchors = user.anchorIds.map((id) => game(id, `Âncora ${id}`))
  const result = {
    items: [match("301", "Primeiro Jogo", "recommended"), match("302", "Segundo Jogo", "minimum")], pending: [], excluded: [],
    anchors, issues: [], source: "neo4j",
    calculation: { engine_version: "rules_v1", minimum_affinity: 28, score_version: "manual_v1", hardware_sha256: "f", curation_sha256: "f" },
  }
  const reactions: any[] = []
  const ui = await mount(t, "/app/recomendacoes", "Recommendations", (path, options) => {
    if (path === "/api/auth/me") return Response.json(user)
    if (path === "/api/hardware") return Response.json(hardware)
    if (path === "/api/games") return Response.json({ items: anchors, issues: [], source: "neo4j" })
    if (path === "/api/recommendations") return Response.json(result)
    if (path === "/api/me/games/301/reaction") { reactions.push(JSON.parse(options.body)); return Response.json({ gameId: "301", reaction: "disliked", views: 0 }) }
    throw new Error("Requisição inesperada: " + path)
  })
  await ui.click("Buscar sugestões")
  const card = () => [...document.querySelectorAll(".game-card-shell")].find((item) => item.querySelector("h3")?.textContent === "Primeiro Jogo")
  const dislike = card()!.querySelector('button[aria-label="Não curtir este jogo"]')!
  await ui.m.React.act(async () => { dislike.dispatchEvent(new ui.dom.window.MouseEvent("click", { bubbles: true, cancelable: true, button: 0 })) })
  await ui.settle(50)
  assert.deepEqual(reactions, [{ reaction: "disliked" }])  // salvo na hora, sem esperar a animação
  assert(card()?.classList.contains("gone"), "o card não curtido deve estar caindo")
  assert.equal(document.querySelector(".count")!.textContent, "Exibindo 2 de 2 resultados.")
  await ui.settle(800)
  assert.equal(card(), undefined)
  assert.equal(document.querySelector(".count")!.textContent, "Exibindo 1 de 1 resultados.")
})
