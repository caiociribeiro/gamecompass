import { useState, type FormEvent, type ReactNode } from "react"
import { Link } from "react-router-dom"
import { Logo } from "./Logo"

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
        <Link to="/" className="quiet-link">
          <Logo />
        </Link>
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
  function onSubmit(event: FormEvent, action: () => string | null) {
    event.preventDefault()
    setError(action())
  }
  return { error, onSubmit }
}
