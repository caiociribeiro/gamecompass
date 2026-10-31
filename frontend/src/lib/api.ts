const BASE = (import.meta.env?.VITE_API_BASE_URL ?? "/api").replace(/\/$/, "")
const UNAVAILABLE = "Não foi possível acessar a API do GameCompass. Tente novamente em alguns instantes."

export async function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    signal,
    headers: { Accept: "application/json" },
  })
  const body = await response.json().catch(() => null)
  if (!response.ok)
    throw new Error(
      typeof body?.detail === "string"
        ? body.detail
        : response.status >= 500
          ? UNAVAILABLE
          : "A API não respondeu como esperado.",
    )
  if (!body) throw new Error("A API retornou uma resposta vazia.")
  return body as T
}
export function apiError(error: unknown) {
  return error instanceof TypeError
    ? UNAVAILABLE
    : error instanceof Error
      ? error.message
      : "Falha ao consultar os dados."
}
