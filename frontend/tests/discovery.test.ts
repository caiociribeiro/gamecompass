import assert from "node:assert/strict"
import { test } from "node:test"
import { discoveryFilters, RequestScope } from "../src/lib/discovery.ts"

test("filtros equivalentes têm uma identidade estável mesmo após reordenar preferências", () => {
  const a = discoveryFilters({ anchorIds: ["3", "1", "2", "1"], genres: ["RPG", "Puzzle", "RPG"], themes: ["Fantasia"] })
  const b = discoveryFilters({ anchorIds: ["2", "3", "1"], genres: ["Puzzle", "RPG"], themes: ["Fantasia"] })
  assert.deepEqual(a, b)
  assert.deepEqual(discoveryFilters(null), { anchor_ids: "", genres: "", tags: "" })
})

test("trocar preferências altera a identidade e identificadores inválidos não vão para a API", () => {
  const a = { anchorIds: ["1", "inválido", "2", "3"], genres: ["RPG"], themes: ["Fantasia"] }
  assert.equal(discoveryFilters(a).anchor_ids, "1,2,3")
  assert.notDeepEqual(discoveryFilters(a), discoveryFilters({ ...a, genres: ["Puzzle"] }))
})

test("nova busca cancela a anterior e apenas a resposta atual pode atualizar a tela", async () => {
  const scope = new RequestScope()
  const old = scope.start()
  const current = scope.start()
  let result = ""
  await Promise.resolve().then(() => { if (current.isCurrent()) result = "novo" })
  await Promise.resolve().then(() => { if (old.isCurrent()) result = "antigo" })
  assert.equal(old.signal.aborted, true)
  assert.equal(current.signal.aborted, false)
  assert.equal(result, "novo")
})

test("mudar perfil ou sair cancela o resultado pendente e permite uma nova busca", () => {
  const scope = new RequestScope()
  const pending = scope.start()
  scope.cancel()
  assert.equal(pending.isCurrent(), false)
  assert.equal(pending.signal.aborted, true)
  assert.equal(scope.start().isCurrent(), true)
})
