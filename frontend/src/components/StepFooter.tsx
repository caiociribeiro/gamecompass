import { Link } from "react-router-dom"
import { useCatalog } from "../context/CatalogContext"
import { useSession } from "../context/SessionContext"
import { stepGuide, type StepId } from "../lib/profile"

/**
 * Fecha uma etapa do perfil: diz o que já está feito (ou o que falta), confirma que o
 * salvamento aconteceu e oferece o botão para a próxima etapa.
 * `pending` bloqueia o avanço com um aviso, por exemplo quando há alterações ainda não salvas.
 */
export function StepFooter({ id, pending }: { id: StepId; pending?: string }) {
  const { user, saving, saveError } = useSession()
  const { games, hardware } = useCatalog()
  if (!user) return null
  const guide = stepGuide(user, games, hardware, id)
  const ready = guide.done && !pending
  const message = pending ?? (guide.done ? guide.status : guide.missing)
  return (
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
        <Link className="btn" to={guide.next.to}>
          {guide.next.label}
        </Link>
      ) : (
        <button className="btn" type="button" disabled>
          {guide.next.label}
        </button>
      )}
    </footer>
  )
}
