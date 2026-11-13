import { Link, useLocation, useSearchParams } from "react-router-dom"
import { CatalogStatus } from "../components/CatalogStatus"
import { GameCard } from "../components/GameCard"
import { ReactionButtons } from "../components/ReactionButtons"
import { PageHeader } from "../components/PageHeader"
import { useCatalog } from "../context/CatalogContext"
import { useSession } from "../context/SessionContext"
import { explanationChips } from "../lib/explain"
import { nextPendingStep, profileSteps } from "../lib/profile"
import { compatibilityLabel, profileReady } from "../lib/recommend"
import { fold } from "../lib/text"
import { useState } from "react"
import { Pager, usePage } from "../components/Pager"
import { HeartIcon } from "../components/PixelIcons"
import { useGridCols } from "../lib/useGridCols"
import { LoadingBar } from "../components/PhaseOverlay"
import { StepNav } from "../components/StepNav"
import "../styles/results.css"
import { apiError } from "../lib/api"
import type { GameMatch, Reaction } from "../types"

const STATUS_FILTERS: [string, string][] = [
  ["all", "Todos"],
  ["recommended", "Recomendados atendidos"],
  ["minimum", "Apenas mínimos atendidos"],
  ["pending", "Validação pendente"],
  ["incompatible", "Com restrições"],
]

const PAGE_SIZE = 12
const EMPTY_RESULT = { items: [] as GameMatch[], pending: [] as GameMatch[], excluded: [] as GameMatch[] }
const HELP_KEY = "gc_help_reactions"

function readHelpHidden() {
  try { return localStorage.getItem(HELP_KEY) === "off" } catch { return false }
}

/** Explica os dois corações antes de a pessoa reagir. */
function ReactionHelp() {
  const [hidden, setHidden] = useState(readHelpHidden)
  if (hidden) return null
  return (
    <aside className="panel rx-help" aria-label="Como funcionam as reações">
      <h2>Curtir ou não curtir?</h2>
      <ul>
        <li><span className="rx-help-icon" aria-hidden="true"><HeartIcon filled /></span>
          <span><b>Curtir</b> diz que o jogo tem a sua cara. Ele reforça a afinidade das próximas sugestões quando você atualizar a lista.</span></li>
        <li><span className="rx-help-icon" aria-hidden="true"><HeartIcon broken filled /></span>
          <span><b>Não curtir</b> tira o jogo da lista na hora, e ele não volta a ser sugerido.</span></li>
      </ul>
      <p className="hint">Clicar de novo no mesmo coração desfaz a reação. Tudo fica no histórico da sua conta.</p>
      <button type="button" className="btn small ghost" onClick={() => {
        setHidden(true)
        try { localStorage.setItem(HELP_KEY, "off") } catch { /* sem armazenamento: só esconde agora */ }
      }}>Entendi</button>
    </aside>
  )
}

export function Recommendations() {
  const { user } = useSession()
  const location = useLocation()
  const [params, setParams] = useSearchParams()
  const { games, hardware, discovered, discoverGames, gamesLoading, candidateSource, gameIssues, recommendations,
    reactions, reactionsStale, reactToGame, leaving } = useCatalog()
  const [reactionError, setReactionError] = useState<string | null>(null)
  const reactionOf = (match: GameMatch) => reactions[match.game.id] !== undefined ? reactions[match.game.id] : match.reaction
  const card = (match: GameMatch) => (
    <GameCard
      key={match.game.id}
      game={match.game}
      affinity={match.affinity}
      href={`/app/jogos/${match.game.id}`}
      note={compatibilityLabel(match)}
      badge={match.meets === "recommended" ? { label: "RECOMENDADO", tone: "ok" } : match.meets === "minimum" ? { label: "MÍNIMO", tone: "min" } : { label: "PENDENTE", tone: "pending" }}
      reason={match.reasons.find((reason) => reason.startsWith("Em comum com "))}
      leaving={leaving.has(match.game.id)}
      chips={explanationChips(match)}
      actions={
        <ReactionButtons compact reaction={reactionOf(match)} onReact={(next: Reaction | null) => {
          setReactionError(null)
          reactToGame(match.game.id, next).catch((error) => setReactionError(apiError(error)))
        }} />
      }
    />
  )
  const query = params.get("q") ?? ""
  const status = params.get("status") ?? "all"
  const filter = ["recommended", "minimum", "pending", "incompatible"].includes(status) ? status : "all"
  function updateFilter(key: "q" | "status", value: string) {
    const next = new URLSearchParams(params)
    if (value && !(key === "status" && value === "all")) next.set(key, value)
    else next.delete(key)
    setParams(next, { replace: true })
  }
  const result = recommendations ?? EMPTY_RESULT
  const needle = fold(query.trim())
  const matches = (title: string) => fold(title).includes(needle)
  const items = result.items.filter((match) => matches(match.game.title) && (filter === "all" || match.meets === filter))
  const pending = filter === "all" || filter === "pending" ? result.pending.filter((match) => matches(match.game.title)) : []
  const excluded = filter === "all" || filter === "incompatible" ? result.excluded.filter((match) => matches(match.game.title)) : []
  const resetKey = `${query}|${filter}|${result.items.length}|${result.pending.length}`
  const itemPage = usePage(items, PAGE_SIZE, resetKey)
  const pendingPage = usePage(pending, PAGE_SIZE, resetKey)
  const itemGrid = useGridCols(itemPage.items.length)
  const pendingGrid = useGridCols(pendingPage.items.length)
  if (!user) return null
  const ready = profileReady(user, games, hardware)
  const visible = items.length + pending.length + excluded.length
  const total = result.items.length + result.pending.length + result.excluded.length
  return (
    <div className="page">
      {!(ready && discovered) && <StepNav current="recs" />}
      <PageHeader
        eyebrow="Recomendações"
        title="Jogos para o seu perfil e para o seu PC"
        lede="A afinidade considera gêneros e temáticas dos seus jogos âncora. As verificações mostram o que já foi comparado e o que ainda precisa de revisão."
      />
      <CatalogStatus />
      <CatalogStatus scope="hardware" />
      {!ready && (() => {
        const steps = profileSteps(user, games, hardware)
        const next = nextPendingStep(steps)
        return (
          <section className="stack">
            <h2>Falta pouco para as suas recomendações</h2>
            <p className="hint">
              {steps.filter((step) => step.done).length} de {steps.length} etapas concluídas. Termine as que faltam
              para ver os jogos que combinam com você e funcionam no seu computador.
            </p>
            <ul className="plain-list">
              {steps
                .filter((step) => !step.done)
                .map((step) => (
                  <li key={step.id}>
                    <Link to={step.to}>{step.label}</Link>
                    <span>{step.hint}</span>
                  </li>
                ))}
            </ul>
            {next && (
              <Link className="btn next-cta" to={next.to}>
                Continuar: {next.label}
              </Link>
            )}
          </section>
        )
      })()}
      {ready && (
        <div className="stack">
          <button type="button" className="btn" disabled={gamesLoading} onClick={() => void discoverGames()}>
            {gamesLoading ? "Buscando sugestões…" : discovered ? "Atualizar sugestões" : "Buscar sugestões"}
          </button>
          {gamesLoading && <LoadingBar />}
          {!discovered && !gamesLoading && <p className="hint">As sugestões são consultadas quando você solicitar.</p>}
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
          <div className="sum">
            <span className="tg g">{result.items.filter((match) => match.meets === "recommended").length} atendem aos recomendados</span>
            <span className="tg y">{result.items.filter((match) => match.meets === "minimum").length} atendem aos mínimos</span>
            <span className="tg p">{result.pending.length} com validação pendente</span>
            <span className="tg r">{result.excluded.length} com restrições identificadas</span>
          </div>
          <div className="flt">
            <label className="flt-name">
              Filtrar a lista
              <input
                value={query}
                placeholder="Nome do jogo"
                onChange={(event) => updateFilter("q", event.target.value)}
              />
            </label>
            <div className="chips" role="group" aria-label="Situação dos requisitos">
              {STATUS_FILTERS.map(([value, label]) => (
                <button key={value} type="button" className={`chip${filter === value ? " on" : ""}`} aria-pressed={filter === value}
                  onClick={() => updateFilter("status", value)}>
                  {label}
                </button>
              ))}
            </div>
          </div>
          <ReactionHelp />
          <p className="count" role="status">Exibindo {visible} de {total} resultados.</p>
          {reactionError && <p className="hint" role="alert">{reactionError}</p>}
          {reactionsStale && (
            <p className="banner reactions-banner" role="status">
              Suas reações foram salvas. Jogos que você não curtiu já saíram da lista; as curtidas entram no cálculo de
              afinidade quando você atualizar as sugestões.{" "}
              <button type="button" className="btn small" disabled={gamesLoading} onClick={() => void discoverGames()}>
                Atualizar sugestões
              </button>
            </p>
          )}
          {visible === 0 && <p className="empty">{total > 0
            ? "Nenhum jogo encontrado com esses filtros."
            : "Nenhuma sugestão disponível para este conjunto de âncoras e preferências. Experimente outras escolhas."}</p>}
          {items.length > 0 && (
            <section className="stack" id="pager-requisitos-atendidos">
              <h2>Requisitos atendidos</h2>
              <div className="card-grid" ref={itemGrid}>
                {itemPage.items.map(card)}
              </div>
              <Pager page={itemPage.page} pages={itemPage.pages} onChange={itemPage.setPage} label="requisitos-atendidos" />
            </section>
          )}
          {pending.length > 0 && (
          <section className="stack" id="pager-aguardando-validacao">
            <h2>Com afinidade, aguardando validação</h2>
            <p className="hint">
              Esses jogos combinam com seu perfil. Consulte as pendências antes de concluir se atendem ao
              computador.
            </p>
            <div className="card-grid" ref={pendingGrid}>
              {pendingPage.items.map(card)}
            </div>
            <Pager page={pendingPage.page} pages={pendingPage.pages} onChange={pendingPage.setPage} label="aguardando-validacao" />
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
