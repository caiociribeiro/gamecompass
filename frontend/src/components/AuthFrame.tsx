import { useState, type FormEvent, type ReactNode } from "react"
import { Link } from "react-router-dom"
import { Logo } from "./Logo"
import "../styles/public.css"

export function AuthFrame({
  title,
  lede,
  children,
}: {
  title: string
  lede: string
  children: ReactNode
}) {
  return (
    <div className="auth">
      <section className="auth-panel">
        <Link to="/" className="auth-back">
          ◀ INÍCIO
        </Link>
        <div className="logo-row">
          <Logo />
        </div>
        <h1>{title}</h1>
        <p className="lede">{lede}</p>
        {children}
      </section>
    </div>
  )
}

export function FormError({ message }: { message: string | null }) {
  if (!message) return null
  return (
    <p className="form-error" role="alert">
      {message}
    </p>
  )
}

export function useField() {
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  async function onSubmit(event: FormEvent, action: () => string | null | Promise<string | null>) {
    event.preventDefault()
    if (pending) return
    setPending(true)
    setError(null)
    try {
      setError(await action())
    } finally {
      setPending(false)
    }
  }
  return { error, pending, onSubmit }
}
