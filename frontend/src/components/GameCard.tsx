import { useState } from "react"
import { Link, useLocation } from "react-router-dom"
import type { Game } from "../types"

function hue(id: string) {
  let hash = 0
  for (const char of id) hash = (hash * 31 + char.charCodeAt(0)) % 360
  return hash
}

export function Cover({ game, className = "" }: {
  game: Pick<Game, "id" | "title" | "image_url">
  className?: string
}) {
  const tone = hue(game.id)
  const [broken, setBroken] = useState(false)
  return (
    <div
      className={`cover ${className}`.trim()}
      style={{
        background: `linear-gradient(160deg, hsl(${tone} 28% 28%), hsl(${(tone + 40) % 360} 22% 14%))`,
      }}
      aria-hidden="true"
    >
      {game.image_url && !broken ? (
        <img src={game.image_url} alt="" loading="lazy" onError={() => setBroken(true)} />
      ) : (
        <span>{game.title.slice(0, 1)}</span>
      )}
    </div>
  )
}

export function GameCard({
  game,
  affinity,
  href,
  note,
  reason,
}: {
  game: Game
  affinity?: number
  href: string
  note?: string
  reason?: string
}) {
  const location = useLocation()
  return (
    <Link className="game-card" to={href} state={{ returnTo: location.pathname + location.search, returnKey: location.key }}>
      <Cover game={game} />
      <div className="game-card-body">
        <div className="game-card-top">
          <h3>{game.title}</h3>
          {typeof affinity === "number" && <strong>{affinity}%</strong>}
        </div>
        <p className="muted">
          {game.developer} · {game.year}
        </p>
        <p className="tags">{game.genres.join(" · ")}</p>
        {typeof affinity === "number" && (
          <div className="meter" aria-hidden="true">
            <span style={{ width: `${affinity}%` }} />
          </div>
        )}
        {note && <p className="note">{note}</p>}
        {reason && <p className="hint card-reason">{reason}</p>}
      </div>
    </Link>
  )
}
