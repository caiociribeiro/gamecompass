import { useMemo, useState } from "react"
import { Cover } from "../components/GameCard"
import { PageHeader } from "../components/PageHeader"
import { useSession } from "../context/SessionContext"
import { GAMES, findGame } from "../data/catalog"
import { fold } from "../lib/text"

export function Anchors() {
  const { user, updateUser } = useSession()
  const [query, setQuery] = useState("")
  const anchorIds = user?.anchorIds ?? []
  const results = useMemo(() => {
    const q = fold(query.trim())
    if (!q) return []
    return GAMES.filter((game) => fold(game.title).includes(q) && !anchorIds.includes(game.id)).slice(0, 6)
  }, [query, anchorIds])
  if (!user) return null

  const selected = anchorIds.map((id) => findGame(id)).filter((game) => Boolean(game))

  function add(id: string) {
    if (anchorIds.length >= 3 || anchorIds.includes(id)) return
    updateUser({ anchorIds: [...anchorIds, id] })
    setQuery("")
  }

  function remove(id: string) {
    updateUser({ anchorIds: anchorIds.filter((item) => item !== id) })
  }

  return (
    <div className="page narrow">
      <PageHeader
        eyebrow="Jogos âncora"
        title="Três jogos que representam você"
        lede="Eles precisam existir no catálogo de demonstração. A lista de recomendações não repete esses títulos."
      />

      <ol className="slots">
        {[0, 1, 2].map((index) => {
          const game = selected[index]
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
                  <button type="button" className="btn ghost small" onClick={() => remove(game.id)}>
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
        Buscar no catálogo
        <input
          value={query}
          placeholder={anchorIds.length >= 3 ? "Remova um jogo para trocar" : "Nome do jogo"}
          disabled={anchorIds.length >= 3}
          onChange={(event) => setQuery(event.target.value)}
        />
      </label>

      {query.trim() && results.length === 0 && (
        <p className="empty">Nenhum jogo com esse nome na base de demonstração.</p>
      )}

      <ul className="search-results">
        {results.map((game) => (
          <li key={game.id}>
            <div>
              <strong>{game.title}</strong>
              <p>
                {game.developer} · {game.genres.join(", ")}
              </p>
            </div>
            <button type="button" className="btn small" onClick={() => add(game.id)}>
              Usar
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
