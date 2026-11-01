import { useEffect, useState } from "react"
import { Cover } from "../components/GameCard"
import { CatalogStatus } from "../components/CatalogStatus"
import { PageHeader } from "../components/PageHeader"
import { useCatalog } from "../context/CatalogContext"
import { useSession } from "../context/SessionContext"
import { apiError, apiGet } from "../lib/api"
import type { GameSearchResult } from "../types"

type Suggestions = {
  items: GameSearchResult[]
  issues: { appid: string; message: string }[]
}

export function Anchors() {
  const { user, updateUser } = useSession()
  const { games, loadGame } = useCatalog()
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

  async function add(result: GameSearchResult) {
    if (full || adding || anchorIds.includes(result.id)) return
    setAdding(result.id)
    setAddError(null)
    try {
      await loadGame(result.id)
      updateUser({ anchorIds: [...anchorIds, result.id] })
      setQuery("")
      setResults([])
    } catch (error) {
      setAddError(apiError(error))
    } finally {
      setAdding(null)
    }
  }

  return (
    <div className="page narrow">
      <PageHeader
        eyebrow="Jogos âncora"
        title="Três jogos que representam você"
        lede="Pesquise pelo nome ou escolha entre as sugestões abaixo. Selecione três jogos que você gosta para encontrar títulos parecidos."
      />
      <CatalogStatus />
      <ol className="slots">
        {[0, 1, 2].map((index) => {
          const game = selected[index]
          const id = anchorIds[index]
          return (
            <li key={index}>
              <span>Âncora {index + 1}</span>
              {game ? (
                <div className="slot-filled">
                  <Cover game={game} className="cover-sm" />
                  <div>
                    <strong>{game.title}</strong>
                    <p>{game.genres.join(" · ")}</p>
                  </div>
                  <button
                    type="button"
                    className="btn ghost small"
                    disabled={Boolean(adding)}
                    onClick={() =>
                      updateUser({
                        anchorIds: anchorIds.filter((item) => item !== game.id),
                      })
                    }
                  >
                    Remover
                  </button>
                </div>
              ) : id ? (
                <div>
                  <p>Detalhes do jogo salvo ainda não disponíveis.</p>
                  <button
                    type="button"
                    className="btn ghost small"
                    disabled={Boolean(adding)}
                    onClick={() =>
                      updateUser({
                        anchorIds: anchorIds.filter((item) => item !== id),
                      })
                    }
                  >
                    Remover
                  </button>
                </div>
              ) : (
                <p className="muted">Vazio</p>
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
      <label className="stack-label">
        Buscar jogos na Steam
        <input
          value={query}
          maxLength={100}
          placeholder={full ? "Remova um jogo para trocar" : "Digite o nome do jogo"}
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
              <li key={game.id}>
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
          <ul className="anchor-suggestions-grid">
            {suggestions.map((game) => {
              const chosen = anchorIds.includes(game.id)
              return (
                <li className="anchor-suggestion" key={game.id}>
                  <Cover game={{ ...game, image_url: game.image_url ?? null }} />
                  <div className="anchor-suggestion-body">
                    <h3>{game.title}</h3>
                    <button
                      type="button"
                      className="btn small"
                      disabled={full || Boolean(adding) || chosen}
                      onClick={() => void add(game)}
                    >
                      {adding === game.id ? "Carregando…" : chosen ? "Selecionado" : "Usar"}
                    </button>
                  </div>
                </li>
              )
            })}
          </ul>
        </section>
      )}
    </div>
  )
}
