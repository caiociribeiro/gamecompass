// Preferências não podem dizer "SALVO NA CONTA" quando o servidor recusou a gravação.
import assert from "node:assert/strict"
import { test } from "node:test"
import { mountReact, src } from "./helpers/react-harness.ts"

test("aviso de salvamento das Preferências respeita a falha do servidor", { timeout: 15000 }, async (t) => {
  const user = { id: "qa", name: "Fixture", genres: [], themes: [], anchorIds: [], hardware: null, catalogVersion: "steam-v2" }
  let failSave = true
  const ui = await mountReact(t, {
    source: `
      import React from 'react';import {createRoot} from 'react-dom/client';
      import {MemoryRouter,Routes,Route} from 'react-router-dom';
      import {SessionProvider} from ${src("context/SessionContext.tsx")};
      import {CatalogProvider} from ${src("context/CatalogContext.tsx")};
      import {Preferences} from ${src("pages/Preferences.tsx")};
      export {React,createRoot};
      export function Harness(){return <SessionProvider><CatalogProvider><MemoryRouter initialEntries={['/app/preferencias']}>
        <Routes><Route path='/app/preferencias' element={<Preferences/>}/></Routes></MemoryRouter></CatalogProvider></SessionProvider>}
    `,
    fetch: (path) => {
      if (path === "/api/auth/me") return Response.json(user)
      if (path === "/api/hardware") return Response.json({ CPU: [], GPU: [], source: "neo4j", score_version: "manual_v1" })
      if (path === "/api/me/profile") return failSave ? Response.json({ detail: "Banco fora do ar." }, { status: 503 }) : Response.json(user)
      throw new Error("Requisição inesperada: " + path)
    },
  })
  const { act } = ui
  for (let attempt = 0; attempt < 40 && !document.querySelector(".save-flash"); attempt++) await ui.settle(10)
  const click = (label: string) => ui.click(ui.button(label)!)
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
