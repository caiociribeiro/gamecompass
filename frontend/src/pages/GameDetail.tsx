import { useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import { Cover } from "../components/GameCard"
import { useTitle } from "../components/PageHeader"
import { useCatalog } from "../context/CatalogContext"
import { useSession } from "../context/SessionContext"
import { OPERATING_SYSTEMS } from "../data/hardware"
import { apiError } from "../lib/api"
import { describeMatch } from "../lib/recommend"
import type { OperatingSystem } from "../types"

export function GameDetail() {
  const { id } = useParams()
  const { user } = useSession()
  const { games, hardware, loadGame } = useCatalog()
  const game = games.find((item) => item.id === id)
  const [error, setError] = useState<string | null>(null)
  const [revision, setRevision] = useState(0)
  const [system, setSystem] = useState<OperatingSystem>(user?.hardware?.os ?? "Windows")
  useTitle(game?.title ?? "Jogo")
  useEffect(() => {
    if (game || !id) return
    let active = true
    setError(null)
    loadGame(id).catch((error) => {
      if (active) setError(apiError(error))
    })
    return () => {
      active = false
    }
  }, [id, game, loadGame, revision])
  if (!user) return null
  if (!game)
    return (
      <div className="page narrow">
        <p className="empty" role={error ? "alert" : "status"}>
          {error || "Consultando os detalhes na Steam…"}
        </p>
        {error && (
          <button type="button" className="btn ghost small" onClick={() => setRevision((value) => value + 1)}>
            Tentar novamente
          </button>
        )}
        <Link to="/app">Voltar ao painel</Link>
      </div>
    )
  const match = describeMatch(user, game, games, hardware)
  const platform = game.platforms[system]
  return (
    <div className="page">
      <Link className="back" to="/app">
        Voltar ao painel
      </Link>
      <article className="detail">
        <Cover game={game} className="cover-lg" />
        <div>
          <p className="eyebrow">
            {game.developer} {game.year ? `· ${game.year}` : ""}
          </p>
          <h1>{game.title}</h1>
          <p className="lede">{game.summary}</p>
          <p className="tags">{game.genres.join(" · ")}</p>
          <p className="hint">{game.price_text}</p>
          <a href={game.store_url} target="_blank" rel="noreferrer">
            Abrir na Steam
          </a>
          <div className="affinity-row">
            <strong>{match.affinity}%</strong>
            <span>de afinidade com o perfil informado</span>
          </div>
          {match.anchor && <p className="banner">Este é um dos seus jogos âncora.</p>}
          {user.hardware && match.compatibility === "needs_review" && (
            <p className="banner warn">
              Há verificações pendentes. A compatibilidade completa ainda não foi confirmada.
            </p>
          )}
          {user.hardware && match.compatibility === "incompatible" && (
            <p className="banner warn">Há restrições identificadas para o computador informado.</p>
          )}
        </div>
      </article>
      <section className="stack">
        <h2>Requisitos publicados na Steam</h2>
        <label>
          Plataforma dos requisitos
          <select value={system} onChange={(event) => setSystem(event.target.value as OperatingSystem)}>
            {OPERATING_SYSTEMS.map((os) => (
              <option key={os}>{os}</option>
            ))}
          </select>
        </label>
        <p className="hint">
          {platform.native_support === true
            ? `Suporte nativo a ${system} informado pela Steam.`
            : platform.native_support === false
              ? `A Steam não informa suporte nativo a ${system}.`
              : "Suporte nativo não informado."}
        </p>
        <div className="requirements-grid">
          {(
            [
              ["minimum", "Mínimos"],
              ["recommended", "Recomendados"],
            ] as const
          ).map(([level, label]) => {
            const block = platform[level]
            return (
              <section className="requirements-panel" key={level}>
                <h3>{label}</h3>
                {block ? (
                  <>
                    <pre className="requirements-text">{block.text}</pre>
                    <p className="hint">
                      RAM:{" "}
                      {block.requirements.ram_gb === null ? "pendente" : `${block.requirements.ram_gb} GB`} ·
                      CPU: {block.requirements.cpu_score ?? "pendente"} · GPU:{" "}
                      {block.requirements.gpu_score ?? "pendente"}.
                    </p>
                    {block.issues.length > 0 && (
                      <details>
                        <summary>Pendências de identificação</summary>
                        <ul>
                          {block.issues.map((issue, i) => (
                            <li key={i}>{issue}</li>
                          ))}
                        </ul>
                      </details>
                    )}
                  </>
                ) : (
                  <p className="muted">Não informado pela Steam para esta plataforma.</p>
                )}
              </section>
            )
          })}
        </div>
        <p className="hint">
          Consulta: {new Date(game.source.collected_at).toLocaleString("pt-BR")} ·{" "}
          <a href={game.source.source_url} target="_blank" rel="noreferrer">
            Resposta da loja
          </a>
          .
        </p>
      </section>
      <section className="stack">
        <h2>Comparação com seu computador</h2>
        {!match.checks.length ? (
          <p className="empty">Cadastre seu computador para comparar.</p>
        ) : (
          <ul className="checks">
            {match.checks.map((check) => (
              <li key={check.label}>
                <span className={check.ok === true ? "pill ok" : check.ok === false ? "pill no" : "pill"}>
                  {check.ok === true ? "Atende" : check.ok === false ? "Não atende" : "Pendente"}
                </span>
                <div>
                  <strong>{check.label}</strong>
                  <p>{check.detail}</p>
                </div>
              </li>
            ))}
          </ul>
        )}
        <p className="hint">
          A análise usa requisitos da plataforma do seu computador. Versão do SO, VRAM, DirectX e outros
          requisitos específicos ainda exigem conferência.
        </p>
      </section>
      {match.reasons.length > 0 && (
        <section className="stack">
          <h2>Relação com seu perfil</h2>
          <ul className="reasons">
            {match.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
