import { Navigate, useSearchParams } from "react-router-dom"
import type { ReactNode } from "react"
import { useSession } from "../context/SessionContext"

function safeNext(value: string | null) {
  if (value && value.startsWith("/app")) return value
  return "/app"
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user } = useSession()
  if (!user) return <Navigate to="/entrar" replace />
  return children
}

export function GuestOnly({ children }: { children: ReactNode }) {
  const { user } = useSession()
  const [params] = useSearchParams()
  if (user) return <Navigate to={safeNext(params.get("next"))} replace />
  return children
}
