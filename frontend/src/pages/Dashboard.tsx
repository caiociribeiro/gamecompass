import { Link } from "react-router-dom"
import { CatalogStatus } from "../components/CatalogStatus"
import { GameCard } from "../components/GameCard"
import { PageHeader } from "../components/PageHeader"
import { useCatalog } from "../context/CatalogContext"
import { useSession } from "../context/SessionContext"
import { hardwareSummary } from "../lib/hardware"
import { nextPendingStep, profileSteps } from "../lib/profile"
import { compatibilityLabel, profileReady } from "../lib/recommend"

export function Dashboard() {
  const { user } = useSession()
  const catalog = useCatalog()
  if (!user) return null
  const { games, hardware } = catalog
  const steps = profileSteps(user, games, hardware)
  const next = nextPendingStep(steps)
  const ready = profileReady(user, games, hardware)
  const result = catalog.recommendations ?? { items: [], pending: [], excluded: [] }
  const summary = hardwareSummary(user.hardware, hardware)
  return (
    <div className="page">
      <PageHeader
        eyebrow="Painel"
        title={`Olá, ${user.name}.`}
        lede={
          ready
            ? "Seu perfil está preenchido. Confira a afinidade e as pendências técnicas de cada título."
            : "Complete seu perfil e explore os jogos consultados na Steam."
        }
      />
      <section className="progress-card">
        <div>
          <p className="eyebrow">Cadastro</p>
          <h2>
            {steps.filter((step) => step.done).length} de {steps.length} prontos
          </h2>
        </div>
        <ol className="progress-list">
          {steps.map((step) => (
            <li key={step.id}>
              <div>
                <strong>{step.label}</strong>
                {step.id === next?.id && <span className="next-tag">Próxima etapa</span>}
                <p>{step.hint}</p>
              </div>
              <Link className={step.id === next?.id ? "btn small" : "btn ghost small"} to={step.to}>
                {step.done ? "Rever" : step.id === next?.id ? "Continuar" : "Preencher"}
              </Link>
            </li>
          ))}
        </ol>
        {!next && (
          <Link className="btn" to="/app/recomendacoes">
            Ver recomendações
          </Link>
        )}
      </section>
      {summary && (
        <section className="summary-line">
          <p className="eyebrow">Seu computador</p>
          <p>{summary.text}</p>
        </section>
      )}
      {ready && catalog.discovered && (
        <section className="stack">
          <div className="section-head inline">
            <h2>Jogos com afinidade</h2>
            <Link to="/app/recomendacoes">Ver análise completa</Link>
          </div>
          <div className="card-grid">
            {[...result.items, ...result.pending].slice(0, 3).map((match) => (
              <GameCard
                key={match.game.id}
                game={match.game}
                affinity={match.affinity}
                href={`/app/jogos/${match.game.id}`}
                note={compatibilityLabel(match)}
              />
            ))}
          </div>
          {!result.items.length && !result.pending.length && (
            <p className="empty">
              Nenhum título passou pelo filtro de afinidade e pelas verificações disponíveis.
            </p>
          )}
        </section>
      )}
      <section className="stack">
        <div className="section-head inline">
          <h2>Seus jogos âncora</h2>
          <Link to="/app/ancoras">Escolher jogos</Link>
        </div>
        <CatalogStatus />
        <p className="hint">
          {hardware.CPU.length} CPUs · {hardware.GPU.length} GPUs disponíveis para configurar seu computador.
        </p>
        {catalog.gameIssues.length > 0 && (
          <p className="hint">Alguns jogos salvos não foram disponibilizados pela Steam nesta consulta.</p>
        )}
        <div className="card-grid">
          {games
            .filter((game) => user.anchorIds.includes(game.id))
            .map((game) => (
              <GameCard
                key={game.id}
                game={game}
                href={`/app/jogos/${game.id}`}
                note={game.price_text ?? undefined}
              />
            ))}
        </div>
        {!user.anchorIds.length && (
          <p className="empty">Nenhum jogo selecionado. Pesquise pelo nome para escolher suas âncoras.</p>
        )}
        {ready && !catalog.discovered && (
          <Link to="/app/recomendacoes">Buscar sugestões para meu perfil</Link>
        )}
      </section>
    </div>
  )
}
