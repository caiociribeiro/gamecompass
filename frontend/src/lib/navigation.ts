const RETURN_PAGES = [
  { to: "/app/recomendacoes", label: "Voltar às recomendações" },
  { to: "/app/ancoras", label: "Voltar aos jogos âncora" },
  { to: "/app", label: "Voltar ao painel" },
]

export function gameReturnTarget(state: unknown) {
  if (state && typeof state === "object" && "returnTo" in state && typeof state.returnTo === "string") {
    const origin = state.returnTo
    const page = RETURN_PAGES.find(({ to }) => origin === to || origin.startsWith(`${to}?`))
    if (page) return {
      to: origin, label: page.label,
      historyBack: "returnKey" in state && typeof state.returnKey === "string" && Boolean(state.returnKey),
    }
  }
  return { ...RETURN_PAGES[0], historyBack: false }
}
