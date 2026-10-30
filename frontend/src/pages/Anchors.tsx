import { useEffect, useState } from "react"
import { Cover } from "../components/GameCard"
import { CatalogStatus } from "../components/CatalogStatus"
import { PageHeader } from "../components/PageHeader"
import { useCatalog } from "../context/CatalogContext"
import { useSession } from "../context/SessionContext"
import { apiError, apiGet } from "../lib/api"
import type { GameSearchResult } from "../types"

export function Anchors() {
  const { user, updateUser } = useSession()
  const { games, loadGame } = useCatalog()
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<GameSearchResult[]>([])
  const [searching, setSearching] = useState(false)
  const [adding, setAdding] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const anchorIds = user?.anchorIds ?? []
  const full = anchorIds.length >= 3
  const term = query.trim()

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
  }, [term, full])
  if (!user) return null
  const selected = anchorIds.map((id) => games.find((game) => game.id === id))

  async function add(result: GameSearchResult) {
    if (full || adding || anchorIds.includes(result.id)) return
    setAdding(result.id)
    setError(null)
    try {
      await loadGame(result.id)
      updateUser({ anchorIds: [...anchorIds, result.id] })
      setQuery("")
      setResults([])
    } catch (error) {
      setError(apiError(error))
    } finally {
      setAdding(null)
    }
  }

  return (
    <div className="page narrow">
      <PageHeader
        eyebrow="Jogos âncora"
        title="Três jogos que representam você"
        lede="Pesquise pelo nome e escolha três jogos que você gosta. Eles ajudam a encontrar títulos parecidos."
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
                    onClick={() => updateUser({ anchorIds: anchorIds.filter((item) => item !== game.id) })}
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
                    onClick={() => updateUser({ anchorIds: anchorIds.filter((item) => item !== id) })}
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
        <p className="form-error" role="alert">
          {error}
        </p>
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
    </div>
  )
}
