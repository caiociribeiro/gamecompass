import assert from "node:assert/strict"
import { test } from "node:test"
import { buildRecommendations, compatibilityLabel, describeMatch, hardwareChecks, hardwareProfileReady, profileReady, replacementPart, windowsCheck } from "../src/lib/recommend.ts"
import { hardwareSummary } from "../src/lib/hardware.ts"
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
const pc: HardwareProfile = { cpuId: "cpu", gpuId: "gpu", ramGb: 16, os: "Windows", windowsVersion: "11" }
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
  assert.deepEqual(result.items.map((match) => match.game.id), ["4", "5"])
  assert.ok(result.items[0].affinity > result.items[1].affinity)
  assert.ok(result.items[0].reasons.some((reason) => reason.includes("Temáticas do perfil: Fantasia")))
  assert.ok(result.items[0].reasons.some((reason) => reason.includes("Em comum com Jogo fixture 1") && reason.includes("Fantasia")))
  assert.equal(result.pending.length, 0)
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
  const previous = { ...pc, windowsVersion: undefined }
  assert.equal(hardwareChecks(fixture(), previous, hardware)[3].ok, null)
  assert.equal(
    describeMatch({ ...user, hardware: previous }, fixture("4"), [fixture("1"), fixture("2"), fixture("3")], hardware).compatibility,
    "needs_review",
  )
  assert.equal(profileReady({ ...user, hardware: previous }, [fixture("1"), fixture("2"), fixture("3")], hardware), false)
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
  assert.equal(result.items.length, 1)
  assert.deepEqual(
    result.items.map((match) => match.game.id),
    ["4"],
  )
  assert.equal(result.pending.length, 0)
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

test("Windows 10 atende Windows 10 e Windows 11 atende ao mínimo Windows 10", () => {
  assert.equal(windowsCheck("64-bit Windows 10", "10").ok, true)
  assert.equal(windowsCheck("Windows 10 - 64-bit", "11").ok, true)
})

test("Windows 10 fica abaixo do requisito Windows 11", () => {
  assert.equal(windowsCheck("64-bit Windows 11", "10").ok, false)
  const game = fixture("4")
  game.platforms.Windows.minimum!.os_text = "64-bit Windows 11"
  assert.equal(describeMatch({ ...user, hardware: { ...pc, windowsVersion: "10" } }, game, [], hardware).compatibility, "incompatible")
})

test("listas de versões Windows e sufixos x64 usam a menor versão indicada", () => {
  for (const text of ["Windows 10/11", "Windows 11 or Windows 10", "Windows 7 / Vista / XP",
    "Windows Xp, Vista, 7, 8/8.1, 10", "Windows 7x64 / Windows 8.1x64 / Windows 10x64",
    "Windows10 (64-bit)", "Windows 7 SP1", "Windows 7 or newer"]) {
    assert.equal(windowsCheck(text, "10").ok, true, text)
  }
})

test("build específica exige conferência dentro da mesma versão principal", () => {
  const text = "Windows 10 version 21H1 (build 19043) or newer"
  assert.equal(windowsCheck(text, "10").ok, null)
  assert.equal(windowsCheck(text, "11").ok, true)
})

test("SO sem versão identificável ou com restrições específicas fica pendente", () => {
  for (const text of [null, "Windows 64-bit", "Windows 12", "Linux Ubuntu 22.04", "macOS 15.5",
    "Windows Server 2019", "Windows 10 ARM64", "Windows 10 only"]) {
    assert.equal(windowsCheck(text, "11").ok, null, String(text))
  }
})

test("Windows sem confirmação de suporte nativo não recebe aprovação de versão", () => {
  const game = fixture()
  game.platforms.Windows.native_support = null
  assert.equal(hardwareChecks(game, pc, hardware)[3].ok, null)
  game.platforms.Windows.native_support = false
  assert.equal(hardwareChecks(game, pc, hardware)[3].ok, false)
})

test("macOS mantém conferência própria e não herda a versão do Windows", () => {
  assert.equal(hardwareChecks(fixture(), { ...pc, os: "macOS" }, hardware)[3].ok, null)
})

test("versão salva aparece no resumo e perfis incompletos precisam ser atualizados", () => {
  assert.match(hardwareSummary(pc, hardware)!.text, /Windows 11 \(64 bits\)/)
  assert.equal(hardwareProfileReady(pc, hardware), true)
  assert.equal(hardwareProfileReady({ ...pc, windowsVersion: undefined }, hardware), false)
  assert.equal(hardwareProfileReady({ ...pc, ramGb: 0 }, hardware), false)
})

test("um campo de hardware pendente continua impedindo aprovação mesmo com Windows válido", () => {
  const game = fixture("4")
  game.platforms.Windows.minimum!.requirements.gpu_score = null
  const result = buildRecommendations(user, [fixture("1"), fixture("2"), fixture("3"), game], hardware)
  assert.equal(result.items.length, 0)
  assert.deepEqual(result.pending.map((match) => match.game.id), ["4"])
})

function withRecommended(): Game {
  const game = fixture("4")
  game.platforms.Windows.recommended = structuredClone(game.platforms.Windows.minimum)
  game.platforms.Windows.recommended!.requirements = { ram_gb: 16, cpu_score: 500, gpu_score: 650 }
  return game
}

test("mínimos e recomendados são avaliados separadamente e o card informa o maior nível atendido", () => {
  const game = withRecommended()
  const minimum = describeMatch(user, game, [], hardware)
  assert.equal(minimum.compatible, true)
  assert.equal(minimum.meets, "minimum")
  assert.equal(compatibilityLabel(minimum), "Atende aos mínimos")
  assert.equal(minimum.assessments.minimum.compatibility, "compatible")
  assert.equal(minimum.assessments.recommended.compatibility, "incompatible")
  const catalog = structuredClone(hardware)
  catalog.CPU[0].performance_score = 500
  catalog.GPU[0].performance_score = 650
  const recommended = describeMatch(user, game, [], catalog)
  assert.equal(recommended.meets, "recommended")
  assert.equal(compatibilityLabel(recommended), "Atende aos recomendados")
})

test("recomendados ausentes não herdam os mínimos nem impedem aprovação dos mínimos", () => {
  const match = describeMatch(user, fixture("4"), [], hardware)
  assert.equal(match.meets, "minimum")
  assert.equal(match.assessments.recommended.available, false)
  assert.equal(match.assessments.recommended.compatibility, "needs_review")
  assert(match.assessments.recommended.checks.every((check) => check.ok === null && !check.suggestion))
})

test("recomendados incompletos não são aprovados a partir de um status genérico resolved", () => {
  const game = withRecommended()
  game.platforms.Windows.recommended!.requirements = { ram_gb: 16, cpu_score: null, gpu_score: 550 }
  const match = describeMatch(user, game, [], hardware)
  assert.equal(match.meets, "minimum")
  assert.equal(match.assessments.recommended.compatibility, "needs_review")
  assert.equal(match.assessments.recommended.checks[0].suggestion, undefined)
})

test("uma aprovação dos recomendados não esconde uma falha conhecida nos mínimos", () => {
  const game = withRecommended()
  game.platforms.Windows.recommended = structuredClone(game.platforms.Windows.minimum)
  game.platforms.Windows.minimum!.requirements.cpu_score = 500
  let match = describeMatch(user, game, [], hardware)
  assert.equal(match.assessments.recommended.compatibility, "compatible")
  assert.equal(match.meets, null)
  assert.equal(compatibilityLabel(match), "Não atende aos mínimos")
  game.platforms.Windows.minimum!.requirements.cpu_score = null
  match = describeMatch(user, game, [], hardware)
  assert.equal(match.assessments.minimum.checks[0].ok, null)
  assert.equal(match.meets, "recommended")
  assert.equal(compatibilityLabel(match), "Atende aos recomendados")
})

test("substituição busca a menor faixa suficiente, sem alterar o catálogo ou trocar CPU por GPU", () => {
  const catalog = structuredClone(hardware)
  catalog.CPU[0].performance_score = 100
  catalog.CPU.push(
    { ...catalog.CPU[0], id: "cpu-top", name: "CPU topo", performance_score: 700 },
    { ...catalog.CPU[0], id: "cpu-fit", name: "CPU suficiente", performance_score: 400 },
    { ...catalog.CPU[0], id: "cpu-low", name: "CPU insuficiente", performance_score: 350 },
  )
  const before = structuredClone(catalog)
  const checks = hardwareChecks(fixture(), pc, catalog)
  assert.equal(checks[0].ok, false)
  assert.equal(checks[0].suggestion?.partId, "cpu-fit")
  assert.equal(checks[1].suggestion, undefined)
  assert.deepEqual(catalog, before)
  assert.equal(hardwareChecks(fixture(), { ...pc, cpuId: "cpu-fit" }, catalog)[0].ok, true)
})

test("cada nível sugere uma substituição própria para a GPU que não atende", () => {
  const catalog = structuredClone(hardware)
  catalog.GPU[0].performance_score = 100
  catalog.GPU.push(
    { ...catalog.GPU[0], id: "gpu-min", name: "GPU mínimo", performance_score: 550 },
    { ...catalog.GPU[0], id: "gpu-rec", name: "GPU recomendado", performance_score: 650 },
  )
  const match = describeMatch(user, withRecommended(), [], catalog)
  assert.equal(match.assessments.minimum.checks[1].suggestion?.partId, "gpu-min")
  assert.equal(match.assessments.recommended.checks[1].suggestion?.partId, "gpu-rec")
})

test("substituições ignoram peças sem nota, não finitas ou de outra versão", () => {
  const current = { ...hardware.CPU[0], performance_score: 100 }
  const parts = [
    { ...current, id: "pending", performance_score: null },
    { ...current, id: "infinite", performance_score: Infinity },
    { ...current, id: "other", performance_score: 400, score_version: "manual_v2" },
    { ...current, id: "fit", name: "CPU válida", performance_score: 500 },
  ]
  assert.equal(replacementPart(parts, current, 400, "manual_v1")?.id, "fit")
  assert.equal(replacementPart(parts.slice(0, 3), current, 400, "manual_v1"), undefined)
})

test("desempate de substituições é estável e não depende da ordem do catálogo", () => {
  const current = { ...hardware.CPU[0], performance_score: 100 }
  const a = { ...current, id: "a", name: "AMD fixture", performance_score: 400 }
  const b = { ...current, id: "b", name: "Intel fixture", performance_score: 400 }
  assert.equal(replacementPart([b, a], current, 400, "manual_v1")?.id, "a")
  assert.equal(replacementPart([a, b], current, 400, "manual_v1")?.id, "a")
})

test("peça já suficiente ou de versão incompatível não recebe sugestão de troca", () => {
  assert.equal(replacementPart(hardware.CPU, hardware.CPU[0], 400, "manual_v1"), undefined)
  assert.equal(replacementPart(hardware.CPU, hardware.CPU[0], 500, "manual_v2"), undefined)
  assert.equal(replacementPart(hardware.CPU, hardware.CPU[0], 0, "manual_v1"), undefined)
})

test("requisito pendente não gera falha nem sugestão inventada", () => {
  const game = withRecommended()
  game.platforms.Windows.minimum!.requirements.cpu_score = null
  const checks = hardwareChecks(game, pc, hardware)
  assert.equal(checks[0].ok, null)
  assert.equal(checks[0].suggestion, undefined)
  assert.equal(checks[1].ok, true)
})

test("sem substituto suficiente a falha permanece e não se sugere a peça mais forte abaixo do requisito", () => {
  const game = fixture()
  game.platforms.Windows.minimum!.requirements.gpu_score = 1000
  const check = hardwareChecks(game, pc, hardware)[1]
  assert.equal(check.ok, false)
  assert.equal(check.suggestion, undefined)
})

test("RAM indica a capacidade total de cada nível e nunca a diferença como se fosse o total", () => {
  const game = withRecommended()
  const profile = { ...pc, ramGb: 4 }
  assert.equal(hardwareChecks(game, profile, hardware)[2].suggestion?.name, "8 GB de RAM no total")
  assert.equal(hardwareChecks(game, profile, hardware, "recommended")[2].suggestion?.name, "16 GB de RAM no total")
  assert.equal(hardwareChecks(game, { ...pc, ramGb: 0 }, hardware)[2].ok, null)
})

test("Windows do requisito recomendado é comparado sem reutilizar o texto do mínimo", () => {
  const game = withRecommended()
  game.platforms.Windows.recommended!.os_text = "Windows 11"
  const checks = hardwareChecks(game, { ...pc, windowsVersion: "10" }, hardware, "recommended")
  assert.equal(checks[3].ok, false)
  assert.equal(checks[3].suggestion?.name, "Windows 11 (64 bits)")
  assert.match(checks[3].detail, /recomendado/)
  assert.equal(hardwareChecks(game, { ...pc, windowsVersion: "10" }, hardware)[3].ok, true)
})

test("Linux sem suporte não recebe sugestão de uma peça Windows", () => {
  const checks = hardwareChecks(withRecommended(), { ...pc, os: "Linux" }, hardware)
  assert.equal(checks[3].ok, false)
  assert(checks.every((check) => !check.suggestion))
})

test("textos apresentados ao usuário não expõem a classe ou versão do índice", () => {
  const match = describeMatch(user, withRecommended(), [], hardware)
  for (const assessment of Object.values(match.assessments)) {
    for (const check of assessment.checks) {
      assert.doesNotMatch(check.detail, /classe|manual_v1|classificação|score/i)
      if (check.suggestion) assert.doesNotMatch(check.suggestion.detail, /classe|manual_v1|classificação|score/i)
    }
  }
})

test("a lista mantém jogos que atendem aos mínimos e separa os que falham nos mínimos", () => {
  const recommended = fixture("4")
  recommended.platforms.Windows.recommended = structuredClone(recommended.platforms.Windows.minimum)
  const minimum = withRecommended()
  minimum.id = "5"
  const failed = fixture("6")
  failed.platforms.Windows.minimum!.requirements.ram_gb = 32
  const games = [fixture("1"), fixture("2"), fixture("3"), recommended, minimum, failed]
  const result = buildRecommendations(user, games, hardware)
  assert.deepEqual(result.items.map((match) => [match.game.id, match.meets]), [["4", "recommended"], ["5", "minimum"]])
  assert.deepEqual(result.excluded.map((match) => match.game.id), ["6"])
})

function alternative(name: string, score: number | null = 300) {
  return { status: "matched" as const, component_type: "GPU" as const, name,
    performance_score: score, score_version: "manual_v1", score_status: score === null ? "pending" as const : "classified" as const }
}

test("uma alternativa publicada suficiente comprova o OR mesmo com outro modelo desconhecido", () => {
  const game = withRecommended()
  const block = game.platforms.Windows.recommended!
  block.requirements = { ram_gb: 16, cpu_score: 400, gpu_score: null }
  block.hardware = { GPU: { alternatives: [alternative("GPU publicada"), {
    status: "not_found", component_type: "GPU", name: null, performance_score: null,
    score_status: "not_found", score_version: null,
  }] } }
  const match = describeMatch(user, game, [], hardware)
  assert.equal(match.meets, "recommended")
  assert.match(match.assessments.recommended.checks[1].detail, /alternativa GPU publicada/)
  assert.equal(block.requirements.gpu_score, null)
})

test("abaixo das alternativas conhecidas a comparação parcial permanece pendente e não inventa troca", () => {
  const game = fixture()
  game.platforms.Windows.minimum!.requirements.gpu_score = null
  game.platforms.Windows.minimum!.hardware = { GPU: { alternatives: [alternative("GPU muito forte", 700)] } }
  const check = hardwareChecks(game, pc, hardware)[1]
  assert.equal(check.ok, null)
  assert.equal(check.suggestion, undefined)
})

test("prova parcial rejeita nota pendente, tipo errado e versão incompatível", () => {
  const game = fixture()
  const block = game.platforms.Windows.minimum!
  block.requirements.gpu_score = null
  for (const invalid of [alternative("GPU pendente", null),
    { ...alternative("GPU outra versão"), score_version: "manual_v2" },
    { ...alternative("CPU não é GPU"), component_type: "CPU" as const },
    { ...alternative("GPU inválida"), performance_score: Infinity }]) {
    block.hardware = { GPU: { alternatives: [invalid] } }
    assert.equal(hardwareChecks(game, pc, hardware)[1].ok, null)
  }
})

test("uma alternativa de CPU também pode comprovar uma lista parcialmente identificada", () => {
  const game = fixture()
  const block = game.platforms.Windows.minimum!
  block.requirements.cpu_score = null
  block.hardware = { CPU: { alternatives: [{ ...alternative("CPU publicada", 300), component_type: "CPU" }] } }
  assert.equal(hardwareChecks(game, pc, hardware)[0].ok, true)
})

test("recomendados suficientes concluem a comparação com mínimo genérico sem apagar a pendência original", () => {
  const game = fixture("4")
  game.platforms.Windows.recommended = structuredClone(game.platforms.Windows.minimum)
  game.platforms.Windows.minimum!.requirements.cpu_score = null
  const result = buildRecommendations(user, [fixture("1"), fixture("2"), fixture("3"), game], hardware)
  assert.equal(result.items[0].meets, "recommended")
  assert.equal(result.items[0].assessments.minimum.compatibility, "needs_review")
  assert.equal(result.items[0].checks[0].ok, null)
})

test("recomendados ausentes ou parciais não liberam um mínimo genérico", () => {
  const game = withRecommended()
  game.platforms.Windows.minimum!.requirements.cpu_score = null
  assert.equal(describeMatch(user, game, [], hardware).meets, null)
  game.platforms.Windows.recommended = null
  assert.equal(describeMatch(user, game, [], hardware).meets, null)
})

function estimatedFixture() {
  const game = fixture("4")
  game.platforms.Windows.minimum!.curation = [{
    component_type: "CPU", method: "manual_reference", original_query: "CPU genérica fixture",
    reference_models: ["CPU de referência fixture"], source_url: "https://example.org/fixture",
    notes: "Referência fictícia para testar a indicação de estimativa.",
  }]
  return game
}

test("comparação por referência manual aparece como estimativa sem expor classes", () => {
  const game = estimatedFixture()
  const match = describeMatch(user, game, [], hardware)
  assert.equal(match.meets, "minimum")
  assert.equal(match.estimated, true)
  assert.equal(compatibilityLabel(match), "Atende aos mínimos (estimativa)")
  assert.match(match.checks[0].detail, /Referência estimada: CPU de referência fixture/)
  assert.doesNotMatch(match.checks[0].detail, /manual_v1|classe|400/)
  assert.equal(game.platforms.Windows.minimum!.text, "Requisitos fixture")
})

test("indicação de estimativa acompanha o nível efetivamente atendido", () => {
  const game = estimatedFixture()
  game.platforms.Windows.recommended = structuredClone(game.platforms.Windows.minimum)
  game.platforms.Windows.recommended!.curation = undefined
  const match = describeMatch(user, game, [], hardware)
  assert.equal(match.meets, "recommended")
  assert.equal(match.estimated, false)
  assert.equal(compatibilityLabel(match), "Atende aos recomendados")
})

test("falha em referência manual mantém a sugestão e identifica a estimativa", () => {
  const game = estimatedFixture()
  game.platforms.Windows.minimum!.requirements.cpu_score = 450
  const catalog = structuredClone(hardware)
  catalog.CPU.push({ ...hardware.CPU[0], id: "cpu-forte", name: "CPU suficiente fixture", performance_score: 500 })
  const match = describeMatch(user, game, [], catalog)
  assert.equal(match.compatibility, "incompatible")
  assert.equal(compatibilityLabel(match), "Não atende aos mínimos (estimativa)")
  assert.equal(match.checks[0].suggestion?.name, "CPU suficiente fixture")
})
