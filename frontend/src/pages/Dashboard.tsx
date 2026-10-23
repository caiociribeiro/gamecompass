import { Link } from "react-router-dom"
import { GameCard } from "../components/GameCard"
import { PageHeader } from "../components/PageHeader"
import { useSession } from "../context/SessionContext"
import { hardwareSummary } from "../data/hardware"
import { profileSteps } from "../lib/profile"
import { buildRecommendations, profileReady } from "../lib/recommend"

export function Dashboard() {
  const { user } = useSession()
  if (!user) return null
  const steps = profileSteps(user)
  const ready = profileReady(user)
  const result = buildRecommendations(user)
  const hardware = hardwareSummary(user.hardware)
  const done = steps.filter((step) => step.done).length

  return (
    <div className="page">
      <PageHeader
        eyebrow="Painel"
        title={`Olá, ${user.name}.`}
        lede={
          ready
            ? "Seu perfil está completo. A lista abaixo já considera gosto e computador."
            : "Faltam dados para montar a primeira lista. Complete os passos na ordem que fizer sentido."
        }
      />

      <section className="progress-card">
        <div>
          <p className="eyebrow">Cadastro</p>
          <h2>
            {done} de {steps.length} prontos
          </h2>
        </div>
        <ol className="progress-list">
          {steps.map((step) => (
            <li key={step.id}>
              <div>
                <strong>{step.label}</strong>
                <p>{step.hint}</p>
              </div>
              <Link className={step.done ? "btn ghost small" : "btn small"} to={step.to}>
                {step.done ? "Rever" : "Preencher"}
              </Link>
            </li>
          ))}
        </ol>
      </section>

      {hardware && (
        <section className="summary-line">
          <p className="eyebrow">Seu computador</p>
          <p>{hardware.text}</p>
        </section>
      )}

      {ready && (
        <section>
          <div className="section-head inline">
            <h2>Primeiras sugestões</h2>
            <Link to="/app/recomendacoes">Ver a lista completa</Link>
          </div>
          {result.items.length === 0 ? (
            <p className="empty">Nenhum jogo compatível ficou acima do corte de afinidade com este perfil.</p>
          ) : (
            <div className="card-grid">
              {result.items.slice(0, 3).map((match) => (
                <GameCard
                  key={match.game.id}
                  game={match.game}
                  affinity={match.affinity}
                  href={`/app/jogos/${match.game.id}`}
                  note="Roda no seu PC"
                />
              ))}
            </div>
          )}
          {result.excluded.length > 0 && (
            <p className="hint">
              {result.excluded.length} {result.excluded.length === 1 ? "título parecido ficou" : "títulos parecidos ficaram"} de
              fora porque o computador não atende o mínimo.
            </p>
          )}
        </section>
      )}
    </div>
  )
}
