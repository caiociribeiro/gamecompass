import assert from "node:assert/strict"
import { test } from "node:test"
import { contentAffinity, facetSimilarity } from "./reference/affinity.ts"
import type { Game } from "../src/types.ts"

function game(id: string, genres: string[], themes: string[]): Game {
  return { id, title: `Fixture ${id}`, genres, themes, themes_status: "classified", developer: "",
    year: null, summary: "Fixture inventada", image_url: null, price_text: null, store_url: "https://example.org/fixture",
    platforms: { Windows: { native_support: true, minimum: null, recommended: null },
      macOS: { native_support: false, minimum: null, recommended: null },
      Linux: { native_support: false, minimum: null, recommended: null } },
    source: { source_url: "https://example.org/fixture", collected_at: "2026-10-31T00:00:00Z", response_sha256: "fixture" } }
}
const user = { genres: ["Puzzle"], themes: ["Ficção científica"] }
const anchors = [game("portal", ["Puzzle", "Aventura"], ["Ficção científica", "Exploração"]),
  game("gestão", ["Simulação"], ["Gestão"]), game("rpg", ["RPG"], ["Fantasia"])]
const candidate = game("candidato", ["Puzzle", "Aventura"], ["Ficção científica", "Exploração"])

test("uma âncora diferente não dilui a semelhança com outra ao ganhar categorias sem relação", () => {
  const before = contentAffinity(user, candidate, anchors)
  const different = structuredClone(anchors)
  different[1].genres.push("Estratégia", "RPG", "Tiro", "Plataforma")
  different[1].themes.push("Terror", "Competitivo")
  assert.equal(contentAffinity(user, candidate, different).affinity, before.affinity)
  assert.equal(before.anchorMatches[0].id, "portal")
  assert(before.reasons.some((reason) => reason.includes("Fixture portal") && reason.includes("Puzzle")))
})

test("ordem de seleção das âncoras não altera a afinidade ou a explicação", () => {
  assert.deepEqual(contentAffinity(user, candidate, anchors), contentAffinity(user, candidate, [...anchors].reverse()))
})

test("conjuntos normalizam acentos, espaços e duplicatas sem inflar a afinidade", () => {
  assert.equal(facetSimilarity([" Ação ", "ação", "RPG"], ["Acao", "rpg"]), 1)
  const original = structuredClone(candidate)
  candidate.genres.push("puzzle", " Puzzle ")
  try {
    const duplicated = { genres: ["Puzzle", "puzzle"], themes: ["Ficção científica", "ficcao cientifica"] }
    assert.equal(contentAffinity(duplicated, candidate, anchors).affinity, contentAffinity(user, original, anchors).affinity)
  } finally { candidate.genres = original.genres }
})

test("preferência específica melhora o candidato que possui essa classificação", () => {
  const platform = game("plataforma", ["Indie", "Plataforma"], ["Exploração"])
  const generic = game("genérico", ["Indie"], ["Exploração"])
  const profile = { genres: ["Plataforma"], themes: ["Exploração"] }
  assert(contentAffinity(profile, platform, [generic]).affinity > contentAffinity(profile, generic, [generic]).affinity)
})

test("classificação temática pendente não gera justificativa de temática", () => {
  const unknown = game("pendente", ["Puzzle"], ["Ficção científica"])
  unknown.themes_status = "pending"
  const result = contentAffinity(user, unknown, anchors)
  assert(!result.reasons.some((reason) => reason.includes("Ficção científica")))
  assert(result.anchorMatches.every((anchor) => anchor.themes.length === 0))
})

test("sem evidência a afinidade é zero e sem correspondência não há âncora inventada", () => {
  assert.equal(contentAffinity({ genres: [], themes: [] }, game("vazio", [], []), []).affinity, 0)
  const unrelated = contentAffinity(user, game("outro", ["Estratégia"], ["Terror"]), anchors)
  assert.equal(unrelated.affinity, 0)
  assert.deepEqual(unrelated.anchorMatches, [])
})

test("o gênero escolhido prevalece sobre uma coincidência temática genérica", () => {
  const reference = [game("rogue-a", ["Ação", "Indie", "Roguelike"], ["Fantasia"]),
    game("rogue-b", ["Aventura", "Indie", "Roguelike"], ["Fantasia"]),
    game("rogue-c", ["Estratégia", "Roguelike"], ["Fantasia"])]
  const profile = { genres: ["Roguelike"], themes: ["Fantasia"] }
  const rogue = contentAffinity(profile, game("rogue", ["Ação", "Indie", "Roguelike"], ["Ficção científica"]), reference)
  const fantasy = contentAffinity(profile, game("fantasy", ["Ação", "Indie"], ["Fantasia"]), reference)
  assert(rogue.affinity > fantasy.affinity)
  assert.deepEqual(rogue.preferredGenres, ["Roguelike"])
  assert.deepEqual(fantasy.preferredGenres, [])
})


test("o arredondamento em meio ponto preserva a soma sequencial das regras anteriores", () => {
  const args = [{"genres": ["RPG", "Aventura"], "themes": ["Fantasia", "Mundo aberto"]}, {"id": "2050650", "title": "Resident Evil 4", "genres": ["Aventura", "Ação", "Tiro"], "themes": ["Terror", "Narrativa"], "themes_status": "classified", "developer": "CAPCOM Co., Ltd."}, [{"id": "1091500", "title": "Cyberpunk 2077", "genres": ["RPG", "Tiro"], "themes": ["Ficção científica", "Mundo aberto", "Narrativa"], "themes_status": "classified", "developer": "CD PROJEKT RED"}, {"id": "292030", "title": "The Witcher 3: Wild Hunt — Remastered", "genres": ["RPG"], "themes": ["Fantasia", "Mundo aberto", "Narrativa"], "themes_status": "classified", "developer": "CD PROJEKT RED"}, {"id": "1245620", "title": "ELDEN RING", "genres": ["Ação", "RPG"], "themes": ["Fantasia", "Mundo aberto", "Exploração"], "themes_status": "classified", "developer": "FromSoftware, Inc."}]]
  assert.equal(contentAffinity(args[0] as any, args[1] as Game, args[2] as Game[]).affinity, 28)
})
