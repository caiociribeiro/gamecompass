import { execFileSync } from "node:child_process"
import { randomBytes } from "node:crypto"
import { expect, test } from "@playwright/test"

// Roteiro de uma pessoa nova: cria a conta, preenche as três etapas do perfil seguindo só os
// botões da tela (sem usar o menu lateral) e chega às recomendações.
// Cria uma conta descartável e a remove no final pelo contêiner do Neo4j.

const CONTAINER = process.env.GAMECOMPASS_NEO4J_CONTAINER ?? "gamecompass-neo4j"
const email = `e2e-${randomBytes(5).toString("hex")}@exemplo.test`
const password = randomBytes(18).toString("base64url")

// Jogos do catálogo no Neo4j. As sugestões da Steam são simuladas para o teste não depender
// da internet; os dados de cada jogo continuam vindo do banco de verdade.
const ANCHORS = [
  { id: "1091500", title: "Cyberpunk 2077" },
  { id: "292030", title: "The Witcher 3: Wild Hunt" },
  { id: "1245620", title: "ELDEN RING" },
]

test.afterAll(() => {
  const query = `MATCH (u:User {email: "${email}"}) OPTIONAL MATCH (u)-[:HAS_SESSION]->(s:Session) DETACH DELETE u, s`
  const script = `cypher-shell -u "\${NEO4J_AUTH%%/*}" -p "\${NEO4J_AUTH#*/}" '${query}'`
  try {
    execFileSync("docker", ["exec", CONTAINER, "sh", "-c", script], { stdio: "ignore", timeout: 60_000 })
  } catch {
    console.log(`Não foi possível apagar a conta de teste. Rode no Neo4j Browser:\n  ${query}`)
  }
})

test("do cadastro às recomendações, só pelos botões da tela", async ({ page, request }) => {
  const health = await request.get("/api/hardware").catch(() => null)
  test.skip(!health?.ok(), "Suba a pilha local antes: docker compose up -d neo4j api e npm run dev.")

  await page.route("**/api/games/anchors", (route) =>
    route.fulfill({
      json: {
        items: ANCHORS.map((game) => ({ ...game, image_url: null })),
        issues: [],
        source: "steam",
        selection: "editorial",
      },
    }),
  )

  await test.step("cria a conta", async () => {
    await page.goto("/cadastro")
    await page.getByLabel("Nome").fill("Teste E2E")
    await page.getByLabel("E-mail").fill(email)
    await page.getByLabel("Senha", { exact: true }).fill(password)
    await page.getByLabel("Confirmar senha").fill(password)
    await page.getByRole("button", { name: "Criar conta" }).click()
    await expect(page).toHaveURL(/\/app$/)
  })

  await test.step("o painel mostra por onde começar", async () => {
    await expect(page.getByRole("heading", { name: "0 de 3 prontos" })).toBeVisible()
    await expect(page.getByText("Próxima etapa")).toBeVisible()
    await page.getByRole("link", { name: "Continuar", exact: true }).click()
    await expect(page).toHaveURL(/\/app\/preferencias$/)
  })

  await test.step("preferências: o rodapé só libera o avanço depois das escolhas", async () => {
    const footer = page.locator(".step-footer")
    await expect(footer).toContainText("Escolha pelo menos um gênero e uma temática para continuar.")
    await expect(footer.getByRole("button", { name: "Continuar para jogos âncora" })).toBeDisabled()
    await page.getByRole("button", { name: "RPG", exact: true }).click()
    await expect(footer).toContainText("Escolha pelo menos uma temática para continuar.")
    await page.getByRole("button", { name: "Fantasia", exact: true }).click()
    await expect(footer).toContainText("Etapa concluída")
    await expect(footer).toContainText("1 gênero e 1 temática escolhidos.")
    await expect(footer).toContainText("Salvo na sua conta.")
    await footer.getByRole("link", { name: "Continuar para jogos âncora" }).click()
    await expect(page).toHaveURL(/\/app\/ancoras$/)
  })

  await test.step("jogos âncora: três escolhas liberam a próxima etapa", async () => {
    const footer = page.locator(".step-footer")
    await expect(footer).toContainText("Escolha mais 3 jogos para continuar.")
    for (const [index, game] of ANCHORS.entries()) {
      await page
        .locator(".anchor-suggestion", { hasText: game.title })
        .getByRole("button", { name: "Usar" })
        .click()
      if (index < 2) await expect(footer).toContainText(`Escolha mais ${2 - index} ${index === 1 ? "jogo" : "jogos"} para continuar.`)
    }
    await expect(footer).toContainText("Os três jogos âncora estão escolhidos.")
    await footer.getByRole("link", { name: "Continuar para o computador" }).click()
    await expect(page).toHaveURL(/\/app\/hardware$/)
  })

  await test.step("computador: salva sozinho quando as peças estão completas", async () => {
    const footer = page.locator(".step-footer")
    await page.getByRole("combobox", { name: "Processador" }).fill("Ryzen 5 3600")
    await page.getByRole("option").filter({ has: page.getByText("AMD Ryzen 5 3600", { exact: true }) }).click()
    await page.getByRole("combobox", { name: "Placa de vídeo" }).fill("RTX 3060 12GB")
    await page.getByRole("option").filter({ has: page.getByText("NVIDIA GeForce RTX 3060 12GB", { exact: true }) }).click()
    await expect(footer.getByRole("button", { name: "Ver recomendações" })).toBeDisabled()
    await page.getByRole("button", { name: "16 GB", exact: true }).click()
    await page.getByRole("button", { name: "Windows", exact: true }).click()
    await page.getByRole("button", { name: /Windows 11/ }).click()
    await expect(footer).toContainText("Etapa concluída")
    await footer.getByRole("link", { name: "Ver recomendações" }).click()
    await expect(page).toHaveURL(/\/app\/recomendacoes$/)
  })

  await test.step("recomendações: o motor devolve jogos que não são as âncoras", async () => {
    await page.getByRole("button", { name: "Buscar sugestões" }).click()
    await expect(page.getByText(/Exibindo \d+ de \d+ resultados\./)).toBeVisible({ timeout: 30_000 })
    const links = await page.locator('a[href^="/app/jogos/"]').evaluateAll((items) =>
      items.map((item) => item.getAttribute("href") ?? ""),
    )
    expect(links.length).toBeGreaterThan(0)
    for (const game of ANCHORS) expect(links).not.toContain(`/app/jogos/${game.id}`)
  })

  const shells = page.locator(".game-card-shell")
  // Pelo título: depois de curtir um jogo, os outros cartões passam a citá-lo nos chips ("Parecido com ...").
  const cardOf = (title: string) => shells.filter({ has: page.locator("h3", { hasText: title }) })
  let disliked = ""
  let liked = ""

  await test.step("não curtir tira o jogo da lista na hora", async () => {
    const total = async () => Number((await page.getByText(/Exibindo \d+ de \d+ resultados\./).innerText()).match(/de (\d+)/)![1])
    const before = await total()
    expect(await shells.count()).toBeGreaterThan(1)
    disliked = (await shells.nth(0).locator("h3").innerText()).trim()
    liked = (await shells.nth(1).locator("h3").innerText()).trim()
    await shells.nth(0).getByRole("button", { name: "Não curtir este jogo" }).click()
    await expect(cardOf(disliked)).toHaveCount(0)
    // Com paginação, o próximo jogo ocupa a vaga; o que cai é o total da lista.
    await expect.poll(total).toBe(before - 1)
  })

  await test.step("curtir avisa que a afinidade muda no próximo cálculo e atualizar aplica", async () => {
    const card = cardOf(liked)
    await card.getByRole("button", { name: "Curtir este jogo", exact: true }).click()
    await expect(card.getByRole("button", { name: "Curtir este jogo", exact: true })).toHaveAttribute("aria-pressed", "true")
    const notice = page.getByRole("status").filter({ hasText: "Suas reações foram salvas" })
    await expect(notice).toBeVisible()
    await notice.getByRole("button", { name: "Atualizar sugestões" }).click()
    await expect(notice).toHaveCount(0, { timeout: 30_000 })
    await expect(cardOf(disliked)).toHaveCount(0)
    await expect(cardOf(liked).getByRole("button", { name: "Curtir este jogo", exact: true })).toHaveAttribute("aria-pressed", "true")
  })

  let viewed = ""
  await test.step("abrir a ficha de um jogo registra a visualização", async () => {
    const other = shells.filter({ hasNot: page.locator("h3", { hasText: liked }) }).first()
    viewed = (await other.locator("h3").innerText()).trim()
    await other.locator("a.game-card").click()
    await expect(page).toHaveURL(/\/app\/jogos\//)
    await expect(page.getByRole("heading", { level: 1 })).toContainText(viewed)
  })

  await test.step("a conta lista as reações e permite limpar o histórico", async () => {
    await page.goto("/app/conta")
    const history = page.locator("section", { has: page.getByRole("heading", { name: "Histórico de jogos" }) })
    await expect(history).toContainText(liked)
    await expect(history).toContainText(disliked)
    const onlyViewed = history.locator("ul", { has: page.locator(".history-eye") })
    await expect(onlyViewed).toContainText(viewed)
    await expect(onlyViewed).toContainText("aberto 1 vez")
    await history.getByRole("button", { name: "Limpar histórico de jogos" }).click()
    await history.getByRole("button", { name: "Confirmar limpeza do histórico" }).click()
    await expect(history).toContainText("Histórico removido")
    await expect(history).not.toContainText(liked)
  })

  await test.step("o painel termina com o perfil completo", async () => {
    await page.goto("/app")
    await expect(page.getByRole("heading", { name: "3 de 3 prontos" })).toBeVisible()
    await expect(page.getByRole("link", { name: "Ver recomendações" })).toBeVisible()
  })

  await test.step("sair da conta leva à Landing, não ao login", async () => {
    await page.goto("/app/conta")
    await page.getByRole("button", { name: "Sair da conta" }).click()
    await expect(page).toHaveURL(/\/$/)
    await expect(page.getByRole("heading", { name: /Jogos do seu gosto/ })).toBeVisible()
  })
})
