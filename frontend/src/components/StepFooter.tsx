import { useEffect, useRef, useState, type MouseEvent } from "react"
import { Link, useNavigate } from "react-router-dom"
import { useCatalog } from "../context/CatalogContext"
import { useSession } from "../context/SessionContext"
import { stepGuide, type StepId } from "../lib/profile"
import { PhaseCleared } from "./PhaseOverlay"

const TITLE: Record<StepId, string> = {
  prefs: "FASE 1 CONCLUÍDA!",
  anchors: "FASE 2 CONCLUÍDA!",
  hardware: "FASE 3 CONCLUÍDA!",
}
const LOADING: Record<StepId, string> = {
  prefs: "CARREGANDO FASE 2...",
  anchors: "CARREGANDO FASE 3...",
  hardware: "CARREGANDO SUGESTÕES...",
}

/**
 * Barra fixa no rodapé: diz o que falta (ou que a fase terminou), confirma o salvamento e oferece o
 * botão de avançar, que acende só quando a fase está completa. `pending` bloqueia o avanço com um aviso.
 */
export function StepFooter({ id, pending }: { id: StepId; pending?: string }) {
  const { user, saving, saveError } = useSession()
  const { games, hardware } = useCatalog()
  const navigate = useNavigate()
  const [clearing, setClearing] = useState(false)
  const timer = useRef<number | null>(null)
  useEffect(() => () => { if (timer.current) window.clearTimeout(timer.current) }, [])
  if (!user) return null
  const guide = stepGuide(user, games, hardware, id)
  const ready = guide.done && !pending
  const message = pending ?? (guide.done ? guide.status : guide.missing)

  function advance(event: MouseEvent<HTMLAnchorElement>) {
    if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return
    event.preventDefault()
    if (clearing) return
    setClearing(true)
    timer.current = window.setTimeout(() => navigate(guide.next.to), 1600)
  }

  return (
    <>
      <footer className={ready ? "step-footer ready" : "step-footer"}>
        <div className="step-status" role="status" aria-live="polite">
          <strong>{ready ? "Etapa concluída" : "Para continuar"}</strong>
          <span>{message}</span>
          {saveError ? (
            <small className="save-state">Não foi possível salvar. Veja o aviso no topo da página.</small>
          ) : saving ? (
            <small className="save-state">Salvando…</small>
          ) : ready ? (
            <small className="save-state">Salvo na sua conta.</small>
          ) : null}
        </div>
        {ready ? (
          <Link className="btn" to={guide.next.to} onClick={advance}>
            <span className="ar" aria-hidden="true">▶</span> {guide.next.label}
          </Link>
        ) : (
          <button className="btn" type="button" disabled>
            {guide.next.label}
          </button>
        )}
      </footer>
      {clearing && <PhaseCleared title={TITLE[id]} subtitle={LOADING[id]} />}
    </>
  )
}
