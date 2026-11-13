import test from "node:test"
import assert from "node:assert/strict"
import { rankParts, searchRanked, surveyLabel } from "../src/lib/hardwareRank.ts"

const part = (name: string, score: number | null) => ({ id: name, name, vendor: name.split(" ")[0], performance_score: score, score_version: "manual_v1" })
const survey = { survey_month: "October 2026", items: [
  { steam_name: "NVIDIA GeForce RTX 3060", share_pct: 3.78, catalog_names: ["NVIDIA GeForce RTX 3060 12GB", "NVIDIA GeForce RTX 3060 8GB"] },
  { steam_name: "NVIDIA GeForce GTX 1650", share_pct: 2.44, catalog_names: ["NVIDIA GeForce GTX 1650 4GB"] },
] }

test("GPUs mais usadas na Steam vêm primeiro; o resto segue a pontuação do catálogo", () => {
  const ranked = rankParts([part("AMD Radeon RX 7900 XTX 24GB", 90), part("NVIDIA GeForce GTX 1650 4GB", 20),
    part("NVIDIA GeForce RTX 3060 8GB", 40), part("Intel HD Graphics 4000", 2)], survey)
  assert.deepEqual(ranked.map((option) => option.label), ["NVIDIA GeForce RTX 3060 8GB", "NVIDIA GeForce GTX 1650 4GB",
    "AMD Radeon RX 7900 XTX 24GB", "Intel HD Graphics 4000"])
  assert.equal(ranked[0].hint, "3,78% na Steam (out/2026)")
  assert.equal(ranked[2].hint, "AMD")  // sem dado da pesquisa, nada de porcentagem inventada
})

test("CPUs (sem dado de popularidade) seguem a pontuação; busca põe quem começa pelo termo na frente", () => {
  const cpus = rankParts([part("Intel Core i5-12400F", 50), part("AMD Ryzen 5 5600X", 55), part("AMD Athlon 3000G", 10)])
  assert.deepEqual(cpus.map((option) => option.label), ["AMD Ryzen 5 5600X", "Intel Core i5-12400F", "AMD Athlon 3000G"])
  assert.deepEqual(searchRanked(cpus, "ryzen 5").map((option) => option.label), ["AMD Ryzen 5 5600X"])
  assert.equal(searchRanked(cpus, "").length, 3)
  assert.equal(surveyLabel("March 2027"), "mar/2027")
})
