import assert from "node:assert/strict"
import { test } from "node:test"
import { nextPendingStep, profileSteps, stepGuide } from "../src/lib/profile.ts"
import type { Game, HardwareCatalog, Part, UserProfile } from "../src/types.ts"

const part = (id: string): Part => ({ id, name: id, vendor: "Outro", performance_score: 10, score_version: "manual_v1" })
const hardware: HardwareCatalog = { CPU: [part("cpu")], GPU: [part("gpu")], score_version: "manual_v1", source: "neo4j" }
const game = (id: string) => ({ id, title: `Jogo ${id}` }) as unknown as Game
const games = ["1", "2", "3", "4"].map(game)
const user = (patch: Partial<UserProfile> = {}): UserProfile =>
  ({ id: "u", name: "Teste", genres: [], themes: [], anchorIds: [], hardware: null, ...patch })

test("preferências: sem nada escolhido, diz exatamente o que falta e não libera a próxima etapa", () => {
  const guide = stepGuide(user(), games, hardware, "prefs")
  assert.equal(guide.done, false)
  assert.equal(guide.missing, "Escolha pelo menos um gênero e uma temática para continuar.")
  assert.deepEqual([guide.position, guide.total], [1, 3])
})

test("preferências: só falta a temática ou só o gênero", () => {
  assert.equal(stepGuide(user({ genres: ["RPG"] }), games, hardware, "prefs").missing,
    "Escolha pelo menos uma temática para continuar.")
  assert.equal(stepGuide(user({ themes: ["Fantasia"] }), games, hardware, "prefs").missing,
    "Escolha pelo menos um gênero para continuar.")
})

test("preferências: concluídas, resume as escolhas e aponta para os jogos âncora", () => {
  const guide = stepGuide(user({ genres: ["RPG"], themes: ["Fantasia", "Terror"] }), games, hardware, "prefs")
  assert.equal(guide.done, true)
  assert.equal(guide.status, "1 gênero e 2 temáticas escolhidos.")
  assert.deepEqual(guide.next, { to: "/app/ancoras", label: "Continuar para jogos âncora" })
})

test("âncoras: conta só jogos que o catálogo conseguiu carregar", () => {
  const guide = stepGuide(user({ anchorIds: ["1", "2", "fora-do-catalogo"] }), games, hardware, "anchors")
  assert.equal(guide.done, false)
  assert.equal(guide.missing, "Escolha mais 1 jogo para continuar.")
  assert.equal(stepGuide(user({ anchorIds: ["1"] }), games, hardware, "anchors").missing,
    "Escolha mais 2 jogos para continuar.")
})

test("âncoras: com três jogos a etapa termina e aponta para o computador", () => {
  const guide = stepGuide(user({ anchorIds: ["1", "2", "3"] }), games, hardware, "anchors")
  assert.equal(guide.done, true)
  assert.deepEqual(guide.next, { to: "/app/hardware", label: "Continuar para o computador" })
  assert.deepEqual([guide.position, guide.total], [2, 3])
})

test("computador: só conta como pronto depois de salvo e com peças do catálogo; depois leva às recomendações", () => {
  assert.equal(stepGuide(user(), games, hardware, "hardware").done, false)
  const saved = { cpuId: "cpu", gpuId: "gpu", ramGb: 16, os: "Linux" as const }
  const guide = stepGuide(user({ hardware: saved }), games, hardware, "hardware")
  assert.equal(guide.done, true)
  assert.deepEqual(guide.next, { to: "/app/recomendacoes", label: "Ver recomendações" })
  assert.equal(stepGuide(user({ hardware: { ...saved, cpuId: "removida" } }), games, hardware, "hardware").done, false)
})

test("próxima etapa pendente: segue a ordem do perfil e some quando tudo está pronto", () => {
  const steps = (patch: Partial<UserProfile>) => profileSteps(user(patch), games, hardware)
  assert.equal(nextPendingStep(steps({}))?.id, "prefs")
  assert.equal(nextPendingStep(steps({ genres: ["RPG"], themes: ["Fantasia"] }))?.id, "anchors")
  const saved = { cpuId: "cpu", gpuId: "gpu", ramGb: 16, os: "Linux" as const }
  assert.equal(nextPendingStep(steps({ genres: ["RPG"], themes: ["Fantasia"], anchorIds: ["1", "2", "3"] }))?.id, "hardware")
  assert.equal(nextPendingStep(steps({ genres: ["RPG"], themes: ["Fantasia"], anchorIds: ["1", "2", "3"], hardware: saved })), null)
  // a primeira pendente vem antes, mesmo que uma etapa posterior já esteja pronta
  assert.equal(nextPendingStep(steps({ hardware: saved }))?.id, "prefs")
})
