import assert from "node:assert/strict"
import { test } from "node:test"
import { apiError, apiGet } from "../src/lib/api.ts"

test("proxy sem backend retorna uma mensagem de indisponibilidade", async (t) => {
  t.mock.method(globalThis, "fetch", async () => new Response("", { status: 500 }))
  await assert.rejects(apiGet("/games/search?q=cyberpunk"), /acessar a API do GameCompass/)
})

test("mensagem de erro da Steam é preservada", async (t) => {
  t.mock.method(globalThis, "fetch", async () =>
    Response.json({ detail: "A Steam limitou as consultas." }, { status: 503 }),
  )
  await assert.rejects(apiGet("/games/anchors"), /A Steam limitou as consultas/)
})

test("erro de rede tem uma mensagem legível", () => {
  assert.match(apiError(new TypeError("Failed to fetch")), /acessar a API do GameCompass/)
})

test("resposta válida continua disponível após a API iniciar", async (t) => {
  const items = [{ id: "1091500", title: "Cyberpunk 2077" }]
  t.mock.method(globalThis, "fetch", async () => Response.json({ items }))
  assert.deepEqual(await apiGet("/games/anchors"), { items })
})
