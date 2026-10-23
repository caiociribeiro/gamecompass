import { Link, useParams } from "react-router-dom"
import { Cover } from "../components/GameCard"
import { useTitle } from "../components/PageHeader"
import { useSession } from "../context/SessionContext"
import { findGame } from "../data/catalog"
import { findCpu, findGpu } from "../data/hardware"
import { describeMatch, MIN_AFFINITY } from "../lib/recommend"

export function GameDetail() {
  const { id } = useParams()
  const { user } = useSession()
  const game = id ? findGame(id) : undefined
  useTitle(game?.title ?? "Jogo")
  if (!user) return null

  if (!game) {
    return (
      <div className="page narrow">
        <p className="empty">Esse jogo não está no catálogo de demonstração.</p>
        <Link to="/app/recomendacoes">Voltar à lista</Link>
      </div>
    )
  }

  const match = describeMatch(user, game)
  const cpu = user.hardware ? findCpu(user.hardware.cpuId) : undefined
  const gpu = user.hardware ? findGpu(user.hardware.gpuId) : undefined
  const inList = !match.anchor && match.compatible && match.affinity >= MIN_AFFINITY

  return (
    <div className="page">
      <Link className="back" to="/app/recomendacoes">
        Voltar à lista
      </Link>
      <article className="detail">
        <Cover game={game} className="cover-lg" />
        <div>
          <p className="eyebrow">
            {game.developer} · {game.year}
          </p>
          <h1>{game.title}</h1>
          <p className="lede">{game.summary}</p>
          <p className="tags">{[...game.genres, ...game.themes].join(" · ")}</p>
          <div className="affinity-row">
            <strong>{match.affinity}%</strong>
            <span>de afinidade com o perfil informado</span>
          </div>
          <div className="meter" aria-hidden="true">
            <span style={{ width: `${match.affinity}%` }} />
          </div>
          {match.anchor && <p className="banner">Este é um jogo âncora. Ele não aparece na lista de recomendações.</p>}
          {inList && <p className="banner ok">Entra na sua lista. O computador atende o mínimo deste jogo.</p>}
          {!match.anchor && user.hardware && !match.compatible && (
            <p className="banner warn">Este título não é uma recomendação. O computador não atende o mínimo.</p>
          )}
          {!user.hardware && <p className="banner">Informe o computador para saber se este jogo entra na lista.</p>}
        </div>
      </article>

      {match.reasons.length > 0 && (
        <section className="stack">
          <h2>Relação com o seu perfil</h2>
          <ul className="reasons">
            {match.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </section>
      )}

      <section className="stack">
        <h2>Compatibilidade</h2>
        {match.checks.length === 0 ? (
          <p className="empty">Ainda não há computador salvo para comparar.</p>
        ) : (
          <ul className="checks">
            {match.checks.map((check) => (
              <li key={check.label}>
                <span className={check.ok ? "pill ok" : "pill no"}>{check.ok ? "Atende" : "Não atende"}</span>
                <div>
                  <strong>{check.label}</strong>
                  <p>{check.detail}</p>
                </div>
              </li>
            ))}
          </ul>
        )}
        <details>
          <summary>Números desta demonstração</summary>
          <p>
            Mínimos ilustrativos do jogo: processador {game.minCpu}, placa {game.minGpu}, memória {game.minRam} GB.
            Sistemas: {game.systems.join(", ")}.
          </p>
          {cpu && gpu && (
            <p>
              Seu computador neste protótipo: processador {cpu.score}, placa {gpu.score}. A recomendação usa só essa
              comparação, sem estimativa subjetiva.
            </p>
          )}
        </details>
      </section>
    </div>
  )
}
