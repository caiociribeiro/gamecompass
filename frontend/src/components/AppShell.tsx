import { useEffect, useRef, useState } from "react"
import { Link, Outlet, useLocation } from "react-router-dom"
import { useSession } from "../context/SessionContext"
import { useSound } from "../context/SoundContext"
import { Avatar } from "./PixelIcons"

const PHASE: [RegExp, string][] = [
  [/^\/app\/preferencias/, "FASE 1 · PERFIL"],
  [/^\/app\/ancoras/, "FASE 2 · ÂNCORAS"],
  [/^\/app\/hardware/, "FASE 3 · COMPUTADOR"],
  [/^\/app\/recomendacoes/, "FASE 4 · SUGESTÕES"],
  [/^\/app\/jogos/, "FICHA DO JOGO"],
  [/^\/app\/conta/, "SUA CONTA"],
  [/^\/app\/sobre/, "SOBRE"],
]

const MENU: [string, string, string][] = [
  ["/app", "★", "INÍCIO"],
  ["/app/preferencias", "1", "PERFIL"],
  ["/app/ancoras", "2", "ÂNCORAS"],
  ["/app/hardware", "3", "COMPUTADOR"],
  ["/app/recomendacoes", "4", "SUGESTÕES"],
]

function SideMenu({ pathname, onClose }: { pathname: string; onClose: () => void }) {
  const first = useRef<HTMLAnchorElement>(null)
  useEffect(() => {
    first.current?.focus()
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && onClose()
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [onClose])
  const current = (to: string) => (to === "/app" ? pathname === "/app" || pathname === "/app/" : pathname.startsWith(to))
  return (
    <>
      <div className="drawer-backdrop" onClick={onClose} aria-hidden="true" />
      <nav className="drawer" id="menu-lateral" aria-label="Menu das fases">
        <p className="drawer-title">MENU</p>
        <ul>
          {MENU.map(([to, mark, name], index) => (
            <li key={to}>
              <Link ref={index === 0 ? first : undefined} to={to} className={current(to) ? "cur" : ""} aria-current={current(to) ? "page" : undefined} onClick={onClose}>
                <b aria-hidden="true">{mark}</b>
                {name}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </>
  )
}

/** Cabeçalho fixo do app: botão de início, nome da fase, som, sobre e a conta (avatar e nome). */
export function AppShell() {
  const { user, saveError, dismissSaveError } = useSession()
  const { enabled, toggle } = useSound()
  const { pathname } = useLocation()
  const label = PHASE.find(([pattern]) => pattern.test(pathname))?.[1] ?? "INÍCIO"
  const [open, setOpen] = useState(false)
  const toggleRef = useRef<HTMLButtonElement>(null)
  const close = () => {
    setOpen(false)
    toggleRef.current?.focus()
  }
  useEffect(() => setOpen(false), [pathname])
  const atHome = pathname === "/app" || pathname === "/app/"
  return (
    <div className="shell">
      <i className="stars" aria-hidden="true" />
      <header className="app-top">
        <div className="top-side">
        <button ref={toggleRef} type="button" className="top-btn menu-btn" aria-expanded={open} aria-controls="menu-lateral" aria-label="Abrir menu das fases" onClick={() => setOpen((value) => !value)}>
          ☰
        </button>
        {atHome ? <span className="top-btn ghost" aria-hidden="true">GAMECOMPASS</span> : <Link className="top-btn" to="/app" aria-label="Voltar ao início">◀<span className="lbl"> INÍCIO</span></Link>}
        </div>
        <span className="grow" aria-live="polite">{label}</span>
        <div className="top-side end">
        <button type="button" className="top-btn ghost" aria-pressed={enabled} aria-label={`Som: ${enabled ? "ligado" : "desligado"}`} onClick={toggle}>
          ♪<span className="lbl"> SOM: {enabled ? "LIGADO" : "DESLIGADO"}</span>
        </button>
        <Link className="top-btn ghost" to="/app/sobre">SOBRE</Link>
        <Link className="me" to="/app/conta" aria-label="Sua conta">
          <Avatar name={user?.name} avatar={user?.avatar} />
          <span className="lbl">{user?.name}</span>
        </Link>
        </div>
      </header>
      {open && <SideMenu pathname={pathname} onClose={close} />}
      <main className="workspace-main">
        {saveError && (
          <p className="form-error" role="alert" style={{ padding: "10px 20px" }}>
            {saveError}{" "}
            <button type="button" className="btn small" onClick={dismissSaveError}>
              Fechar
            </button>
          </p>
        )}
        <Outlet />
      </main>
    </div>
  )
}
