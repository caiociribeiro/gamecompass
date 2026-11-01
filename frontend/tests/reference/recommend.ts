// Referência congelada da etapa27, usada apenas pelos testes de paridade.
import type {
  Check, Compatibility, Game, GameMatch, HardwareAssessment, HardwareCatalog,
  HardwareProfile, Part, RequirementLevel, UserProfile,
} from "../../src/types.ts"
import { contentAffinity } from "./affinity.ts"
import { replacementOptions } from "./upgrades.ts"

export const MIN_AFFINITY = 28
const positive = (value: number | null | undefined): value is number =>
  typeof value === "number" && Number.isFinite(value) && value > 0

const WINDOWS_ORDER: Record<string, number> = { xp: 0, vista: 1, "7": 2, "8": 3, "8.1": 4, "10": 5, "11": 6 }

// Compara a versão mínima principal como heurística do TCC1, sem certificar a execução do jogo.
export function windowsCheck(
  text: string | null | undefined,
  version: HardwareProfile["windowsVersion"],
  level: RequirementLevel = "minimum",
): Check {
  const target = level === "minimum" ? "mínimo" : "recomendado"
  const pending = (detail: string): Check => ({ label: "Sistema operacional", ok: null, detail })
  if (version !== "10" && version !== "11")
    return pending("Informe e salve a versão do Windows na página de hardware.")
  if (!text) return pending(`Windows ${target} não informado pela Steam.`)
  // O perfil Windows já é de 64 bits. "64-bit only" não restringe a versão.
  const restrictions = text.replace(/\b(?:64[- ]?bits?|x64)\s+only\b/gi, "64-bit")
  if (/\b(?:server|phone|arm64|arm|only|somente|apenas|earlier|older|lower|not\s+supported)\b/i.test(restrictions))
    return pending(`O requisito possui restrições específicas: ${text}. Confira antes de jogar.`)
  const normalized = text.replace(/[®™]/g, "")
    .replace(/windows(?=\d)/gi, "Windows ")
    .replace(/(?<=\d)x(?:64|86)\b/gi, "")
  const versions: string[] = []
  // A função é chamada para o campo SO da plataforma Windows.
  let windows = /^(?:xp|vista)$/i.test(normalized.trim())
  for (const part of normalized.split(/\s*(?:[,;/]|\b(?:or|ou|and|e)\b)\s*/i)) {
    if (/\bwindows\b/i.test(part)) windows = true
    const explicit = part.match(/\bwindows\s*(xp|vista|7|8(?:\.1)?|10|11)\b/i)
    const abbreviated = windows ? part.match(/^(xp|vista|7|8(?:\.1)?|10|11)\b/i) : null
    if (explicit) windows = true
    const found = explicit ?? abbreviated
    if (found) versions.push(found[1].toLowerCase())
  }
  if (!versions.length) return pending(`Windows ${target} ainda não identificado: ${text}.`)
  const minimum = versions.reduce((a, b) => WINDOWS_ORDER[a] < WINDOWS_ORDER[b] ? a : b)
  const selected = WINDOWS_ORDER[version]
  if (selected === WINDOWS_ORDER[minimum] && /\b(?:build|version|vers[aã]o|compila[cç][aã]o)\s*[:=]?\s*\d/i.test(text))
    return pending(`Confira a atualização específica exigida: ${text}.`)
  const ok = selected >= WINDOWS_ORDER[minimum]
  return {
    label: "Sistema operacional",
    ok,
    detail: ok
      ? `Windows ${version} (64 bits) atende à versão do requisito ${target}. Steam: ${text}.`
      : `Windows ${version} informado; o requisito ${target} indica Windows ${minimum}.`,
    ...(!ok && minimum === "11" ? {
      suggestion: {
        name: "Windows 11 (64 bits)",
        detail: "Confira os requisitos de instalação do Windows antes de atualizar.",
      },
    } : {}),
  }
}

// Escolhe a menor faixa suficiente do mesmo tipo e versão. Não é uma cotação de compra.
export function replacementPart(
  parts: Part[], current: Part, required: number, scoreVersion: string,
): Part | undefined {
  return replacementOptions(parts, current, required, scoreVersion)[0]
}

export function hardwareChecks(
  game: Game,
  profile: HardwareProfile | null,
  catalog: HardwareCatalog,
  level: RequirementLevel = "minimum",
): Check[] {
  if (!profile) return []
  const platform = game.platforms[profile.os]
  const published = platform?.[level]
  const notesOnly = published?.requirements_kind === "notes_only"
  const block = notesOnly ? null : published
  const target = level === "minimum" ? "mínimo" : "recomendado"
  function partCheck(label: string, kind: "CPU" | "GPU", parts: Part[], id: string, required: number | null | undefined): Check {
    const part = parts.find((item) => item.id === id)
    if (!part) return { label, ok: null, detail: "Selecione novamente uma peça do catálogo atual." }
    if (
      !positive(part.performance_score) ||
      !block?.score_version || part.score_version !== block.score_version
    ) {
      return {
        label,
        ok: null,
        detail: `${part.name}: comparação com o requisito ${target} pendente.`,
      }
    }
    if (!positive(required)) {
      // Uma opção publicada e identificada basta para comprovar o OR.
      // Abaixo das opções conhecidas o resultado continua pendente.
      const alternatives = block.hardware?.[kind]?.alternatives ?? []
      const known = alternatives.filter((alternative) =>
        alternative.component_type === kind && alternative.status === "matched" &&
        alternative.score_status === "classified" && alternative.score_version === block.score_version &&
        alternative.name && positive(alternative.performance_score),
      )
      const proof = known.find((alternative) => part.performance_score! >= alternative.performance_score!)
      const query = block.hardware?.[kind]?.query?.trim()
      const reference = query && (query.length > 160 ? query.slice(0, 157) + "…" : query)
      const missing = block.issues.includes(`${kind}: campo ausente.`) && !block.hardware?.[kind]
      return proof
        ? { label, ok: true, detail: `${part.name} atende ao requisito ${target} usando a alternativa ${proof.name}.` }
        : { label, ok: null, detail: known.length
          ? `${part.name}: as alternativas identificadas não confirmam atendimento; outras opções ainda precisam de avaliação.`
          : missing
            ? `${part.name}: a Steam não informou ${kind === "CPU" ? "um processador" : "uma placa de vídeo"} no requisito ${target}.`
          : reference
            ? `${part.name}: referência da Steam ainda sem comparação (${reference}).`
            : `${part.name}: comparação com o requisito ${target} pendente.` }
    }
    const ok = part.performance_score >= required
    const manual = block?.curation?.find((item) => item.component_type === kind)
    const references = (block.hardware?.[kind]?.alternatives ?? []).filter((item) =>
      item.component_type === kind && item.status === "matched" && item.score_status === "classified" &&
      item.score_version === block.score_version && item.name && positive(item.performance_score))
      .map((item) => item.name!)
    const replacements = !ok ? replacementOptions(parts, part, required, block.score_version, references) : []
    const option = (candidate: Part) => ({ name: candidate.name, partId: candidate.id,
      detail: references.includes(candidate.name)
        ? manual ? "Modelo usado como referência manual para este requisito." : "Modelo identificado no requisito do jogo."
        : `Alternativa do catálogo que atende à comparação de desempenho para o requisito ${target}.` })
    const replacement = replacements[0]
    return {
      label,
      ok,
      detail: `${part.name} ${ok ? "atende ao" : "fica abaixo do"} requisito ${target}.` +
        (manual ? ` Referência estimada: ${manual.reference_models.join(" ou ")}.` : ""),
      ...(manual ? { estimated: true } : {}),
      ...(replacement ? {
        suggestion: { ...option(replacement), alternatives: replacements.slice(1).map(option) },
      } : {}),
    }
  }
  const ram = block?.requirements.ram_gb
  const checks: Check[] = [
    partCheck(
      "Processador", "CPU",
      catalog.CPU, profile.cpuId, block?.requirements.cpu_score,
    ),
    partCheck(
      "Placa de vídeo", "GPU",
      catalog.GPU, profile.gpuId, block?.requirements.gpu_score,
    ),
    {
      label: "Memória RAM",
      ok: positive(ram) && positive(profile.ramGb) ? profile.ramGb >= ram : null,
      detail: positive(ram)
        ? `${profile.ramGb} GB informados; ${target} de ${ram} GB.`
        : block?.issues.includes("RAM: campo ausente.")
          ? `A Steam não informou a quantidade de RAM do requisito ${target}.`
        : `Quantidade de RAM do requisito ${target} ainda não identificada.`,
      ...(positive(ram) && positive(profile.ramGb) && profile.ramGb < ram ? {
        suggestion: { name: `${ram} GB de RAM no total`, detail: `Capacidade total para atender ao requisito ${target}. Confira os módulos aceitos pelo computador.` },
      } : {}),
    },
    !block && level === "recommended"
      ? { label: "Sistema operacional", ok: null, detail: `Requisito ${target} não informado pela Steam.` }
      : platform?.native_support === false
      ? { label: "Sistema operacional", ok: false, detail: `A Steam não informa suporte nativo a ${profile.os}.` }
      : platform?.native_support !== true
        ? { label: "Sistema operacional", ok: null, detail: "Suporte nativo não informado pela Steam." }
        : profile.os === "Windows"
          ? windowsCheck(block?.os_text, profile.windowsVersion, level)
          : {
              label: "Sistema operacional", ok: null,
              detail: `Suporte nativo a ${profile.os}. Confira a versão exigida: ${block?.os_text || "não informada"}. A versão ainda exige conferência.`,
            },
  ]
  return notesOnly ? checks.map((check) => check.ok === false ? check : {
    ...check,
    detail: "A Steam publicou apenas observações neste nível; não informou uma especificação de hardware.",
  }) : checks
}

function checksCompatibility(checks: Check[]): Compatibility {
  return checks.some((check) => check.ok === false)
    ? "incompatible"
    : !checks.length || checks.some((check) => check.ok === null) ? "needs_review" : "compatible"
}

export function assessHardware(
  game: Game, profile: HardwareProfile | null, catalog: HardwareCatalog, level: RequirementLevel,
): HardwareAssessment {
  const checks = hardwareChecks(game, profile, catalog, level)
  return {
    available: Boolean(profile && game.platforms[profile.os]?.[level]
      && game.platforms[profile.os][level]?.requirements_kind !== "notes_only"),
    checks,
    compatibility: checksCompatibility(checks),
  }
}

export function compatibilityLabel(match: Pick<GameMatch, "compatibility" | "meets" | "estimated">): string {
  const label = match.meets === "recommended" ? "Atende aos recomendados"
    : match.meets === "minimum" ? "Atende aos mínimos"
      : match.compatibility === "incompatible" ? "Não atende aos mínimos" : "Validação dos mínimos pendente"
  return match.estimated && match.compatibility !== "needs_review" ? `${label} (estimativa)` : label
}

export function anchorsOf(user: UserProfile, games: Game[]) {
  return [...new Set(user.anchorIds)]
    .map((id) => games.find((game) => game.id === id))
    .filter((game): game is Game => Boolean(game))
}

export function describeMatch(
  user: UserProfile,
  game: Game,
  games: Game[],
  hardware: HardwareCatalog,
): GameMatch {
  const anchors = anchorsOf(user, games)
  const { affinity, reasons, anchorMatches, preferredGenres } = contentAffinity(user, game, anchors)
  const assessments = {
    minimum: assessHardware(game, user.hardware, hardware, "minimum"),
    recommended: assessHardware(game, user.hardware, hardware, "recommended"),
  }
  const { checks } = assessments.minimum
  // Os recomendados publicados são uma condição suficiente, desde que
  // nenhum requisito mínimo conhecido tenha sido descumprido.
  const compatibility = assessments.minimum.compatibility === "needs_review" &&
    assessments.recommended.compatibility === "compatible"
    ? "compatible" : assessments.minimum.compatibility
  const meets = compatibility === "compatible"
    ? assessments.recommended.compatibility === "compatible" ? "recommended" : "minimum"
    : null
  return {
    game,
    affinity,
    reasons,
    anchorMatches,
    preferredGenres,
    checks,
    compatibility,
    meets,
    estimated: assessments[meets ?? "minimum"].checks.some((check) => check.estimated),
    assessments,
    compatible: compatibility === "compatible",
    anchor: anchors.some((item) => item.id === game.id),
  }
}

export function hardwareProfileReady(profile: HardwareProfile | null, hardware: HardwareCatalog) {
  return Boolean(
    profile && positive(profile.ramGb) &&
    (profile.os === "Windows" || profile.os === "Linux" || profile.os === "macOS") &&
    (profile.os !== "Windows" || profile.windowsVersion === "10" || profile.windowsVersion === "11") &&
    hardware.CPU.some((part) => part.id === profile.cpuId) &&
    hardware.GPU.some((part) => part.id === profile.gpuId),
  )
}

export function profileReady(user: UserProfile, games: Game[], hardware: HardwareCatalog) {
  return (
    user.genres.length > 0 &&
    user.themes.length > 0 &&
    anchorsOf(user, games).length === 3 &&
    hardwareProfileReady(user.hardware, hardware)
  )
}

export function buildRecommendations(user: UserProfile, games: Game[], hardware: HardwareCatalog) {
  if (!profileReady(user, games, hardware))
    return { items: [] as GameMatch[], pending: [] as GameMatch[], excluded: [] as GameMatch[] }
  const ranked = games
    .map((game) => describeMatch(user, game, games, hardware))
    .filter((match) => !match.anchor && match.affinity >= MIN_AFFINITY)
    .sort((a, b) => b.affinity - a.affinity || a.game.title.localeCompare(b.game.title, "pt-BR") || a.game.id.localeCompare(b.game.id))
  return {
    items: ranked.filter((match) => match.compatibility === "compatible"),
    pending: ranked.filter((match) => match.compatibility === "needs_review"),
    excluded: ranked.filter((match) => match.compatibility === "incompatible"),
  }
}
