import type { Game, UserProfile } from "../types"
import { fold } from "./text.ts"

const key = (value: string) => fold(value.trim().replace(/\s+/g, " "))
const unique = (values: string[]) => [...new Map(values.map((value) => [key(value), value.trim()])).values()]
const keys = (values: string[]) => new Set(values.map(key))

function shared(values: string[], selected: string[]) {
  const wanted = keys(selected)
  return unique(values).filter((value) => wanted.has(key(value)))
}

// Compara conjuntos: a quantidade de categorias de uma âncora não altera as demais.
export function facetSimilarity(left: string[], right: string[]) {
  const a = keys(left), b = keys(right)
  const union = new Set([...a, ...b])
  return union.size ? [...a].filter((value) => b.has(value)).length / union.size : 0
}

function preferenceCoverage(values: string[], selected: string[]) {
  const wanted = unique(selected)
  return wanted.length ? shared(values, wanted).length / wanted.length : 0
}

// Cada âncora participa; a mais próxima recebe maior peso sem depender da ordem de seleção.
function anchorAggregate(values: number[]) {
  const weights = [0.6, 0.25, 0.15]
  const ordered = [...values].sort((a, b) => b - a).slice(0, 3)
  const total = ordered.reduce((sum, _, index) => sum + weights[index], 0)
  return total ? ordered.reduce((sum, value, index) => sum + value * weights[index], 0) / total : 0
}

export function contentAffinity(user: Pick<UserProfile, "genres" | "themes">, game: Game, anchors: Game[]) {
  const genreUser = shared(game.genres, user.genres)
  const themeUser = game.themes_status === "classified" ? shared(game.themes, user.themes) : []
  const genreAnchors = anchors.filter((anchor) => anchor.genres.length)
  const themeAnchors = anchors.filter((anchor) => anchor.themes_status === "classified" && anchor.themes.length)
  const sameStudio = game.developer.trim()
    ? anchors.find((anchor) => anchor.id !== game.id && key(anchor.developer) === key(game.developer))
    : undefined
  const components: { value: number; weight: number }[] = []
  if (game.genres.length && user.genres.length)
    components.push({ value: preferenceCoverage(game.genres, user.genres), weight: 0.4 })
  if (game.genres.length && genreAnchors.length)
    components.push({ value: anchorAggregate(genreAnchors.map((anchor) => facetSimilarity(game.genres, anchor.genres))), weight: 0.25 })
  if (game.developer.trim() && anchors.some((anchor) => anchor.developer.trim()))
    components.push({ value: sameStudio ? 1 : 0, weight: 0.05 })
  if (game.themes_status === "classified" && game.themes.length && user.themes.length)
    components.push({ value: preferenceCoverage(game.themes, user.themes), weight: 0.15 })
  if (game.themes_status === "classified" && game.themes.length && themeAnchors.length)
    components.push({ value: anchorAggregate(themeAnchors.map((anchor) => facetSimilarity(game.themes, anchor.themes))), weight: 0.15 })
  const weight = components.reduce((sum, item) => sum + item.weight, 0)
  const affinity = weight ? Math.round(100 * components.reduce((sum, item) => sum + item.value * item.weight, 0) / weight) : 0

  const anchorMatches = anchors.map((anchor) => {
    const genres = shared(game.genres, anchor.genres)
    const themes = game.themes_status === "classified" && anchor.themes_status === "classified"
      ? shared(game.themes, anchor.themes) : []
    const factors = []
    if (game.genres.length && anchor.genres.length)
      factors.push({ value: facetSimilarity(game.genres, anchor.genres), weight: 0.25 })
    if (game.themes_status === "classified" && anchor.themes_status === "classified" && game.themes.length && anchor.themes.length)
      factors.push({ value: facetSimilarity(game.themes, anchor.themes), weight: 0.15 })
    const total = factors.reduce((sum, item) => sum + item.weight, 0)
    return { id: anchor.id, title: anchor.title, genres, themes,
      similarity: total ? factors.reduce((sum, item) => sum + item.value * item.weight, 0) / total : 0 }
  }).filter((anchor) => anchor.genres.length || anchor.themes.length)
    .sort((a, b) => b.similarity - a.similarity || a.title.localeCompare(b.title, "pt-BR") || a.id.localeCompare(b.id))

  const reasons: string[] = []
  if (genreUser.length) reasons.push(`Gêneros do perfil: ${genreUser.join(", ")}.`)
  if (themeUser.length) reasons.push(`Temáticas do perfil: ${themeUser.join(", ")}.`)
  for (const anchor of anchorMatches.slice(0, 2))
    reasons.push(`Em comum com ${anchor.title}: ${unique([...anchor.genres, ...anchor.themes]).slice(0, 4).join(", ")}.`)
  if (sameStudio) reasons.push(`Mesmo estúdio de ${sameStudio.title}.`)
  return { affinity: Math.max(0, Math.min(100, affinity)), reasons, anchorMatches, preferredGenres: genreUser }
}
