import assert from "node:assert/strict"
import { test } from "node:test"
import { explanationChips } from "../src/lib/explain.ts"

const anchors = [
  { id: "1", title: "Elden Ring", similarity: 0.8, genres: ["RPG"], themes: [] },
  { id: "2", title: "The Witcher 3", similarity: 0.7, genres: ["RPG"], themes: [] },
  { id: "3", title: "Cyberpunk 2077", similarity: 0.6, genres: ["RPG"], themes: [] },
]

test("os chips resumem gênero, âncoras parecidas e estúdio, no máximo três", () => {
  const chips = explanationChips({ preferredGenres: ["RPG", "Ação", "Aventura"], anchorMatches: anchors,
    reasons: ["Mesmo estúdio de Elden Ring."] })
  assert.deepEqual(chips, ["Gênero: RPG, Ação", "Parecido com Elden Ring", "Parecido com The Witcher 3"])
})

test("sem gênero em comum o estúdio aparece e o ponto final é removido", () => {
  const chips = explanationChips({ preferredGenres: [], anchorMatches: [], reasons: ["Mesmo estúdio de Elden Ring."] })
  assert.deepEqual(chips, ["Mesmo estúdio de Elden Ring"])
})

test("sem nenhum dado do motor não há chips", () => {
  assert.deepEqual(explanationChips({ reasons: [] }), [])
})
