import { Navigate, useSearchParams } from "react-router-dom"
import type { ReactNode } from "react"
import { useSession } from "../context/SessionContext"

function safeNext(value: string | null) {
  if (value && value.startsWith("/app")) return value
  return "/app"
}

function Checking() {
  return (
    <p className="muted" role="status" style={{ padding: "2rem" }}>
      Verificando sua sessão…
    </p>
  )
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, status, signedOut } = useSession()
  if (status === "loading") return <Checking />
  if (!user) return <Navigate to={signedOut ? "/" : "/entrar"} replace />
  return children
}

export function GuestOnly({ children }: { children: ReactNode }) {
  const { user, status } = useSession()
  const [params] = useSearchParams()
  if (status === "loading") return <Checking />
  if (user) return <Navigate to={safeNext(params.get("next"))} replace />
  return children
}
