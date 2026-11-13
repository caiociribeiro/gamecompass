import { useState, type ReactNode } from "react"
import { Link, useLocation } from "react-router-dom"
import type { Game } from "../types"

function hue(id: string) {
  let hash = 0
  for (const char of id) hash = (hash * 31 + char.charCodeAt(0)) % 360
  return hash
}

export function Cover({ game, className = "", badge }: {
  game: Pick<Game, "id" | "title" | "image_url">
  className?: string
  badge?: { label: string; tone?: "ok" | "min" | "pending" }
}) {
  const tone = hue(game.id)
  const [failed, setFailed] = useState(false)
  const src = failed ? null : game.image_url
  return (
    <div
      className={`cover ${className}`.trim()}
      style={{ background: `linear-gradient(160deg, hsl(${tone} 38% 32%), hsl(${(tone + 40) % 360} 30% 16%))` }}
      aria-hidden="true"
    >
      {src ? (
        <img
          src={src}
          alt=""
          loading="lazy"
          decoding="async"
          onError={() => setFailed(true)}
        />
      ) : (
        <span>{game.title.slice(0, 1)}</span>
      )}
      {badge && <span className={`cover-badge ${badge.tone ?? "pending"}`}>{badge.label}</span>}
    </div>
  )
}

export function GameCard({
  game,
  affinity,
  href,
  note,
  reason,
  chips,
  actions,
  badge,
  leaving = false,
}: {
  game: Game
  affinity?: number
  href: string
  note?: string
  reason?: string
  chips?: string[]
  actions?: ReactNode
  badge?: { label: string; tone?: "ok" | "min" | "pending" }
  /** O jogo foi marcado como não curtido e está caindo da lista. */
  leaving?: boolean
}) {
  const location = useLocation()
  const card = (
    <Link className="game-card" to={href} state={{ returnTo: location.pathname + location.search, returnKey: location.key }}>
      <Cover game={game} badge={badge} />
      <div className="game-card-body">
        <div className="game-card-top">
          <h3>{game.title}</h3>
          {typeof affinity === "number" && <strong>{affinity}%</strong>}
        </div>
        {typeof affinity === "number" && (
          <div className="meter" aria-hidden="true">
            <span style={{ width: `${affinity}%` }} />
          </div>
        )}
        {note && <p className={badge?.tone ? `note ${badge.tone}` : "note"}>{note}</p>}
        {chips && chips.length > 0 && (
          <ul className="why-chips" aria-label="Por que combina com você">
            {chips.map((chip) => <li key={chip}>{chip}</li>)}
          </ul>
        )}
        {reason && !chips?.length && <p className="hint card-reason">{reason}</p>}
      </div>
    </Link>
  )
  // Os botões ficam fora do link: botão dentro de link não é HTML válido nem acessível.
  const shell = leaving ? "game-card-shell gone" : "game-card-shell"
  return actions ? <div className={shell}>{card}<div className="game-card-actions">{actions}</div></div> : <div className={shell}>{card}</div>
}
