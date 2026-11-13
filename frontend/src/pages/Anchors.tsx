import { useEffect, useState, type DragEvent } from "react"
import { Cover } from "../components/GameCard"
import { CatalogStatus } from "../components/CatalogStatus"
import { PageHeader } from "../components/PageHeader"
import { StepFooter } from "../components/StepFooter"
import { StepNav } from "../components/StepNav"
import { useCatalog } from "../context/CatalogContext"
import { useSession } from "../context/SessionContext"
import { useSound } from "../context/SoundContext"
import { useGridCols } from "../lib/useGridCols"
import "../styles/start.css"
import { apiError, apiGet } from "../lib/api"
import type { GameSearchResult } from "../types"

const GAME_TYPE = "application/x-gamecompass-game"
const SLOT_TYPE = "application/x-gamecompass-slot"

type Suggestions = {
  items: GameSearchResult[]
  issues: { appid: string; message: string }[]
}

export function Anchors() {
  const { user, updateUser } = useSession()
  const { games, loadGame } = useCatalog()
  const { play } = useSound()
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<GameSearchResult[]>([])
  const [searching, setSearching] = useState(false)
  const [adding, setAdding] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [searchRevision, setSearchRevision] = useState(0)
  const [addError, setAddError] = useState<string | null>(null)
  const [suggestions, setSuggestions] = useState<GameSearchResult[]>([])
  const [suggestionsLoading, setSuggestionsLoading] = useState(true)
  const [suggestionsError, setSuggestionsError] = useState<string | null>(null)
  const [partialSuggestions, setPartialSuggestions] = useState(false)
  const [suggestionsRevision, setSuggestionsRevision] = useState(0)
  const anchorIds = user?.anchorIds ?? []
  const full = anchorIds.length >= 3
  const term = query.trim()
  const gridRef = useGridCols(suggestions.length)
  const [over, setOver] = useState<number | null>(null)
  const [dragging, setDragging] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    setSuggestionsLoading(true)
    setSuggestionsError(null)
    setPartialSuggestions(false)
    apiGet<Suggestions>("/games/anchors", controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) {
          setSuggestions(data.items)
          setPartialSuggestions(data.issues.length > 0)
        }
      })
      .catch((error) => {
        if (!controller.signal.aborted) setSuggestionsError(apiError(error))
      })
      .finally(() => {
        if (!controller.signal.aborted) setSuggestionsLoading(false)
      })
    return () => controller.abort()
  }, [suggestionsRevision])

  useEffect(() => {
    const controller = new AbortController()
    setResults([])
    setError(null)
    setSearching(false)
    if (term.length < 2 || full) return () => controller.abort()
    setSearching(true)
    const timer = setTimeout(() => {
      apiGet<{ items: GameSearchResult[] }>(`/games/search?q=${encodeURIComponent(term)}`, controller.signal)
        .then((data) => {
          if (!controller.signal.aborted) setResults(data.items)
        })
        .catch((error) => {
          if (!controller.signal.aborted) setError(apiError(error))
        })
        .finally(() => {
          if (!controller.signal.aborted) setSearching(false)
        })
    }, 350)
    return () => {
      clearTimeout(timer)
      controller.abort()
    }
  }, [term, full, searchRevision])
  if (!user) return null
  const selected = anchorIds.map((id) => games.find((game) => game.id === id))

  /** Põe o jogo no espaço `slot` (substitui quem estiver lá) ou no primeiro espaço livre. */
  async function add(result: GameSearchResult, slot?: number) {
    const replacing = slot !== undefined && slot < anchorIds.length
    if ((full && !replacing) || adding || anchorIds.includes(result.id)) return
    setAdding(result.id)
    setAddError(null)
    try {
      await loadGame(result.id)
      play("select")
      const next = [...anchorIds]
      if (replacing) next[slot] = result.id
      else next.push(result.id)
      updateUser({ anchorIds: next.slice(0, 3) })
      setQuery("")
      setResults([])
    } catch (error) {
      setAddError(apiError(error))
    } finally {
      setAdding(null)
    }
  }

  const startDrag = (event: DragEvent, game: GameSearchResult) => {
    event.dataTransfer.setData(GAME_TYPE, JSON.stringify({ id: game.id, title: game.title, image_url: game.image_url ?? null }))
    event.dataTransfer.effectAllowed = "copy"
    setDragging(true)
  }
  const endDrag = () => { setDragging(false); setOver(null) }
  const dropOn = (event: DragEvent, index: number) => {
    event.preventDefault()
    setOver(null)
    setDragging(false)
    const fromSlot = event.dataTransfer.getData(SLOT_TYPE)
    if (fromSlot !== "") {
      // Troca de posição entre âncoras já escolhidas.
      const from = Number(fromSlot)
      if (from === index || from >= anchorIds.length) return
      const next = [...anchorIds]
      const target = Math.min(index, next.length - 1)
      ;[next[from], next[target]] = [next[target], next[from]]
      play("select")
      updateUser({ anchorIds: next })
      return
    }
    const raw = event.dataTransfer.getData(GAME_TYPE)
    if (!raw) return
    try {
      const game = JSON.parse(raw) as GameSearchResult
      if (typeof game.id === "string" && typeof game.title === "string") void add(game, index)
    } catch {
      // Arrasto de outra origem: ignora.
    }
  }
  const dragTarget = (index: number) => ({
    onDragOver: (event: DragEvent) => {
      const types = event.dataTransfer.types
      if (!types.includes(GAME_TYPE) && !types.includes(SLOT_TYPE)) return
      event.preventDefault()
      event.dataTransfer.dropEffect = types.includes(SLOT_TYPE) ? "move" : "copy"
      if (over !== index) setOver(index)
    },
    onDragLeave: () => setOver((current) => (current === index ? null : current)),
    onDrop: (event: DragEvent) => dropOn(event, index),
  })

  return (
    <div className="page narrow">
      <StepNav current="anchors" />
      <PageHeader
        eyebrow="FASE 2 · ÂNCORAS"
        title="Três jogos que representam você"
        lede="Pesquise pelo nome ou escolha entre as sugestões abaixo. Arraste a capa até um espaço (ou clique em Usar) para escolher três jogos que você gosta. Arrastar sobre um espaço ocupado troca o jogo."
      />
      <CatalogStatus />
      <ol className={dragging ? "anchor-slots dragging" : "anchor-slots"} aria-label="Seus três jogos âncora">
        {[0, 1, 2].map((index) => {
          const game = selected[index]
          const id = anchorIds[index]
          const remove = (target: string) => {
            play("back")
            updateUser({ anchorIds: anchorIds.filter((item) => item !== target) })
          }
          return (
            <li key={game?.id ?? id ?? `vazio-${index}`} className={`anchor-slot${game ? " full" : ""}${over === index ? " over" : ""}`}
              {...dragTarget(index)}
              draggable={Boolean(game)}
              onDragStart={game ? (event) => { event.dataTransfer.setData(SLOT_TYPE, String(index)); event.dataTransfer.effectAllowed = "move"; setDragging(true) } : undefined}
              onDragEnd={endDrag}>
              <span className="lab">ÂNCORA {index + 1}</span>
              {game ? (
                <>
                  <Cover game={game} />
                  <p className="nm">{game.title}</p>
                  <button
                    type="button"
                    className="x"
                    aria-label={`Remover ${game.title}`}
                    disabled={Boolean(adding)}
                    onClick={() => remove(game.id)}
                  >
                    ✕
                  </button>
                </>
              ) : id ? (
                <div className="missing-detail">
                  <p>Detalhes do jogo salvo ainda não disponíveis.</p>
                  <button
                    type="button"
                    className="x"
                    aria-label="Remover jogo salvo"
                    disabled={Boolean(adding)}
                    onClick={() => remove(id)}
                  >
                    ✕
                  </button>
                </div>
              ) : (
                <span className="q" aria-label="Vazio">?</span>
              )}
            </li>
          )
        })}
      </ol>
      {addError && (
        <p className="form-error" role="alert">
          {addError}
        </p>
      )}
      <label className="anchor-search">
        Buscar jogos na Steam
        <input
          value={query}
          maxLength={100}
          placeholder={full ? "3 de 3 escolhidos. Remova um para trocar" : "Digite o nome do jogo"}
          disabled={full || Boolean(adding)}
          onChange={(event) => setQuery(event.target.value)}
        />
      </label>
      {searching && (
        <p className="hint" role="status">
          Buscando jogos…
        </p>
      )}
      {error && (
        <div className="banner warn" role="alert">
          <p>{error}</p>
          <button
            type="button"
            className="btn ghost small"
            onClick={() => setSearchRevision((value) => value + 1)}
          >
            Tentar novamente
          </button>
        </div>
      )}
      {!searching && !error && term.length >= 2 && !full && !results.length && (
        <p className="empty">Nenhum jogo encontrado para esse nome.</p>
      )}
      {!full && (
        <ul className="search-results">
          {results
            .filter((game) => !anchorIds.includes(game.id))
            .map((game) => (
              <li key={game.id} draggable={!adding} onDragStart={(event) => startDrag(event, game)} onDragEnd={endDrag}>
                <div>
                  <strong>{game.title}</strong>
                </div>
                <button
                  type="button"
                  className="btn small"
                  disabled={Boolean(adding)}
                  onClick={() => void add(game)}
                >
                  {adding === game.id ? "Carregando…" : "Usar"}
                </button>
              </li>
            ))}
        </ul>
      )}
      {term.length < 2 && (
        <section className="anchor-suggestions" aria-labelledby="anchor-suggestions-title">
          <div className="section-head">
            <h2 id="anchor-suggestions-title">Sugestões para começar</h2>
            <p className="hint">
              Alguns jogos conhecidos para facilitar sua escolha. Nenhum é selecionado automaticamente.
            </p>
          </div>
          {suggestionsLoading && (
            <p className="hint" role="status">
              Carregando sugestões da Steam…
            </p>
          )}
          {suggestionsError && (
            <div className="banner warn" role="alert">
              <p>{suggestionsError}</p>
              <button
                type="button"
                className="btn ghost small"
                onClick={() => setSuggestionsRevision((value) => value + 1)}
              >
                Tentar novamente
              </button>
            </div>
          )}
          {partialSuggestions && (
            <p className="hint">
              Algumas sugestões não ficaram disponíveis nesta consulta. Você pode buscar outros jogos pelo
              nome.
            </p>
          )}
          {!suggestionsLoading && !suggestionsError && !suggestions.length && (
            <p className="empty">Nenhuma sugestão disponível agora. Use a busca pelo nome.</p>
          )}
          <ul className="anchor-suggestions-grid card-grid" ref={gridRef}>
            {suggestions.map((game) => {
              const chosen = anchorIds.includes(game.id)
              return (
                <li className={`anchor-suggestion${chosen ? " chosen" : full ? " locked" : ""}`} key={game.id}
                  draggable={!chosen && !adding} onDragStart={(event) => startDrag(event, game)} onDragEnd={endDrag}>
                  <Cover game={{ ...game, image_url: game.image_url ?? null }} />
                  <div className="anchor-suggestion-body">
                    <h3>{game.title}</h3>
                    <button
                      type="button"
                      className="btn small"
                      disabled={full || Boolean(adding) || chosen}
                      onClick={() => void add(game)}
                    >
                      {adding === game.id ? "Carregando…" : chosen ? "Escolhido" : "Usar"}
                    </button>
                  </div>
                </li>
              )
            })}
          </ul>
        </section>
      )}
      <StepFooter id="anchors" />
    </div>
  )
}
