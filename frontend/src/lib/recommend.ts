import { GAMES, findGame } from "../data/catalog"
import { findCpu, findGpu } from "../data/hardware"
import type { Game, GameMatch, HardwareProfile, UserProfile } from "../types"

export const MIN_AFFINITY = 28

function overlap(values: string[], selected: string[] | Set<string>) {
  const set = selected instanceof Set ? selected : new Set(selected)
  return values.filter((value) => set.has(value))
}

function hardwareChecks(game: Game, hardware: HardwareProfile | null) {
  if (!hardware) return []
  const cpu = findCpu(hardware.cpuId)
  const gpu = findGpu(hardware.gpuId)
  const systemOk = game.systems.includes(hardware.os)
  return [
    {
      label: "Processador",
      ok: Boolean(cpu && cpu.score >= game.minCpu),
      detail: cpu?.name ?? "Componente fora da base",
    },
    {
      label: "Placa de vídeo",
      ok: Boolean(gpu && gpu.score >= game.minGpu),
      detail: gpu?.name ?? "Componente fora da base",
    },
    {
      label: "Memória",
      ok: hardware.ramGb >= game.minRam,
      detail: `${hardware.ramGb} GB informados, mínimo de ${game.minRam} GB`,
    },
    {
      label: "Sistema",
      ok: systemOk,
      detail: systemOk ? hardware.os : `${hardware.os} não está entre os sistemas deste jogo`,
    },
  ]
}

export function anchorsOf(user: UserProfile) {
  return user.anchorIds.map((id) => findGame(id)).filter((game): game is Game => Boolean(game))
}

export function describeMatch(user: UserProfile, game: Game): GameMatch {
  const anchors = anchorsOf(user)
  const anchor = anchors.some((item) => item.id === game.id)
  const anchorGenres = new Set(anchors.flatMap((item) => item.genres))
  const anchorThemes = new Set(anchors.flatMap((item) => item.themes))
  const genreUser = overlap(game.genres, user.genres)
  const themeUser = overlap(game.themes, user.themes)
  const genreAnchor = overlap(game.genres, anchorGenres)
  const themeAnchor = overlap(game.themes, anchorThemes)
  const sameStudio = anchors.find((item) => item.developer === game.developer && item.id !== game.id)

  const genreUserScore = user.genres.length ? genreUser.length / user.genres.length : 0
  const themeUserScore = user.themes.length ? themeUser.length / user.themes.length : 0
  const genreAnchorScore = anchorGenres.size ? genreAnchor.length / anchorGenres.size : 0
  const themeAnchorScore = anchorThemes.size ? themeAnchor.length / anchorThemes.size : 0
  const affinity = Math.round(
    (genreUserScore * 0.25 +
      themeUserScore * 0.2 +
      genreAnchorScore * 0.3 +
      themeAnchorScore * 0.2 +
      (sameStudio ? 0.05 : 0)) *
      100,
  )

  const reasons: string[] = []
  if (genreUser.length) reasons.push(`Gêneros do seu perfil: ${genreUser.join(", ")}.`)
  if (themeUser.length) reasons.push(`Temáticas do seu perfil: ${themeUser.join(", ")}.`)
  const shared = [...new Set([...genreAnchor, ...themeAnchor])]
  if (shared.length) reasons.push(`Em comum com os jogos âncora: ${shared.slice(0, 4).join(", ")}.`)
  if (sameStudio) reasons.push(`Mesmo estúdio de ${sameStudio.title}.`)

  const checks = hardwareChecks(game, user.hardware)
  return {
    game,
    affinity,
    reasons,
    checks,
    compatible: checks.length > 0 && checks.every((check) => check.ok),
    anchor,
  }
}

export function profileReady(user: UserProfile) {
  return user.genres.length > 0 && user.themes.length > 0 && anchorsOf(user).length === 3 && user.hardware !== null
}

export function buildRecommendations(user: UserProfile) {
  if (!profileReady(user)) return { items: [] as GameMatch[], excluded: [] as GameMatch[] }

  const ranked = GAMES.map((game) => describeMatch(user, game))
    .filter((match) => !match.anchor && match.affinity >= MIN_AFFINITY)
    .sort((a, b) => b.affinity - a.affinity || a.game.title.localeCompare(b.game.title, "pt-BR"))

  return {
    items: ranked.filter((match) => match.compatible),
    excluded: ranked.filter((match) => !match.compatible),
  }
}
