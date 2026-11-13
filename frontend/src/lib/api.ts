const BASE = (import.meta.env?.VITE_API_BASE_URL ?? "/api").replace(/\/$/, "")
const UNAVAILABLE = "Não foi possível acessar a API do GameCompass. Tente novamente em alguns instantes."

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

type Method = "GET" | "POST" | "PATCH" | "PUT" | "DELETE"

async function apiRequest<T>(path: string, signal?: AbortSignal, payload?: unknown, method?: Method, keepalive = false): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    signal,
    // keepalive deixa o navegador terminar o envio mesmo depois que a aba fecha.
    ...(keepalive ? { keepalive: true } : {}),
    method: method ?? (payload === undefined ? "GET" : "POST"),
    // A sessão vai no cookie HttpOnly definido pela API; o JavaScript nunca lê o token.
    credentials: "same-origin",
    headers: { Accept: "application/json", ...(payload === undefined ? {} : { "Content-Type": "application/json" }) },
    ...(payload === undefined ? {} : { body: JSON.stringify(payload) }),
  })
  const body = await response.json().catch(() => null)
  if (!response.ok)
    throw new ApiError(
      typeof body?.detail === "string"
        ? body.detail
        : response.status >= 500
          ? UNAVAILABLE
          : "A API não respondeu como esperado.",
      response.status,
    )
  if (!body) throw new ApiError("A API retornou uma resposta vazia.", response.status)
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
export function apiPatch<T>(path: string, body: unknown, signal?: AbortSignal, options: { keepalive?: boolean } = {}): Promise<T> {
  return apiRequest<T>(path, signal, body, "PATCH", options.keepalive)
}
export function apiPut<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  return apiRequest<T>(path, signal, body, "PUT")
}
export function apiDelete<T>(path: string, signal?: AbortSignal): Promise<T> {
  return apiRequest<T>(path, signal, undefined, "DELETE")
}
