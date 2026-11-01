const BASE = (import.meta.env?.VITE_API_BASE_URL ?? "/api").replace(/\/$/, "")
const UNAVAILABLE = "Não foi possível acessar a API do GameCompass. Tente novamente em alguns instantes."

async function apiRequest<T>(path: string, signal?: AbortSignal, payload?: unknown): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    signal,
    method: payload === undefined ? "GET" : "POST",
    headers: { Accept: "application/json", ...(payload === undefined ? {} : { "Content-Type": "application/json" }) },
    ...(payload === undefined ? {} : { body: JSON.stringify(payload) }),
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

export function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  return apiRequest<T>(path, signal)
}
export function apiPost<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  return apiRequest<T>(path, signal, body)
}
