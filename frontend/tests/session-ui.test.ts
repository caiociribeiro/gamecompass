// Sessão no React com HTTP fictício: nenhuma API, banco ou navegador real é acessado.
import assert from "node:assert/strict"
import { test, type TestContext } from "node:test"
import { mkdtemp, rm } from "node:fs/promises"
import { join } from "node:path"
import { fileURLToPath, pathToFileURL } from "node:url"
import * as esbuild from "esbuild"
import { JSDOM } from "jsdom"

const HARDWARE = { cpuId: "CPU fixture", gpuId: "GPU fixture", ramGb: 16, os: "Windows", windowsVersion: "11" }
const account = (id: string, extra: object = {}) => ({ id, name: `Conta ${id}`, genres: [], themes: [], anchorIds: [], hardware: null, ...extra })

async function boot(t: TestContext, handler: (path: string, options: any, log: string[]) => Response | Promise<Response>, legacy?: unknown) {
  const base = fileURLToPath(new URL("../", import.meta.url))
  const directory = await mkdtemp(join(base, "node_modules", ".gamecompass-session-"))
  const outfile = join(directory, "app.mjs")
  await esbuild.build({ stdin: { contents: `
    import React, {useEffect} from 'react';import {createRoot} from 'react-dom/client';
    import {SessionProvider,useSession} from ${JSON.stringify(join(base, "src/context/SessionContext.tsx"))};
    export {React,createRoot};export const probe={};
    function Probe(){const session=useSession();useEffect(()=>{Object.assign(probe,{session})});return null;}
    export function Harness(){return <SessionProvider><Probe/></SessionProvider>}
  `, resolveDir: base, loader: "tsx" }, bundle: true, format: "esm", platform: "browser", outfile, external: ["react", "react-dom", "react-dom/client"],
    define: { "process.env.NODE_ENV": '"development"' }, logLevel: "silent" })
  const dom = new JSDOM('<!doctype html><div id="root"></div>', { url: "http://localhost/", pretendToBeVisual: true })
  const saved = new Map<string, PropertyDescriptor | undefined>()
  for (const name of ["window", "document", "navigator", "localStorage", "HTMLElement", "Event", "MouseEvent", "IS_REACT_ACT_ENVIRONMENT"]) {
    saved.set(name, Object.getOwnPropertyDescriptor(globalThis, name))
    Object.defineProperty(globalThis, name, { value: name === "IS_REACT_ACT_ENVIRONMENT" ? true : (dom.window as any)[name], configurable: true, writable: true })
  }
  if (legacy !== undefined) localStorage.setItem("gamecompass.users.v1", JSON.stringify(legacy))
  localStorage.setItem("gamecompass.session.v1", "sessao-antiga")
  const log: string[] = []
  t.mock.method(globalThis, "fetch", async (url: any, options: any = {}) => {
    const path = new URL(String(url), "http://localhost").pathname
    log.push(`${options.method ?? "GET"} ${path}`)
    return handler(path, options, log)
  })
  const m = await import(pathToFileURL(outfile).href)
  const { act } = m.React
  const root = m.createRoot(document.getElementById("root"))
  t.after(async () => {
    await act(async () => root.unmount())
    dom.window.close()
    for (const [name, descriptor] of saved) {
      if (descriptor) Object.defineProperty(globalThis, name, descriptor)
      else Reflect.deleteProperty(globalThis, name)
    }
    esbuild.stop()
    await rm(directory, { recursive: true, force: true })
  })
  await act(async () => root.render(m.React.createElement(m.Harness)))
  for (let attempt = 0; attempt < 30 && m.probe.session.status !== "ready"; attempt++) await act(async () => { await new Promise((r) => setTimeout(r, 5)) })
  return { m, act, log, dom }
}

test("sem sessão válida a tela fica deslogada e a falha da API é informada, não escondida", async (t) => {
  const anonymous = await boot(t, () => Response.json({ detail: "Entre na sua conta para continuar." }, { status: 401 }))
  assert.equal(anonymous.m.probe.session.user, null)
  assert.equal(anonymous.m.probe.session.error, null)
})

test("API fora do ar na verificação da sessão não vira login falso", async (t) => {
  const down = await boot(t, () => { throw new TypeError("Failed to fetch") })
  assert.equal(down.m.probe.session.user, null)
  assert.match(down.m.probe.session.error, /acessar a API do GameCompass/)
})

test("login com erro devolve a mensagem da API e não abre sessão", async (t) => {
  const { m, act } = await boot(t, (path) => path === "/api/auth/login"
    ? Response.json({ detail: "E-mail ou senha não conferem." }, { status: 401 })
    : Response.json({ detail: "Entre." }, { status: 401 }))
  let message: string | null = null
  await act(async () => { message = await m.probe.session.login("A@Example.invalid ", "errada") })
  assert.equal(message, "E-mail ou senha não conferem.")
  assert.equal(m.probe.session.user, null)
})

test("trocar de conta envia a edição pendente ainda com a sessão antiga e não mistura perfis", async (t) => {
  let current = "a"
  const { m, act, log } = await boot(t, async (path, options) => {
    if (path === "/api/auth/me") return Response.json(account("a"))
    if (path === "/api/auth/login") { current = JSON.parse(options.body).email.startsWith("b") ? "b" : "a"; return Response.json(account(current, { genres: current === "b" ? ["Puzzle"] : [] })) }
    if (path === "/api/auth/logout") { current = ""; return Response.json({ status: "ok" }) }
    if (path === "/api/me/profile") {
      await new Promise((resolve) => setTimeout(resolve, 20))  // PATCH lento
      return Response.json({ ...account(current), ...JSON.parse(options.body) })
    }
    throw new Error("Requisição inesperada: " + path)
  })
  assert.equal(m.probe.session.user.id, "a")
  await act(async () => {
    m.probe.session.updateUser({ genres: ["RPG"] })
    const out = m.probe.session.logout()
    await out
    await m.probe.session.login("b@example.invalid", "senha-de-teste-1")
  })
  assert.deepEqual(log.slice(1), ["PATCH /api/me/profile", "POST /api/auth/logout", "POST /api/auth/login"])
  assert.equal(m.probe.session.user.id, "b")
  assert.deepEqual(m.probe.session.user.genres, ["Puzzle"])  // nada de A chegou a B
})

test("falha ao salvar mostra o aviso e volta ao que o servidor guardou", async (t) => {
  let patched = false
  const { m, act } = await boot(t, (path, options) => {
    if (path === "/api/auth/me") return Response.json(account("a", { genres: ["RPG"] }))
    if (path === "/api/me/profile") { patched = true; return Response.json({ detail: "Banco indisponível." }, { status: 503 }) }
    throw new Error("Requisição inesperada: " + path + options.method)
  })
  await act(async () => { m.probe.session.updateUser({ genres: ["Puzzle"] }); await new Promise((r) => setTimeout(r, 700)) })
  assert(patched)
  assert.match(m.probe.session.saveError, /Não foi possível salvar no servidor\. Banco indisponível\./)
  assert.deepEqual(m.probe.session.user.genres, ["RPG"])
})

test("sessão encerrada em outro lugar derruba a interface ao salvar", async (t) => {
  const { m, act } = await boot(t, (path) => path === "/api/auth/me"
    ? Response.json(account("a"))
    : Response.json({ detail: "Sessão expirada. Entre novamente." }, { status: 401 }))
  await act(async () => { m.probe.session.updateUser({ genres: ["RPG"] }); await new Promise((r) => setTimeout(r, 700)) })
  assert.equal(m.probe.session.user, null)
})

test("dados da versão antiga (e-mails, senhas, preferências) são apagados do navegador ao iniciar", async (t) => {
  const legacy = [{ id: "x1", name: "Antigo", email: "a@example.invalid", password: "senha-em-texto-puro", genres: ["RPG"], themes: [], anchorIds: [], hardware: null }]
  const { m } = await boot(t, (path) => {
    if (path === "/api/auth/me") return Response.json(account("a"))
    throw new Error("Requisição inesperada: " + path)
  }, legacy)
  assert.equal(localStorage.getItem("gamecompass.users.v1"), null)
  assert.equal(localStorage.getItem("gamecompass.session.v1"), null)
  assert.equal(m.probe.session.user.id, "a")
})

test("cliques seguidos viram um único PATCH; sair envia o que faltava antes de encerrar", async (t) => {
  const log: string[] = []
  const patches: any[] = []
  const { m, act } = await boot(t, (path, options) => {
    log.push(path)
    if (path === "/api/auth/me") return Response.json(account("a"))
    if (path === "/api/me/profile") { patches.push(JSON.parse(options.body)); return Response.json(account("a")) }
    if (path === "/api/auth/logout") return Response.json({ status: "ok" })
    throw new Error("Requisição inesperada: " + path)
  })
  await act(async () => {
    m.probe.session.updateUser({ genres: ["RPG"] })
    m.probe.session.updateUser({ genres: ["RPG", "Puzzle"] })
    m.probe.session.updateUser({ themes: ["Fantasia"] })
    await new Promise((r) => setTimeout(r, 700))
  })
  assert.deepEqual(patches, [{ genres: ["RPG", "Puzzle"], themes: ["Fantasia"] }])
  await act(async () => {
    m.probe.session.updateUser({ anchorIds: ["1"] })
    await m.probe.session.logout()
  })
  assert.deepEqual(patches.at(-1), { anchorIds: ["1"] })
  assert(log.lastIndexOf("/api/me/profile") < log.lastIndexOf("/api/auth/logout"))
})

test("esconder a aba envia na hora, com keepalive, o que ainda esperava a pausa", async (t) => {
  const sent: any[] = []
  const { m, act, dom } = await boot(t, (path, options) => {
    if (path === "/api/auth/me") return Response.json(account("a"))
    if (path === "/api/me/profile") { sent.push({ body: JSON.parse(options.body), keepalive: options.keepalive === true }); return Response.json(account("a")) }
    throw new Error("Requisição inesperada: " + path)
  })
  await act(async () => {
    m.probe.session.updateUser({ genres: ["RPG"] })
    Object.defineProperty(dom.window.document, "visibilityState", { value: "hidden", configurable: true })
    dom.window.document.dispatchEvent(new dom.window.Event("visibilitychange"))
    await new Promise((r) => setTimeout(r, 20))  // bem antes da pausa de 600 ms
  })
  assert.deepEqual(sent, [{ body: { genres: ["RPG"] }, keepalive: true }])
  assert.equal(m.probe.session.saving, false)
})
