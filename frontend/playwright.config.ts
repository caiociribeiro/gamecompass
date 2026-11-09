import { defineConfig, devices } from "@playwright/test"

// Teste de ponta a ponta pelo navegador. Não sobe servidor: usa a pilha local já no ar
// (docker compose up -d neo4j api e, na pasta frontend, npm run dev).
// Para outro endereço: E2E_BASE_URL=http://127.0.0.1:4173 npm run e2e
export default defineConfig({
  testDir: "./e2e",
  timeout: 90_000,
  expect: { timeout: 10_000 },
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  outputDir: "./test-results",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://127.0.0.1:5173",
    locale: "pt-BR",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
})
