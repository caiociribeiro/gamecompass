import { Link } from "react-router-dom"
import { useCatalog } from "../context/CatalogContext"
import { useSession } from "../context/SessionContext"
import { phaseProgress, type PhaseId } from "../lib/phaseProgress"
import { profileSteps } from "../lib/profile"

const NODES: { id: PhaseId; label: string; to: string }[] = [
  { id: "prefs", label: "PERFIL", to: "/app/preferencias" },
  { id: "anchors", label: "ÂNCORAS", to: "/app/ancoras" },
  { id: "hardware", label: "COMPUTADOR", to: "/app/hardware" },
  { id: "recs", label: "SUGESTÕES", to: "/app/recomendacoes" },
]

/**
 * Trilha de fases com barra de nível. A barra enche de forma contínua conforme a fase atual é preenchida;
 * `live` deixa a página informar o progresso ainda não salvo (por exemplo, o computador em edição).
 */
export function StepNav({ current, live }: { current: PhaseId; live?: Partial<Record<"prefs" | "anchors" | "hardware", number>> }) {
  const { user } = useSession()
  const { games, hardware } = useCatalog()
  if (!user) return null
  const steps = profileSteps(user, games, hardware)
  const base = phaseProgress(user, games, hardware)
  const progress = { ...base, ...live }
  const sum = current === "recs" ? 3 : progress.prefs + progress.anchors + progress.hardware
  const percent = Math.min(100, (sum / 3) * 100)
  return (
    <nav className="phase-bar" aria-label="Etapas do seu perfil">
      <ol className="phase-track" style={{ listStyle: "none" }}>
        <li className="phase-rail" aria-hidden="true"><span className="phase-fill" style={{ width: `${percent}%` }} /></li>
        {NODES.map((node, index) => {
          const done = node.id === "recs" ? false : steps.find((step) => step.id === node.id)?.done === true
          const cls = node.id === current ? "phase-node cur" : done ? "phase-node done" : "phase-node"
          return (
            <li key={node.id} style={{ position: "absolute", top: 0, left: `calc((100% - 32px) * ${index / 3})` }}>
              <Link className={cls} to={node.to} aria-current={node.id === current ? "step" : undefined} style={{ position: "static", display: "block" }}>
                <b aria-hidden="true">{done ? "✓" : index + 1}</b>
                <span>{node.label}</span>
                {done && <span className="sr-only"> (concluída)</span>}
              </Link>
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
