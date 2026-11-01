import { useEffect, useState, type MouseEvent } from "react"
import { Link, useLocation, useNavigate, useParams } from "react-router-dom"
import { Cover } from "../components/GameCard"
import { useTitle } from "../components/PageHeader"
import { RequirementsComparison } from "../components/RequirementsComparison"
import { useCatalog } from "../context/CatalogContext"
import { useSession } from "../context/SessionContext"
import { OPERATING_SYSTEMS } from "../data/hardware"
import { apiError } from "../lib/api"
import { gameReturnTarget } from "../lib/navigation"
import { compatibilityLabel } from "../lib/recommend"
import type { GameMatch, OperatingSystem } from "../types"

export function GameDetail() {
  const { id } = useParams()
  const back = gameReturnTarget(useLocation().state)
  const navigate = useNavigate()
  function goBack(event: MouseEvent<HTMLAnchorElement>) {
    if (back.historyBack && event.button === 0 && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey) {
      event.preventDefault()
      navigate(-1)
    }
  }
  const { user } = useSession()
  const { hardware, compareGame, recommendations, calculationKey } = useCatalog()
  const cached = recommendations && [...recommendations.items, ...recommendations.pending, ...recommendations.excluded].find((item) => item.game.id === id)
  const [computed, setComputed] = useState<{ key: string; match: GameMatch } | null>(null)
  const matchKey = JSON.stringify([id, calculationKey])
  const match = cached || (computed?.key === matchKey ? computed.match : null)
  const game = match?.game
  const [error, setError] = useState<string | null>(null)
  const [revision, setRevision] = useState(0)
  const [system, setSystem] = useState<OperatingSystem>(user?.hardware?.os ?? "Windows")
  useTitle(game?.title ?? "Jogo")
  useEffect(() => {
    if (cached || !id || !user) return
    const controller = new AbortController()
    setError(null)
    compareGame(id, controller.signal)
      .then((result) => { if (!controller.signal.aborted) setComputed({ key: matchKey, match: result }) })
      .catch((error) => { if (!controller.signal.aborted) setError(apiError(error)) })
    return () => controller.abort()
  }, [id, cached, user?.id, compareGame, matchKey, revision])
  if (!user) return null
  if (!game || !match)
    return (
      <div className="page narrow">
        <p className="empty" role={error ? "alert" : "status"}>
          {error || "Consultando os detalhes e a comparação…"}
        </p>
        {error && (
          <button type="button" className="btn ghost small" onClick={() => setRevision((value) => value + 1)}>
            Tentar novamente
          </button>
        )}
        <Link to={back.to} replace onClick={goBack}>{back.label}</Link>
      </div>
    )
  const platform = game.platforms[system]
  return (
    <div className="page">
      <Link className="back" to={back.to} replace onClick={goBack}>
        {back.label}
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
          {Boolean(game.genre_source?.editorial.length) && (
            <p className="hint">Categorias de jogabilidade classificadas pelo GameCompass: {game.genre_source!.editorial.join(", ")}.</p>
          )}
          <p className="hint">{game.price_text}</p>
          <a href={game.store_url} target="_blank" rel="noreferrer">
            Abrir na Steam
          </a>
          <div className="affinity-row">
            <strong>{match.affinity}%</strong>
            <span>de afinidade com o perfil informado</span>
          </div>
          {match.anchor && <p className="banner">Este é um dos seus jogos âncora.</p>}
          {user.hardware && (
            <p className={`banner ${match.compatible ? "ok" : "warn"}`}>
              {compatibilityLabel(match)}.
              {match.meets === "minimum" && match.assessments.recommended.compatibility === "needs_review" && (
                <> {match.assessments.recommended.available
                  ? "A validação dos recomendados está pendente."
                  : "A Steam não informou requisitos recomendados de hardware para esta plataforma."}</>
              )}
            </p>
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
                    {block.requirements_kind === "notes_only" && (
                      <p className="hint">A Steam publicou apenas observações neste nível, sem especificar CPU, GPU, RAM ou sistema operacional.</p>
                    )}
                    <pre className="requirements-text">{block.text}</pre>
                    {Boolean(block.curation?.length) && (
                      <details>
                        <summary>A comparação usa referências manuais para requisitos genéricos</summary>
                        <ul>
                          {block.curation!.map((reference) => (
                            <li key={reference.component_type}>
                              <strong>{reference.component_type === "CPU" ? "Processador" : "Placa de vídeo"}:</strong>{" "}
                              {reference.reference_models.join(" ou ")}. {reference.notes}
                            </li>
                          ))}
                        </ul>
                      </details>
                    )}
                    {block.requirements_kind !== "notes_only" && block.issues.length > 0 && (
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
        {user.hardware && <p className="hint">Requisitos da versão para {user.hardware.os}, o sistema salvo no seu perfil.</p>}
        {!match.checks.length ? (
          <p className="empty">Cadastre seu computador para comparar.</p>
        ) : (
          user.hardware && <RequirementsComparison match={match} profile={user.hardware} catalog={hardware} />
        )}
        <p className="hint">
          As sugestões são referências de desempenho. Confira soquete, placa-mãe, fonte e espaço físico
          antes de trocar uma peça. VRAM, DirectX e outros requisitos específicos exigem conferência.
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
