import { useState } from "react"
import { NavLink, Outlet, useNavigate } from "react-router-dom"
import { useSession } from "../context/SessionContext"
import { profileSteps } from "../lib/profile"
import { Logo } from "./Logo"

const LINKS = [
  { to: "/app", label: "Painel", end: true },
  { to: "/app/preferencias", label: "Preferências", end: false },
  { to: "/app/ancoras", label: "Jogos âncora", end: false },
  { to: "/app/hardware", label: "Hardware", end: false },
  { to: "/app/recomendacoes", label: "Recomendações", end: false },
  { to: "/app/conta", label: "Conta", end: false },
  { to: "/app/sobre", label: "Sobre", end: false },
]

export function AppShell() {
  const { user, logout } = useSession()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const steps = user ? profileSteps(user) : []

  function closeAnd(action?: () => void) {
    setOpen(false)
    action?.()
  }

  return (
    <div className={open ? "shell nav-open" : "shell"}>
      <button type="button" className="scrim" aria-label="Fechar menu" onClick={() => setOpen(false)} />
      <aside className="rail">
        <Logo />
        <nav className="rail-nav">
          {LINKS.map((link) => {
            const step = steps.find((item) => item.to === link.to)
            return (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                className={({ isActive }) => (isActive ? "rail-link active" : "rail-link")}
                onClick={() => setOpen(false)}
              >
                <span>{link.label}</span>
                {step && <i className={step.done ? "dot on" : "dot"} aria-hidden="true" />}
              </NavLink>
            )
          })}
        </nav>
        <div className="rail-foot">
          <p className="muted tiny">Protótipo local. Nada é enviado a um servidor.</p>
          <div className="who">
            <strong>{user?.name}</strong>
            <span>{user?.email}</span>
          </div>
          <button
            type="button"
            className="btn ghost small"
            onClick={() =>
              closeAnd(() => {
                logout()
                navigate("/entrar")
              })
            }
          >
            Sair
          </button>
        </div>
      </aside>
      <div className="workspace">
        <header className="mobile-bar">
          <button type="button" className="btn ghost small" onClick={() => setOpen(true)}>
            Menu
          </button>
          <Logo size={22} />
        </header>
        <main className="workspace-main">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
