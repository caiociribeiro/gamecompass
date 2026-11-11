// Resumo curto de por que um jogo combina com o perfil, montado só com o que o motor já calculou.
import type { GameMatch } from "../types"

export const MAX_CHIPS = 3

export function explanationChips(match: Pick<GameMatch, "reasons" | "anchorMatches" | "preferredGenres">): string[] {
  const chips: string[] = []
  const genres = (match.preferredGenres ?? []).slice(0, 2)
  if (genres.length) chips.push(`Gênero: ${genres.join(", ")}`)
  for (const anchor of (match.anchorMatches ?? []).slice(0, 2)) chips.push(`Parecido com ${anchor.title}`)
  const studio = match.reasons.find((reason) => reason.startsWith("Mesmo estúdio de "))
  if (studio) chips.push(studio.replace(/\.$/, ""))
  return chips.slice(0, MAX_CHIPS)
}
