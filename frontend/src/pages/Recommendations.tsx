import { useState } from "react"
import { Link } from "react-router-dom"
import { GameCard } from "../components/GameCard"
import { PageHeader } from "../components/PageHeader"
import { useSession } from "../context/SessionContext"
import { profileSteps } from "../lib/profile"
import { buildRecommendations, profileReady } from "../lib/recommend"
import { fold } from "../lib/text"

export function Recommendations() {
  const { user } = useSession()
  const [query, setQuery] = useState("")
  if (!user) return null

  const ready = profileReady(user)
  const result = buildRecommendations(user)
  const q = fold(query.trim())
  const items = result.items.filter((match) => fold(match.game.title).includes(q))
  const excluded = result.excluded.filter((match) => fold(match.game.title).includes(q))

  return (
    <div className="page">
      <PageHeader
        eyebrow="Recomendações"
        title="Jogos para o seu perfil e para o seu PC"
        lede="A ordem segue a afinidade. Um jogo só aparece aqui se o computador atende processador, placa, memória e sistema."
      />

      {!ready && (
        <section className="stack">
          <p className="empty">A lista espera o cadastro completo.</p>
          <ul className="plain-list">
            {profileSteps(user)
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
        <>
          <label className="stack-label search-wide">
            Filtrar a lista
            <input value={query} placeholder="Nome do jogo" onChange={(event) => setQuery(event.target.value)} />
          </label>
          <p className="hint">
            {result.items.length} {result.items.length === 1 ? "jogo compatível" : "jogos compatíveis"}.
            {result.excluded.length > 0 &&
              ` ${result.excluded.length} com afinidade parecida ficaram de fora por hardware ou sistema.`}
          </p>
          {items.length === 0 ? (
            <p className="empty">Nenhum jogo compatível com esse filtro.</p>
          ) : (
            <div className="card-grid">
              {items.map((match) => (
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

          {excluded.length > 0 && (
            <details className="excluded">
              <summary>Fora do seu computador</summary>
              <p>Estes títulos não são recomendações. Eles só mostram o que a filtragem removeu.</p>
              <ul>
                {excluded.map((match) => (
                  <li key={match.game.id}>
                    <div>
                      <strong>{match.game.title}</strong>
                      <span>
                        {match.checks
                          .filter((check) => !check.ok)
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
