import type { Check, Game, GameMatch, HardwareCatalog, HardwareProfile, Part, UserProfile } from "../types"

export const MIN_AFFINITY = 28
const positive = (value: number | null | undefined): value is number =>
  typeof value === "number" && Number.isFinite(value) && value > 0

function overlap(values: string[], selected: string[] | Set<string>) {
  const set = selected instanceof Set ? selected : new Set(selected)
  return values.filter((value) => set.has(value))
}

export function hardwareChecks(
  game: Game,
  profile: HardwareProfile | null,
  catalog: HardwareCatalog,
): Check[] {
  if (!profile) return []
  const platform = game.platforms[profile.os]
  const minimum = platform?.minimum
  function partCheck(label: string, part: Part | undefined, required: number | null | undefined): Check {
    if (!part) return { label, ok: null, detail: "Selecione novamente uma peça do catálogo atual." }
    if (
      !positive(part.performance_score) ||
      !positive(required) ||
      part.score_version !== minimum?.score_version
    ) {
      return {
        label,
        ok: null,
        detail: `${part.name}: classificação ou requisito ainda pendente de revisão.`,
      }
    }
    return {
      label,
      ok: part.performance_score >= required,
      detail: `${part.name}: classe ${part.performance_score}; requisito mínimo ${required} (${part.score_version}).`,
    }
  }
  const ram = minimum?.requirements.ram_gb
  return [
    partCheck(
      "Processador",
      catalog.CPU.find((part) => part.id === profile.cpuId),
      minimum?.requirements.cpu_score,
    ),
    partCheck(
      "Placa de vídeo",
      catalog.GPU.find((part) => part.id === profile.gpuId),
      minimum?.requirements.gpu_score,
    ),
    {
      label: "Memória RAM",
      ok: positive(ram) ? profile.ramGb >= ram : null,
      detail: positive(ram)
        ? `${profile.ramGb} GB informados; mínimo de ${ram} GB.`
        : "Quantidade mínima ainda não identificada.",
    },
    {
      label: "Sistema operacional",
      ok: platform?.native_support === false ? false : null,
      detail:
        platform?.native_support === false
          ? `A Steam não informa suporte nativo a ${profile.os}.`
          : platform?.native_support === true
            ? `Suporte nativo a ${profile.os}. Confira a versão exigida: ${minimum?.os_text || "não informada"}. A validação de versão está pendente.`
            : "Suporte nativo não informado pela Steam.",
    },
  ]
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
  const anchorGenres = new Set(anchors.flatMap((item) => item.genres))
  const anchorThemes = new Set(
    anchors.filter((item) => item.themes_status === "classified").flatMap((item) => item.themes),
  )
  const genreUser = overlap(game.genres, user.genres)
  const themeUser = game.themes_status === "classified" ? overlap(game.themes, user.themes) : []
  const genreAnchor = overlap(game.genres, anchorGenres)
  const themeAnchor = game.themes_status === "classified" ? overlap(game.themes, anchorThemes) : []
  const sameStudio = game.developer
    ? anchors.find((item) => item.developer === game.developer && item.id !== game.id)
    : undefined
  const components = [
    { value: user.genres.length ? genreUser.length / user.genres.length : 0, weight: 0.25 },
    { value: anchorGenres.size ? genreAnchor.length / anchorGenres.size : 0, weight: 0.3 },
    { value: sameStudio ? 1 : 0, weight: 0.05 },
  ]
  // A falta de classificação temática não é interpretada como desinteresse.
  if (game.themes_status === "classified" && user.themes.length)
    components.push({ value: themeUser.length / user.themes.length, weight: 0.2 })
  if (game.themes_status === "classified" && anchorThemes.size)
    components.push({ value: themeAnchor.length / anchorThemes.size, weight: 0.2 })
  const affinity = Math.round(
    (100 * components.reduce((sum, item) => sum + item.value * item.weight, 0)) /
      components.reduce((sum, item) => sum + item.weight, 0),
  )
  const reasons: string[] = []
  if (genreUser.length) reasons.push(`Gêneros do perfil: ${genreUser.join(", ")}.`)
  if (themeUser.length) reasons.push(`Temáticas do perfil: ${themeUser.join(", ")}.`)
  const shared = [...new Set([...genreAnchor, ...themeAnchor])]
  if (shared.length) reasons.push(`Em comum com seus jogos âncora: ${shared.slice(0, 4).join(", ")}.`)
  if (sameStudio) reasons.push(`Mesmo estúdio de ${sameStudio.title}.`)
  const checks = hardwareChecks(game, user.hardware, hardware)
  const compatibility = checks.some((check) => check.ok === false)
    ? "incompatible"
    : checks.length === 0 || checks.some((check) => check.ok === null)
      ? "needs_review"
      : "compatible"
  return {
    game,
    affinity,
    reasons,
    checks,
    compatibility,
    compatible: compatibility === "compatible",
    anchor: anchors.some((item) => item.id === game.id),
  }
}

export function profileReady(user: UserProfile, games: Game[], hardware: HardwareCatalog) {
  return (
    user.genres.length > 0 &&
    user.themes.length > 0 &&
    anchorsOf(user, games).length === 3 &&
    user.hardware !== null &&
    hardware.CPU.some((part) => part.id === user.hardware?.cpuId) &&
    hardware.GPU.some((part) => part.id === user.hardware?.gpuId)
  )
}

export function buildRecommendations(user: UserProfile, games: Game[], hardware: HardwareCatalog) {
  if (!profileReady(user, games, hardware))
    return { items: [] as GameMatch[], pending: [] as GameMatch[], excluded: [] as GameMatch[] }
  const ranked = games
    .map((game) => describeMatch(user, game, games, hardware))
    .filter((match) => !match.anchor && match.affinity >= MIN_AFFINITY)
    .sort((a, b) => b.affinity - a.affinity || a.game.title.localeCompare(b.game.title, "pt-BR"))
  return {
    items: ranked.filter((match) => match.compatibility === "compatible"),
    pending: ranked.filter((match) => match.compatibility === "needs_review"),
    excluded: ranked.filter((match) => match.compatibility === "incompatible"),
  }
}
