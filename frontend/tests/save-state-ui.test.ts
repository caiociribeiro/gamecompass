// Preferências não podem dizer "SALVO NA CONTA" quando o servidor recusou a gravação.
import assert from "node:assert/strict"
import { test } from "node:test"
import { mkdtemp, rm } from "node:fs/promises"
import { join } from "node:path"
import { fileURLToPath, pathToFileURL } from "node:url"
import * as esbuild from "esbuild"
import { JSDOM } from "jsdom"

test("aviso de salvamento das Preferências respeita a falha do servidor", { timeout: 15000 }, async (t) => {
  const base = fileURLToPath(new URL("../", import.meta.url))
  const directory = await mkdtemp(join(base, "node_modules", ".gamecompass-save-"))
  const outfile = join(directory, "app.mjs")
  await esbuild.build({ stdin: { contents: `
    import React from 'react';import {createRoot} from 'react-dom/client';
    import {MemoryRouter,Routes,Route} from 'react-router-dom';
    import {SessionProvider} from ${JSON.stringify(join(base, "src/context/SessionContext.tsx"))};
    import {CatalogProvider} from ${JSON.stringify(join(base, "src/context/CatalogContext.tsx"))};
    import {Preferences} from ${JSON.stringify(join(base, "src/pages/Preferences.tsx"))};
    export {React,createRoot};
    export function Harness(){return <SessionProvider><CatalogProvider><MemoryRouter initialEntries={['/app/preferencias']}>
      <Routes><Route path='/app/preferencias' element={<Preferences/>}/></Routes></MemoryRouter></CatalogProvider></SessionProvider>}
  `, resolveDir: base, loader: "tsx" }, bundle: true, format: "esm", platform: "browser", outfile, external: ["react", "react-dom", "react-dom/client"],
    define: { "process.env.NODE_ENV": '"development"' }, loader: { ".css": "empty" }, logLevel: "silent" })
  const dom = new JSDOM('<!doctype html><div id="root"></div>', { url: "http://localhost/", pretendToBeVisual: true })
  const saved = new Map<string, PropertyDescriptor | undefined>()
  for (const name of ["window", "document", "navigator", "localStorage", "HTMLElement", "Event", "MouseEvent", "IS_REACT_ACT_ENVIRONMENT"]) {
    saved.set(name, Object.getOwnPropertyDescriptor(globalThis, name))
    Object.defineProperty(globalThis, name, { value: name === "IS_REACT_ACT_ENVIRONMENT" ? true : dom.window[name], configurable: true, writable: true })
  }
  let unmount = async () => {}
  t.after(async () => {
    await unmount()
    dom.window.close()
    for (const [name, descriptor] of saved) {
      if (descriptor) Object.defineProperty(globalThis, name, descriptor)
      else Reflect.deleteProperty(globalThis, name)
    }
    esbuild.stop()
    await rm(directory, { recursive: true, force: true })
  })
  const user = { id: "qa", name: "Fixture", genres: [], themes: [], anchorIds: [], hardware: null, catalogVersion: "steam-v2" }
  let failSave = true
  t.mock.method(globalThis, "fetch", async (url: string, options: any = {}) => {
    const path = new URL(String(url), "http://localhost").pathname
    if (path === "/api/auth/me") return Response.json(user)
    if (path === "/api/hardware") return Response.json({ CPU: [], GPU: [], source: "neo4j", score_version: "manual_v1" })
    if (path === "/api/me/profile") return failSave ? Response.json({ detail: "Banco fora do ar." }, { status: 503 }) : Response.json(user)
    throw new Error("Requisição inesperada: " + path)
  })
  const m = await import(pathToFileURL(outfile).href)
  const { act } = m.React
  const root = m.createRoot(document.getElementById("root"))
  unmount = async () => { await act(async () => root.unmount()) }
  await act(async () => root.render(m.React.createElement(m.Harness)))
  for (let attempt = 0; attempt < 40 && !document.querySelector(".save-flash"); attempt++) await act(async () => { await new Promise((r) => setTimeout(r, 10)) })
  const click = async (label: string) => {
    const button = [...document.querySelectorAll("button")].find((item) => item.textContent?.trim() === label)!
    await act(async () => { button.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true, cancelable: true, button: 0 })) })
  }
  const flash = () => document.querySelector(".save-flash")!

  await click("RPG")
  assert.equal(flash().textContent, "SALVANDO…")
  await act(async () => { await new Promise((r) => setTimeout(r, 750)) })
  assert.equal(flash().textContent, "NÃO FOI SALVO")
  assert(flash().classList.contains("error"))

  failSave = false
  await click("Aventura")
  await act(async () => { await new Promise((r) => setTimeout(r, 750)) })
  assert.equal(flash().textContent, "SALVO NA CONTA")
  assert(!flash().classList.contains("error"))
})
