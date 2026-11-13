import { fold } from "./text.ts"
import type { Part } from "../types"

export type GpuSurvey = { survey_month: string; items: { steam_name: string; share_pct: number; catalog_names: string[] }[] }
export type RankedOption = { id: string; label: string; hint: string; share?: number }

const MONTHS: Record<string, string> = {
  January: "jan", February: "fev", March: "mar", April: "abr", May: "mai", June: "jun",
  July: "jul", August: "ago", September: "set", October: "out", November: "nov", December: "dez",
}

/** "October 2026" -> "out/2026". */
export function surveyLabel(month: string) {
  const [name, year] = month.split(" ")
  return `${MONTHS[name] ?? name}/${year}`
}

/**
 * Ordena as peças para a lista de escolha. GPUs: participação na pesquisa da Steam (maior primeiro);
 * sem dado da pesquisa, as mais potentes do catálogo. CPUs: a pesquisa não publica modelos de
 * processador, então a ordem é só pela pontuação do catálogo.
 */
export function rankParts(parts: Part[], survey?: GpuSurvey): RankedOption[] {
  const share = new Map<string, number>()
  for (const item of survey?.items ?? []) for (const name of item.catalog_names) share.set(name, item.share_pct)
  const label = survey ? surveyLabel(survey.survey_month) : ""
  return [...parts]
    .sort((a, b) => (share.get(b.name) ?? -1) - (share.get(a.name) ?? -1)
      || (b.performance_score ?? -1) - (a.performance_score ?? -1)
      || a.name.localeCompare(b.name))
    .map((part) => {
      const pct = share.get(part.name)
      return pct === undefined
        ? { id: part.id, label: part.name, hint: part.vendor }
        : { id: part.id, label: part.name, hint: `${pct.toLocaleString("pt-BR")}% na Steam (${label})`, share: pct }
    })
}

/** Filtra mantendo a ordem de popularidade, mas com quem começa pelo termo digitado na frente. */
export function searchRanked<T extends { label: string }>(options: T[], query: string, limit = 8): T[] {
  const needle = fold(query.trim())
  if (!needle) return options.slice(0, limit)
  const words = needle.split(/\s+/)
  const hits = options.filter((option) => { const text = fold(option.label); return words.every((word) => text.includes(word)) })
  const starts = (option: T) => fold(option.label).split(/\s+/).some((word) => word.startsWith(words[0]))
  return [...hits.filter(starts), ...hits.filter((option) => !starts(option))].slice(0, limit)
}
