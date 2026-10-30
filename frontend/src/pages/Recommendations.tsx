import { useState } from "react"
import { Link } from "react-router-dom"
import { CatalogStatus } from "../components/CatalogStatus"
import { GameCard } from "../components/GameCard"
import { PageHeader } from "../components/PageHeader"
import { useCatalog } from "../context/CatalogContext"
import { useSession } from "../context/SessionContext"
import { profileSteps } from "../lib/profile"
import { buildRecommendations, profileReady } from "../lib/recommend"
import { fold } from "../lib/text"

export function Recommendations() {
  const { user } = useSession()
  const { games, hardware, discovered, discoverGames, gamesLoading } = useCatalog()
  const [query, setQuery] = useState("")
  if (!user) return null
  const ready = profileReady(user, games, hardware)
  const result = buildRecommendations(user, games, hardware)
  const matches = (title: string) => fold(title).includes(fold(query.trim()))
  return (
    <div className="page">
      <PageHeader
        eyebrow="Recomendações"
        title="Jogos para o seu perfil e para o seu PC"
        lede="A afinidade usa os dados da Steam. As verificações mostram o que já foi comparado e o que ainda precisa de revisão."
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
          <label className="stack-label search-wide">
            Filtrar a lista
            <input
              value={query}
              placeholder="Nome do jogo"
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
          <p className="hint">
            {result.items.length} com verificações atendidas · {result.pending.length} com validação pendente
            · {result.excluded.length} com restrições identificadas.
          </p>
          {result.items.length > 0 && (
            <section className="stack">
              <h2>Verificações atendidas</h2>
              <div className="card-grid">
                {result.items
                  .filter((match) => matches(match.game.title))
                  .map((match) => (
                    <GameCard
                      key={match.game.id}
                      game={match.game}
                      affinity={match.affinity}
                      href={`/app/jogos/${match.game.id}`}
                      note="Atende aos campos comparados"
                    />
                  ))}
              </div>
            </section>
          )}
          <section className="stack">
            <h2>Com afinidade, aguardando validação</h2>
            <p className="hint">
              Esses jogos combinam com seu perfil. Consulte as pendências antes de concluir se atendem ao
              computador.
            </p>
            {result.pending.filter((match) => matches(match.game.title)).length ? (
              <div className="card-grid">
                {result.pending
                  .filter((match) => matches(match.game.title))
                  .map((match) => (
                    <GameCard
                      key={match.game.id}
                      game={match.game}
                      affinity={match.affinity}
                      href={`/app/jogos/${match.game.id}`}
                      note="Validação pendente"
                    />
                  ))}
              </div>
            ) : (
              <p className="empty">Nenhum título pendente com esse filtro.</p>
            )}
          </section>
          {result.excluded.length > 0 && (
            <details className="excluded">
              <summary>Restrições identificadas</summary>
              <ul>
                {result.excluded
                  .filter((match) => matches(match.game.title))
                  .map((match) => (
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
                      <Link to={`/app/jogos/${match.game.id}`}>Ver o motivo</Link>
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
