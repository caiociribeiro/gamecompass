import { Link } from "react-router-dom"
import { useCatalog } from "../context/CatalogContext"
import { useSession } from "../context/SessionContext"
import { profileSteps, type StepId } from "../lib/profile"

const SHORT: Record<StepId, string> = {
  prefs: "Preferências",
  anchors: "Jogos âncora",
  hardware: "Computador",
}

/** Mostra em que etapa do perfil a pessoa está e quais já foram concluídas. */
export function StepNav({ current }: { current: StepId }) {
  const { user } = useSession()
  const { games, hardware } = useCatalog()
  if (!user) return null
  const steps = profileSteps(user, games, hardware)
  return (
    <nav className="step-nav" aria-label="Etapas do seu perfil">
      <ol>
        {steps.map((step, index) => {
          const id = step.id as StepId
          return (
            <li key={step.id} className={step.done ? "done" : undefined}>
              <Link to={step.to} aria-current={id === current ? "step" : undefined}>
                <span className="step-mark" aria-hidden="true">
                  {step.done ? "✓" : index + 1}
                </span>
                <span>{SHORT[id]}</span>
                {step.done && <span className="sr-only"> (concluída)</span>}
              </Link>
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
