import { Link, useLocation, useSearchParams } from "react-router-dom"
import { CatalogStatus } from "../components/CatalogStatus"
import { GameCard } from "../components/GameCard"
import { PageHeader } from "../components/PageHeader"
import { useCatalog } from "../context/CatalogContext"
import { useSession } from "../context/SessionContext"
import { profileSteps } from "../lib/profile"
import { compatibilityLabel, profileReady } from "../lib/recommend"
import { fold } from "../lib/text"

export function Recommendations() {
  const { user } = useSession()
  const location = useLocation()
  const [params, setParams] = useSearchParams()
  const { games, hardware, discovered, discoverGames, gamesLoading, candidateSource, gameIssues, recommendations } = useCatalog()
  const query = params.get("q") ?? ""
  const status = params.get("status") ?? "all"
  const filter = ["recommended", "minimum", "pending", "incompatible"].includes(status) ? status : "all"
  function updateFilter(key: "q" | "status", value: string) {
    const next = new URLSearchParams(params)
    if (value && !(key === "status" && value === "all")) next.set(key, value)
    else next.delete(key)
    setParams(next, { replace: true })
  }
  if (!user) return null
  const ready = profileReady(user, games, hardware)
  const result = recommendations ?? { items: [], pending: [], excluded: [] }
  const matches = (title: string) => fold(title).includes(fold(query.trim()))
  const items = result.items.filter((match) => matches(match.game.title) && (filter === "all" || match.meets === filter))
  const pending = filter === "all" || filter === "pending" ? result.pending.filter((match) => matches(match.game.title)) : []
  const excluded = filter === "all" || filter === "incompatible" ? result.excluded.filter((match) => matches(match.game.title)) : []
  const visible = items.length + pending.length + excluded.length
  const total = result.items.length + result.pending.length + result.excluded.length
  return (
    <div className="page">
      <PageHeader
        eyebrow="Recomendações"
        title="Jogos para o seu perfil e para o seu PC"
        lede="A afinidade considera gêneros e temáticas dos seus jogos âncora. As verificações mostram o que já foi comparado e o que ainda precisa de revisão."
      />
      <CatalogStatus />
      <CatalogStatus scope="hardware" />
      {!ready && (
        <section className="stack">
          <p className="empty">Complete o perfil com os dados do catálogo carregado.</p>
          <ul className="plain-list">
            {profileSteps(user, games, hardware)
              .filter((step) => !step.done)
              .map((step) => (
                <li key={step.id}>
                  <Link to={step.to}>{step.label}</Link>
                  <span>{step.hint}</span>
                </li>
              ))}
          </ul>
        </section>
      )}
      {ready && (
        <div className="stack">
          <button type="button" className="btn" disabled={gamesLoading} onClick={() => void discoverGames()}>
            {gamesLoading ? "Buscando sugestões…" : discovered ? "Atualizar sugestões" : "Buscar sugestões"}
          </button>
          {!discovered && <p className="hint">As sugestões são consultadas quando você solicitar.</p>}
        </div>
      )}
      {ready && discovered && (
        <>
          <p className="hint">
            {candidateSource === "neo4j"
              ? "Sugestões encontradas pelas ligações de gêneros e temáticas no catálogo."
              : "Sugestões consultadas diretamente na Steam."}
          </p>
          {total > 0 && ![...result.items, ...result.pending, ...result.excluded].some((match) => match.preferredGenres?.length) && (
            <p className="hint">Não há outros jogos dos gêneros escolhidos entre os candidatos desta busca. A lista usa afinidade com suas âncoras e temáticas.</p>
          )}
          {gameIssues.filter((issue) => !issue.appid).map((issue) => (
            <p className="hint" key={issue.message}>{issue.message}</p>
          ))}
          <div className="recommendation-filters">
            <label className="stack-label">
              Filtrar a lista
              <input
                value={query}
                placeholder="Nome do jogo"
                onChange={(event) => updateFilter("q", event.target.value)}
              />
            </label>
            <label className="stack-label">
              Situação dos requisitos
              <select value={filter} onChange={(event) => updateFilter("status", event.target.value)}>
                <option value="all">Todos os resultados</option>
                <option value="recommended">Recomendados atendidos</option>
                <option value="minimum">Apenas mínimos atendidos</option>
                <option value="pending">Validação pendente</option>
                <option value="incompatible">Com restrições</option>
              </select>
            </label>
          </div>
          <p className="hint">
            {result.items.filter((match) => match.meets === "recommended").length} atendem aos recomendados
            {" · "}{result.items.filter((match) => match.meets === "minimum").length} atendem aos mínimos
            {" · "}{result.pending.length} com validação pendente
            · {result.excluded.length} com restrições identificadas.
          </p>
          <p className="hint" role="status">Exibindo {visible} de {total} resultados.</p>
          {visible === 0 && <p className="empty">{total > 0
            ? "Nenhum jogo encontrado com esses filtros."
            : "Nenhuma sugestão disponível para este conjunto de âncoras e preferências. Experimente outras escolhas."}</p>}
          {items.length > 0 && (
            <section className="stack">
              <h2>Requisitos atendidos</h2>
              <div className="card-grid">
                {items.map((match) => (
                    <GameCard
                      key={match.game.id}
                      game={match.game}
                      affinity={match.affinity}
                      href={`/app/jogos/${match.game.id}`}
                      note={compatibilityLabel(match)}
                      reason={match.reasons.find((reason) => reason.startsWith("Em comum com "))}
                    />
                  ))}
              </div>
            </section>
          )}
          {pending.length > 0 && (
          <section className="stack">
            <h2>Com afinidade, aguardando validação</h2>
            <p className="hint">
              Esses jogos combinam com seu perfil. Consulte as pendências antes de concluir se atendem ao
              computador.
            </p>
            <div className="card-grid">
                {pending.map((match) => (
                    <GameCard
                      key={match.game.id}
                      game={match.game}
                      affinity={match.affinity}
                      href={`/app/jogos/${match.game.id}`}
                      note={compatibilityLabel(match)}
                      reason={match.reasons.find((reason) => reason.startsWith("Em comum com "))}
                    />
                  ))}
            </div>
          </section>
          )}
          {excluded.length > 0 && (
            <details className="excluded" open={filter === "incompatible"}>
              <summary>Restrições identificadas</summary>
              <ul>
                {excluded.map((match) => (
                    <li key={match.game.id}>
                      <div>
                        <strong>{match.game.title}</strong>
                        <span>
                          {match.checks
                            .filter((check) => check.ok === false)
                            .map((check) => check.label)
                            .join(", ")}
                        </span>
                      </div>
                      <Link to={`/app/jogos/${match.game.id}`} state={{ returnTo: location.pathname + location.search, returnKey: location.key }}>Ver o motivo</Link>
                    </li>
                  ))}
              </ul>
            </details>
          )}
        </>
      )}
    </div>
  )
}
