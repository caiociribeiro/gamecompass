// Mede o custo de deixar telas paradas (RNF10): recálculos de estilo e de layout e tempo de CPU
// do navegador em 3 s, via Chrome DevTools Protocol (Performance.getMetrics).
//
// Uso (com a stack no ar; cria e apaga uma conta descartável no Neo4j):
//   node scripts/measure-idle.mjs [URL do frontend] [repetições] [arquivo de saída .json]
//   node scripts/measure-idle.mjs http://127.0.0.1:5173 3 medicao.json
//
// Telas: Landing, Início de conta nova e Sugestões (esta também conta os elementos da página).
import { chromium } from "@playwright/test"
import { execFileSync } from "node:child_process"
import { randomBytes } from "node:crypto"
import { writeFileSync } from "node:fs"
import os from "node:os"
import { createRequire } from "node:module"

const base = process.argv[2] ?? "http://127.0.0.1:5173"
const runs = Number(process.argv[3] ?? 3)
const output = process.argv[4]
const IDLE_MS = 3000
let browserVersion = ""

async function once() {
  const email = `medida-${randomBytes(5).toString("hex")}@exemplo.test`
  const password = randomBytes(18).toString("base64url")
  const browser = await chromium.launch()
  browserVersion = browser.version()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, locale: "pt-BR" })
  const cdp = await page.context().newCDPSession(page)
  await cdp.send("Performance.enable")
  const metric = async () => Object.fromEntries((await cdp.send("Performance.getMetrics")).metrics.map((m) => [m.name, m.value]))
  const idle = async () => {
    await page.waitForTimeout(1500) // deixa a tela assentar antes de medir
    const a = await metric()
    await page.waitForTimeout(IDLE_MS)
    const b = await metric()
    return {
      recalc_style: b.RecalcStyleCount - a.RecalcStyleCount,
      layout: b.LayoutCount - a.LayoutCount,
      task_ms: Math.round((b.TaskDuration - a.TaskDuration) * 1000),
      script_ms: Math.round((b.ScriptDuration - a.ScriptDuration) * 1000),
    }
  }
  const result = {}
  try {
    await page.goto(base + "/")
    result.landing = await idle()
    await page.goto(base + "/cadastro")
    await page.getByLabel("Nome").fill("Medição")
    await page.getByLabel("E-mail").fill(email)
    await page.getByLabel("Senha", { exact: true }).fill(password)
    await page.getByLabel("Confirmar senha").fill(password)
    await page.getByRole("button", { name: "Criar conta" }).click()
    await page.waitForURL(/\/app$/)
    result.inicio_conta_nova = await idle()
    await page.goto(base + "/app/preferencias")
    await page.getByRole("button", { name: "RPG", exact: true }).click()
    await page.getByRole("button", { name: "Fantasia", exact: true }).click()
    await page.goto(base + "/app/ancoras")
    for (const title of ["Cyberpunk 2077", "The Witcher 3", "ELDEN RING"]) {
      await page.locator(".anchor-suggestion", { hasText: title }).getByRole("button", { name: "Usar" }).first().click()
      await page.waitForTimeout(800)
    }
    await page.goto(base + "/app/hardware")
    await page.getByRole("combobox", { name: "Processador" }).fill("Ryzen 5 3600")
    await page.getByRole("option").filter({ has: page.getByText("AMD Ryzen 5 3600", { exact: true }) }).click()
    await page.getByRole("combobox", { name: "Placa de vídeo" }).fill("RTX 3060 12GB")
    await page.getByRole("option").filter({ has: page.getByText("NVIDIA GeForce RTX 3060 12GB", { exact: true }) }).click()
    await page.getByRole("button", { name: "16 GB", exact: true }).click()
    await page.getByRole("button", { name: "Windows", exact: true }).click()
    await page.getByRole("button", { name: /Windows 11/ }).click()
    await page.waitForTimeout(1500)
    await page.goto(base + "/app/recomendacoes")
    await page.getByRole("button", { name: "Buscar sugestões" }).click()
    await page.getByText(/Exibindo \d+ de \d+ resultados\./).waitFor({ timeout: 30000 })
    result.sugestoes = { ...(await idle()), elementos: await page.evaluate(() => document.querySelectorAll("*").length) }
  } finally {
    await browser.close()
    const query = `MATCH (u:User {email: "${email}"}) OPTIONAL MATCH (u)-[:HAS_SESSION]->(s:Session) DETACH DELETE u, s`
    try {
      execFileSync("docker", ["exec", "gamecompass-neo4j", "sh", "-c", `cypher-shell -u "\${NEO4J_AUTH%%/*}" -p "\${NEO4J_AUTH#*/}" '${query}'`], { stdio: "ignore", timeout: 60000 })
    } catch {
      console.error("Não foi possível apagar a conta de medição. Rode no Neo4j:", query)
    }
  }
  return result
}

const median = (values) => [...values].sort((a, b) => a - b)[Math.floor(values.length / 2)]
const samples = []
for (let index = 0; index < runs; index += 1) samples.push(await once())
const summary = {}
for (const screen of Object.keys(samples[0])) {
  summary[screen] = {}
  for (const key of Object.keys(samples[0][screen])) summary[screen][key] = median(samples.map((sample) => sample[screen][key]))
}
const report = {
  measured_at: new Date().toISOString(),
  url: base,
  runs,
  idle_ms: IDLE_MS,
  environment: {
    chromium: browserVersion, playwright: createRequire(import.meta.url)("@playwright/test/package.json").version,
    node: process.version, os: `${os.type()} ${os.release()}`, cpu: os.cpus()[0]?.model, cores: os.cpus().length,
    memory_gb: Math.round(os.totalmem() / 2 ** 30),
  },
  median: summary,
  samples,
}
console.log(JSON.stringify(report.median, null, 2))
if (output) writeFileSync(output, JSON.stringify(report, null, 2) + "\n")
