import type { Part } from "../types"

const positive = (value: number | null): value is number =>
  typeof value === "number" && Number.isFinite(value) && value > 0
const key = (name: string) => name.trim().replace(/\s+/g, " ").toLowerCase()
const brand = (part: Part) => /^ATI\s/i.test(part.name) ? "AMD" : part.vendor

export function replacementOptions(
  parts: Part[], current: Part, required: number, scoreVersion: string, references: string[] = [],
): Part[] {
  if (!positive(required) || !scoreVersion || !positive(current.performance_score) ||
    current.score_version !== scoreVersion || current.performance_score >= required) return []
  const eligible = parts.filter((part) => part.id !== current.id && part.score_version === scoreVersion &&
    positive(part.performance_score) && part.performance_score >= required)
  const names = new Set(references.map(key))
  const compare = (a: Part, b: Part) => a.performance_score! - b.performance_score! ||
    Number(brand(b) === brand(current)) - Number(brand(a) === brand(current)) ||
    a.name.localeCompare(b.name, "pt-BR") || a.id.localeCompare(b.id)
  // Prioriza modelos identificados no requisito, preservando as variantes publicadas.
  const named = eligible.filter((part) => names.has(key(part.name))).sort(compare)
  const ordered = [...named, ...eligible.filter((part) => !names.has(key(part.name))).sort(compare)]
  const options: Part[] = []
  const brands = new Set<string>()
  for (const part of ordered) {
    if (!brands.has(brand(part))) {
      options.push(part)
      brands.add(brand(part))
      if (options.length === 3) break
    }
  }
  return options
}
