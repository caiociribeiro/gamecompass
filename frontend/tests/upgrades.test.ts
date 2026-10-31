import assert from "node:assert/strict"
import { test } from "node:test"
import { replacementOptions } from "../src/lib/upgrades.ts"
import type { Part } from "../src/types.ts"

const part = (id: string, score: number | null, vendor: string, name = id): Part =>
  ({ id, name, performance_score: score, vendor, score_version: "manual_v1" })
const current = part("atual", 10, "NVIDIA")

test("modelos identificados no requisito têm prioridade sobre empate por nome do catálogo", () => {
  const parts = [part("AMD não citada 4GB", 50, "AMD"), part("NVIDIA publicada 6GB", 100, "NVIDIA"),
    part("Intel publicada 6GB", 50, "Intel")]
  const options = replacementOptions(parts, current, 50, "manual_v1", ["NVIDIA publicada 6GB", "Intel publicada 6GB"])
  assert.equal(options[0].id, "Intel publicada 6GB")
  assert.equal(options[1].id, "NVIDIA publicada 6GB")
  assert(options.every((option) => option.performance_score! >= 50))
})

test("opções de fabricantes diferentes evitam listar vários nomes do mesmo grupo", () => {
  const parts = [part("AMD A", 50, "AMD"), part("AMD B", 50, "AMD"),
    part("NVIDIA A", 50, "NVIDIA"), part("Intel A", 100, "Intel")]
  const options = replacementOptions(parts, current, 50, "manual_v1")
  assert.equal(options.length, 3)
  assert.equal(options[0].vendor, "NVIDIA")
  assert.equal(new Set(options.map((option) => option.vendor)).size, 3)
  assert.deepEqual(replacementOptions([...parts].reverse(), current, 50, "manual_v1"), options)
})

test("referências não aprovam opções ausentes, pendentes ou de versão diferente", () => {
  const options = replacementOptions([part("pendente", null, "AMD"), part("infinito", Infinity, "Intel"),
    { ...part("versão", 100, "Intel"), score_version: "manual_v2" }, part("fraca", 20, "AMD")],
    current, 50, "manual_v1", ["pendente", "infinito", "versão", "fraca"])
  assert.deepEqual(options, [])
})

test("ATI e AMD são tratadas como o mesmo fabricante na diversidade de opções", () => {
  const options = replacementOptions([part("ATI Radeon fixture", 50, "Outro"), part("AMD fixture", 50, "AMD")],
    current, 50, "manual_v1")
  assert.equal(options.length, 1)
})
