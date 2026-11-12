import { useEffect, useRef, useState, type KeyboardEvent, type MouseEvent } from "react"
import { Link, useLocation, useNavigate, useParams } from "react-router-dom"
import { Cover } from "../components/GameCard"
import { useTitle } from "../components/PageHeader"
import { ReactionButtons } from "../components/ReactionButtons"
import { RequirementsComparison } from "../components/RequirementsComparison"
import { useCatalog } from "../context/CatalogContext"
import { useSession } from "../context/SessionContext"
import { OPERATING_SYSTEMS } from "../data/hardware"
import { apiError } from "../lib/api"
import { gameReturnTarget } from "../lib/navigation"
import { compatibilityLabel } from "../lib/recommend"
import type { GameMatch, OperatingSystem } from "../types"
import "../styles/results.css"

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
  const { hardware, compareGame, recommendations, calculationKey, reactions, reactionsStale, reactToGame, recordView } = useCatalog()
  const cached = recommendations && [...recommendations.items, ...recommendations.pending, ...recommendations.excluded].find((item) => item.game.id === id)
  const [computed, setComputed] = useState<{ key: string; match: GameMatch } | null>(null)
  const matchKey = JSON.stringify([id, calculationKey])
  const match = cached || (computed?.key === matchKey ? computed.match : null)
  const game = match?.game
  const [error, setError] = useState<string | null>(null)
  const [revision, setRevision] = useState(0)
  const [system, setSystem] = useState<OperatingSystem>(user?.hardware?.os ?? "Windows")
  const [tab, setTab] = useState<"comparison" | "steam" | "why">("comparison")
  useTitle(game?.title ?? "Jogo")
  const [reactionError, setReactionError] = useState<string | null>(null)
  const viewed = useRef<string | null>(null)
  useEffect(() => {
    // Uma visualização por abertura da página, mesmo com a renderização dupla do modo de desenvolvimento.
    if (!id || !user || viewed.current === id) return
    viewed.current = id
    recordView(id)
  }, [id, user?.id, recordView])
  const reaction = id && reactions[id] !== undefined ? reactions[id] : match?.reaction
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
  const tabs = [
    { id: "comparison", label: "COMPARAÇÃO COM SEU PC" },
    { id: "steam", label: "REQUISITOS NA STEAM" },
    ...(match.reasons.length > 0 ? [{ id: "why", label: "POR QUE COMBINA" }] : []),
  ] as { id: typeof tab; label: string }[]
  const badge = match.meets === "recommended" ? { label: "RECOMENDADO", tone: "ok" as const }
    : match.meets === "minimum" ? { label: "MÍNIMO", tone: "min" as const } : { label: "PENDENTE", tone: "pending" as const }
  function onTabKey(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    const step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0
    if (!step) return
    event.preventDefault()
    const next = tabs[(index + step + tabs.length) % tabs.length]
    setTab(next.id)
    document.getElementById(`tab-${next.id}`)?.focus()
  }
  return (
    <div className="page">
      <Link className="back" to={back.to} replace onClick={goBack}>
        {back.label}
      </Link>
      <article className="detail">
        <div className="poster">
          <Cover game={game} className="cover-lg" badge={user.hardware ? badge : undefined} />
        </div>
        <div className="detail-main">
          <p className="eyebrow">
            {game.developer} {game.year ? `· ${game.year}` : ""}
          </p>
          <h1>{game.title}</h1>
          <p className="tags genre-tags">{game.genres.map((genre) => <span key={genre}>{genre}</span>)}</p>
          <p className="lede">{game.summary}</p>
          {Boolean(game.genre_source?.editorial.length) && (
            <p className="hint">Categorias de jogabilidade classificadas pelo GameCompass: {game.genre_source!.editorial.join(", ")}.</p>
          )}
          <p className="hint">{game.price_text}</p>
          <a className="btn" href={game.store_url} target="_blank" rel="noreferrer">
            Abrir na Steam <span aria-hidden="true">↗</span>
          </a>
          <div className="affinity-box">
            <div className="affinity-row">
              <div className="meter" aria-hidden="true"><span style={{ width: `${match.affinity}%` }} /></div>
              <strong>{match.affinity}%</strong>
            </div>
            <small>de afinidade com o perfil informado</small>
          </div>
          {match.anchor && <p className="banner ok">Este é um dos seus jogos âncora.</p>}
          {!match.anchor && (
            <>
              <ReactionButtons reaction={reaction} onReact={(next) => {
                setReactionError(null)
                reactToGame(game.id, next).catch((error) => setReactionError(apiError(error)))
              }} />
              {reactionError && <p className="hint" role="alert">{reactionError}</p>}
              {reaction === "disliked" && <p className="hint">Este jogo não aparece mais nas suas recomendações.</p>}
              {reaction === "liked" && (
                <p className="hint">
                  {reactionsStale ? "Curtida salva. Ela passa a contar na afinidade quando as sugestões forem atualizadas."
                    : "Os jogos que você curte também entram no cálculo de afinidade."}
                </p>
              )}
            </>
          )}
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
      <div className="tabs" role="tablist" aria-label="Detalhes do jogo">
        {tabs.map((item, index) => (
          <button key={item.id} type="button" role="tab" id={`tab-${item.id}`} className={`tab${tab === item.id ? " on" : ""}`}
            aria-selected={tab === item.id} aria-controls={`panel-${item.id}`} tabIndex={tab === item.id ? 0 : -1}
            onClick={() => setTab(item.id)} onKeyDown={(event) => onTabKey(event, index)}>
            {item.label}
          </button>
        ))}
      </div>
      <section className="pn" role="tabpanel" id="panel-comparison" aria-labelledby="tab-comparison" hidden={tab !== "comparison"}>
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
      <section className="pn" role="tabpanel" id="panel-steam" aria-labelledby="tab-steam" hidden={tab !== "steam"}>
        <h2>Requisitos publicados na Steam</h2>
        <div className="chips" role="group" aria-label="Plataforma dos requisitos">
          {OPERATING_SYSTEMS.map((os) => (
            <button key={os} type="button" className={`chip${system === os ? " on" : ""}`} aria-pressed={system === os}
              onClick={() => setSystem(os)}>
              {os}
            </button>
          ))}
        </div>
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
      {match.reasons.length > 0 && (
        <section className="pn" role="tabpanel" id="panel-why" aria-labelledby="tab-why" hidden={tab !== "why"}>
          <h2>Por que combina com você</h2>
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
