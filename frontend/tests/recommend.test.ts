import assert from "node:assert/strict"
import { test } from "node:test"
import { buildRecommendations, describeMatch, hardwareChecks } from "../src/lib/recommend.ts"
import type { Game, HardwareCatalog, HardwareProfile, UserProfile } from "../src/types.ts"
import { migrateProfile } from "../src/lib/migrateProfile.ts"

// Fixtures inventadas para verificar a lógica; não são medições de jogos reais.
const hardware: HardwareCatalog = {
  CPU: [
    { id: "cpu", name: "CPU fixture", vendor: "Fixture", performance_score: 400, score_version: "manual_v1" },
  ],
  GPU: [
    { id: "gpu", name: "GPU fixture", vendor: "Fixture", performance_score: 550, score_version: "manual_v1" },
  ],
  score_version: "manual_v1",
  source: "neo4j",
}
const pc: HardwareProfile = { cpuId: "cpu", gpuId: "gpu", ramGb: 16, os: "Windows" }
function fixture(id = "1"): Game {
  const block = {
    text: "Requisitos fixture",
    os_text: "Windows 10",
    status: "resolved" as const,
    requirements: { ram_gb: 8, cpu_score: 400, gpu_score: 550 },
    issues: [],
    score_version: "manual_v1",
  }
  return {
    id,
    title: `Jogo fixture ${id}`,
    developer: "Estúdio fixture",
    year: 2026,
    genres: ["RPG"],
    themes: ["Fantasia"],
    themes_status: "classified",
    summary: "Fixture",
    image_url: null,
    price_text: null,
    store_url: `https://store.steampowered.com/app/${id}/`,
    platforms: {
      Windows: { native_support: true, minimum: block, recommended: null },
      Linux: { native_support: false, minimum: null, recommended: null },
      macOS: {
        native_support: true,
        minimum: { ...block, os_text: "macOS 15", requirements: { ...block.requirements, ram_gb: 24 } },
        recommended: null,
      },
    },
    source: {
      collected_at: "2026-10-30T00:00:00Z",
      source_url: "https://example.org/fixture",
      response_sha256: "fixture",
    },
  }
}
const user: UserProfile = {
  id: "fixture",
  name: "Fixture",
  email: "fixture@example.org",
  password: "fixture",
  genres: ["RPG"],
  themes: ["Fantasia"],
  anchorIds: ["1", "2", "3"],
  hardware: pc,
  catalogVersion: "steam-v2",
}

test("tags classificadas do catálogo mudam a ordem e explicam a afinidade", () => {
  const anchors = [fixture("1"), fixture("2"), fixture("3")]
  const fantasy = fixture("4")
  const horror = { ...fixture("5"), themes: ["Terror"] }
  const games = [...anchors, horror, fantasy]
  const result = buildRecommendations(user, games, hardware)
  assert.deepEqual(result.pending.map((match) => match.game.id), ["4", "5"])
  assert.ok(result.pending[0].affinity > result.pending[1].affinity)
  assert.ok(result.pending[0].reasons.some((reason) => reason.includes("Temáticas do perfil: Fantasia")))
  assert.ok(result.pending[0].reasons.some((reason) => reason.includes("jogos âncora") && reason.includes("Fantasia")))
  assert.equal(result.items.length, 0) // Versão do SO continua pendente.
})

test("null de requisito não vira zero ou aprovação", () => {
  const game = fixture()
  game.platforms.Windows.minimum!.requirements.cpu_score = null
  const check = hardwareChecks(game, pc, hardware).find((check) => check.label === "Processador")
  assert.equal(check?.ok, null)
})
test("peça conhecida sem classificação permanece pendente", () => {
  const catalog = structuredClone(hardware)
  catalog.GPU[0].performance_score = null
  assert.equal(
    hardwareChecks(fixture(), pc, catalog).find((check) => check.label === "Placa de vídeo")?.ok,
    null,
  )
})
test("índices de versões diferentes não são comparados", () => {
  const catalog = structuredClone(hardware)
  catalog.CPU[0].score_version = "outra_versao"
  assert.equal(hardwareChecks(fixture(), pc, catalog)[0].ok, null)
})
test("CPU e GPU são comparadas em suas próprias escalas", () => {
  const catalog = structuredClone(hardware)
  catalog.CPU[0].performance_score = 1000
  catalog.GPU[0].performance_score = 500
  const checks = hardwareChecks(fixture(), pc, catalog)
  assert.equal(checks[0].ok, true)
  assert.equal(checks[1].ok, false)
})
test("Linux sem suporte nativo não herda os requisitos Windows", () => {
  const checks = hardwareChecks(fixture(), { ...pc, os: "Linux" }, hardware)
  assert.equal(checks[0].ok, null)
  assert.equal(checks[2].ok, null)
  assert.equal(checks[3].ok, false)
})
test("RAM é comparada com o requisito da plataforma selecionada", () => {
  assert.equal(hardwareChecks(fixture(), { ...pc, os: "macOS" }, hardware)[2].ok, false)
  assert.equal(hardwareChecks(fixture(), pc, hardware)[2].ok, true)
})
test("família do SO não confirma a versão exigida", () => {
  assert.equal(hardwareChecks(fixture(), pc, hardware)[3].ok, null)
  assert.equal(
    describeMatch(user, fixture("4"), [fixture("1"), fixture("2"), fixture("3")], hardware).compatibility,
    "needs_review",
  )
})
test("restrição confirmada prevalece sobre outras pendências", () => {
  const match = describeMatch(
    { ...user, hardware: { ...pc, ramGb: 4 } },
    fixture("4"),
    [fixture("1")],
    hardware,
  )
  assert.equal(match.compatibility, "incompatible")
  assert.equal(match.compatible, false)
})
test("recomendações excluem âncoras e separam pendências de restrições", () => {
  const games = [fixture("1"), fixture("2"), fixture("3"), fixture("4"), fixture("5")]
  games[4].platforms.Windows.minimum!.requirements.ram_gb = 32
  const result = buildRecommendations(user, games, hardware)
  assert.equal(result.items.length, 0)
  assert.deepEqual(
    result.pending.map((match) => match.game.id),
    ["4"],
  )
  assert.deepEqual(
    result.excluded.map((match) => match.game.id),
    ["5"],
  )
})
test("uma peça removida do catálogo exige nova seleção", () => {
  assert.equal(hardwareChecks(fixture(), pc, { ...hardware, CPU: [] })[0].ok, null)
  assert.equal(
    buildRecommendations(user, [fixture("1"), fixture("2"), fixture("3"), fixture("4")], {
      ...hardware,
      CPU: [],
    }).pending.length,
    0,
  )
})

test("temáticas sem classificação não são inventadas a partir de recursos", () => {
  const game = fixture("4")
  game.themes_status = "pending"
  const match = describeMatch(user, game, [fixture("1"), fixture("2"), fixture("3")], hardware)
  assert.equal(match.affinity, 100)
  assert(!match.reasons.some((reason) => reason.startsWith("Temáticas do perfil:")))
})

test("migração preserva conta, hardware e âncoras já escolhidas", () => {
  const previous = {
    ...user,
    catalogVersion: "steam-v1",
    themes: undefined,
    features: ["Um jogador"],
  } as unknown as UserProfile
  const next = migrateProfile(previous, ["RPG"], ["Fantasia"])
  assert.equal(next.id, user.id)
  assert.equal(next.email, user.email)
  assert.equal(next.password, user.password)
  assert.deepEqual(next.hardware, pc)
  assert.deepEqual(next.anchorIds, ["1", "2", "3"])
  assert.deepEqual(next.genres, ["RPG"])
  assert.deepEqual(next.themes, [])
  assert.equal("features" in next, false)
  assert.equal(next.catalogVersion, "steam-v2")
})

test("as temáticas anteriores válidas são preservadas", () => {
  const next = migrateProfile(user, ["RPG"], ["Fantasia"])
  assert.deepEqual(next.themes, ["Fantasia"])
  assert.deepEqual(next.genres, ["RPG"])
})

test("IDs antigos do mock não se tornam âncoras Steam", () => {
  const previous = {
    ...user,
    catalogVersion: undefined,
    anchorIds: ["hades", "hollow-knight", "the-witcher-3"],
  }
  const next = migrateProfile(previous, ["RPG"], ["Fantasia"])
  assert.deepEqual(next.anchorIds, [])
  assert.equal(next.hardware, null)
  assert.deepEqual(next.themes, ["Fantasia"])
})
