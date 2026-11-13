// Integração React com HTTP fictício; nenhum banco ou Steam é acessado.
import assert from "node:assert/strict"
import { test } from "node:test"
import { mountReact, src } from "./helpers/react-harness.ts"

test("React usa a API e descarta respostas de outro perfil, hardware ou conta", { timeout: 15000 }, async (t) => {
  const user = { id: "qa", name: "Fixture", genres: ["RPG"], themes: ["Fantasia"],
    anchorIds: ["101", "102", "103"], hardware: { cpuId: "CPU fixture", gpuId: "GPU fixture", ramGb: 16, os: "Windows", windowsVersion: "11" }, catalogVersion: "steam-v2" }
  const hardware = { CPU: [{ id: "CPU fixture", name: "CPU fixture", vendor: "Fixture", performance_score: 10, score_version: "manual_v1" }],
    GPU: [{ id: "GPU fixture", name: "GPU fixture", vendor: "Fixture", performance_score: 20, score_version: "manual_v1" }], source: "neo4j", score_version: "manual_v1" }
  function game(id, title = `Âncora fixture ${id}`) {
    return { id, title, genres: ["Puzzle"], themes: ["Fantasia"], themes_status: "classified", developer: "Fixture", year: 2026,
      image_url: null, summary: "Fixture", price_text: null, store_url: "https://example.invalid/fixture",
      source: { collected_at: "2026-10-31T12:00:00Z", source_url: "https://example.invalid/fixture" },
      platforms: { Windows: { native_support: true, minimum: { text: "Requisito fixture", os_text: "Windows 10", score_version: "manual_v1",
        requirements: { cpu_score: 10, gpu_score: 20, ram_gb: 4 }, status: "resolved", issues: [] }, recommended: null },
        Linux: { native_support: false, minimum: null, recommended: null }, macOS: { native_support: false, minimum: null, recommended: null } } }
  }
  const anchors = user.anchorIds.map((id) => game(id))
  const candidate = game("104", "Resultado vindo da API")
  function match(value = candidate) {
    const checks = ["Processador", "Placa de vídeo", "Memória RAM", "Sistema operacional"].map((label) => ({ label, ok: true, detail: "Conferência feita pela API." }))
    return { game: value, affinity: 17, reasons: ["Em comum com Âncora fixture 101: Puzzle."], preferredGenres: ["Puzzle"], anchorMatches: [],
      checks, compatibility: "compatible", meets: "minimum", compatible: true, estimated: false, anchor: false,
      assessments: { minimum: { available: true, checks, compatibility: "compatible" }, recommended: { available: false,
        checks: checks.map((c) => ({ ...c, ok: null })), compatibility: "needs_review" } } }
  }
  const result = () => ({ items: [match()], pending: [], excluded: [], anchors, issues: [], source: "neo4j",
    calculation: { engine_version: "rules_v1", minimum_affinity: 28, score_version: "manual_v1", hardware_sha256: "fixture", curation_sha256: "fixture" } })
  const requests: any[] = [], comparisons: any[] = [], patches: any[] = []
  let signedIn = true
  const ui = await mountReact(t, {
    source: `
      import React, {useEffect} from 'react';import {createRoot} from 'react-dom/client';
      import {MemoryRouter,Routes,Route,useLocation,useNavigate} from 'react-router-dom';
      import {SessionProvider,useSession} from ${src("context/SessionContext.tsx")};
      import {CatalogProvider,useCatalog} from ${src("context/CatalogContext.tsx")};
      import {Recommendations} from ${src("pages/Recommendations.tsx")};
      import {GameDetail} from ${src("pages/GameDetail.tsx")};
      export {React,createRoot};export const probe={};
      function Probe(){const session=useSession(),catalog=useCatalog(),location=useLocation(),navigate=useNavigate();
        useEffect(()=>{Object.assign(probe,{session,catalog,location,navigate})});return null;}
      export function Harness(){return <SessionProvider><CatalogProvider><MemoryRouter initialEntries={['/app/recomendacoes?q=Resultado']}>
        <Probe/><Routes><Route path='/app/recomendacoes' element={<Recommendations/>}/>
        <Route path='/app/jogos/:id' element={<GameDetail/>}/></Routes>
        </MemoryRouter></CatalogProvider></SessionProvider>}
    `,
    fetch: async (path, options) => {
      if (path === "/api/auth/me") return signedIn ? Response.json(user) : Response.json({ detail: "Entre." }, { status: 401 })
      if (path === "/api/auth/login") { signedIn = true; return Response.json(user) }
      if (path === "/api/auth/logout") { signedIn = false; return Response.json({ status: "ok" }) }
      if (path === "/api/me/profile") { assert.equal(options.method, "PATCH"); patches.push(JSON.parse(options.body)); return Response.json(user) }
      if (path === "/api/hardware") return Response.json(hardware)
      if (path === "/api/games") return Response.json({ items: anchors, issues: [], source: "neo4j" })
      if (path === "/api/recommendations" || path.endsWith("/comparison")) {
        assert.equal(options.method, "POST")
        const collection = path.endsWith("/comparison") ? comparisons : requests
        return await new Promise((resolve) => collection.push({ resolve, signal: options.signal, body: JSON.parse(options.body), path }))
      }
      throw new Error("Requisição inesperada: " + path)
    },
  })
  const { m, act, dom } = ui
  for (let attempt = 0; attempt < 20 && m.probe.session.status !== "ready"; attempt++) await act(async () => { await new Promise((r) => setTimeout(r, 5)) })
  assert.equal(m.probe.session.user?.id, "qa")
  assert.equal(requests.length, 0)
  let first, second
  await act(async () => { first = m.probe.catalog.discoverGames() })
  assert.doesNotMatch(JSON.stringify(requests[0].body), /email|password|performance_score/)
  await act(async () => { m.probe.session.updateUser({ genres: ["Puzzle", "Indie"] }); await new Promise((r) => setTimeout(r, 700)) })
  assert.equal(requests[0].signal.aborted, true)
  assert.deepEqual(patches.at(-1), { genres: ["Puzzle", "Indie"] })
  await act(async () => { second = m.probe.catalog.discoverGames() })
  await act(async () => { requests[1].resolve(Response.json(result())); await second })
  assert.equal(m.probe.catalog.discovered, true)
  assert(document.body.textContent.includes("17%"))
  await act(async () => { requests[0].resolve(Response.json({ ...result(), items: [match(game("999", "Resposta antiga"))] })); await first })
  assert(!document.body.textContent.includes("Resposta antiga"))
  await act(async () => m.probe.session.updateUser({ hardware: { ...user.hardware, ramGb: 32 } }))
  assert.equal(requests.length, 3)
  assert.equal(requests[2].body.hardware.ramGb, 32)
  assert.equal(m.probe.catalog.discovered, false)
  await act(async () => { requests[2].resolve(Response.json(result())); await Promise.resolve() })
  assert.equal(m.probe.catalog.discovered, true)
  await act(async () => m.probe.session.updateUser({ genres: ["Indie", "Puzzle"] }))
  assert.equal(requests.length, 3)
  const card = document.querySelector('a[href="/app/jogos/104"]')!
  await act(async () => card.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true, cancelable: true, button: 0 })))
  assert.equal(m.probe.location.pathname, "/app/jogos/104")
  assert.equal(comparisons.length, 0)
  assert(document.body.textContent.includes("Conferência feita pela API."))
  const back = document.querySelector("a.back")!
  await act(async () => back.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true, cancelable: true, button: 0 })))
  assert.equal(m.probe.location.pathname, "/app/recomendacoes")
  assert.equal(m.probe.location.search, "?q=Resultado")
  assert.equal(requests.length, 3)
  await act(async () => m.probe.navigate("/app/jogos/105"))
  assert.equal(comparisons.length, 1)
  await act(async () => { comparisons[0].resolve(Response.json({ match: match(game("105", "Detalhe via API")), issues: [], calculation: result().calculation })); await Promise.resolve() })
  assert(document.body.textContent.includes("Detalhe via API"))
  await act(async () => m.probe.navigate("/app/jogos/106"))
  assert.equal(comparisons.length, 2)
  await act(async () => m.probe.session.logout())
  assert.equal(comparisons[1].signal.aborted, true)
  await act(async () => { comparisons[1].resolve(Response.json({ match: match(game("106")), issues: [], calculation: result().calculation })); await Promise.resolve() })
  assert.equal(m.probe.catalog.games.length, 0)
  assert.equal(m.probe.catalog.recommendations, null)
  assert.equal(m.probe.session.user, null)
  await act(async () => { await m.probe.session.login("fixture@example.invalid", "senha-de-teste-1"); m.probe.navigate("/app/recomendacoes") })
  assert.equal(m.probe.session.user?.id, "qa")
  let failed
  await act(async () => { failed = m.probe.catalog.discoverGames() })
  await act(async () => { requests[3].resolve(Response.json({ detail: "API fixture indisponível." }, { status: 503 })); await failed })
  assert.equal(m.probe.catalog.recommendations, null)
  assert.equal(m.probe.catalog.gamesError, "API fixture indisponível.")
})
