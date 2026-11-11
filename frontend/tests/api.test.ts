import assert from "node:assert/strict"
import { test } from "node:test"
import { apiDelete, apiError, apiGet, apiPut } from "../src/lib/api.ts"

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

test("PUT e DELETE enviam o método certo e o corpo só quando existe", async (t) => {
  const calls: { method?: string; body?: unknown }[] = []
  t.mock.method(globalThis, "fetch", async (_url: unknown, options: { method?: string; body?: unknown }) => {
    calls.push({ method: options.method, body: options.body })
    return Response.json({ ok: true })
  })
  await apiPut("/me/games/1/reaction", { reaction: "liked" })
  await apiDelete("/me/interactions")
  assert.deepEqual(calls, [{ method: "PUT", body: JSON.stringify({ reaction: "liked" }) }, { method: "DELETE", body: undefined }])
})
