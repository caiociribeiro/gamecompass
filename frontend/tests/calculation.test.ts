import assert from "node:assert/strict"
import { test } from "node:test"
import { calculationProfile } from "../src/lib/calculation.ts"
import { apiPost } from "../src/lib/api.ts"
import { compatibilityLabel } from "../src/lib/recommend.ts"
import type { UserProfile } from "../src/types.ts"

const user: UserProfile = { id: "fixture", name: "Fixture", email: "fixture@example.invalid",
  genres: ["RPG", "Puzzle"], themes: ["Fantasia"], anchorIds: ["3", "1", "2"],
  hardware: { cpuId: "CPU fixture", gpuId: "GPU fixture", ramGb: 16, os: "Windows", windowsVersion: "11" } }

test("o corpo de cálculo contém identidades e preferências, sem conta ou pontuações", () => {
  const profile = { ...user, hardware: { ...user.hardware!, performance_score: 999999, score_version: "inventada" } }
  assert.deepEqual(calculationProfile(profile), {
    anchorIds: ["1", "2", "3"], genres: ["Puzzle", "RPG"], themes: ["Fantasia"],
    hardware: { cpuId: "CPU fixture", gpuId: "GPU fixture", ramGb: 16, os: "Windows", windowsVersion: "11" },
  })
  assert.doesNotMatch(JSON.stringify(calculationProfile(profile)), /email|password|performance_score|score_version/)
})

test("reordenar preferências preserva o corpo e trocar hardware altera o cálculo solicitado", () => {
  assert.deepEqual(calculationProfile(user), calculationProfile({ ...user, genres: ["Puzzle", "RPG", "RPG"], anchorIds: ["1", "2", "3"] }))
  assert.notDeepEqual(calculationProfile(user), calculationProfile({ ...user, hardware: { ...user.hardware!, ramGb: 32 } }))
  assert.equal(calculationProfile({ ...user, hardware: { ...user.hardware!, os: "Linux" } }).hardware?.windowsVersion, undefined)
})

test("POST envia JSON e cancelamento e mantém a mensagem de erro da API", async (t) => {
  const controller = new AbortController()
  t.mock.method(globalThis, "fetch", async (url, options) => {
    assert.match(String(url), /\/recommendations$/)
    assert.equal(options?.method, "POST")
    assert.equal(options?.signal, controller.signal)
    assert.equal((options?.headers as Record<string, string>)["Content-Type"], "application/json")
    assert.deepEqual(JSON.parse(options?.body as string), calculationProfile(user))
    return Response.json({ detail: "Selecione novamente seu hardware." }, { status: 422 })
  })
  await assert.rejects(apiPost("/recommendations", calculationProfile(user), controller.signal), /Selecione novamente seu hardware/)
})

test("a apresentação distingue os níveis do servidor e preserva o aviso de estimativa", () => {
  assert.equal(compatibilityLabel({ compatibility: "compatible", meets: "recommended", estimated: true }), "Atende aos recomendados (estimativa)")
  assert.equal(compatibilityLabel({ compatibility: "compatible", meets: "minimum", estimated: false }), "Atende aos mínimos")
  assert.equal(compatibilityLabel({ compatibility: "needs_review", meets: null, estimated: false }), "Validação dos mínimos pendente")
})
