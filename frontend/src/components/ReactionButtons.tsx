import type { Reaction } from "../types"

export function ReactionButtons({ reaction, onReact, busy = false, compact = false }: {
  reaction: Reaction | null | undefined
  onReact: (next: Reaction | null) => void
  busy?: boolean
  compact?: boolean
}) {
  // Tocar no botão ativo remove a reação.
  const toggle = (target: Reaction) => onReact(reaction === target ? null : target)
  return (
    <div className={`reactions${compact ? " compact" : ""}`} role="group" aria-label="Sua opinião sobre este jogo">
      <button type="button" className={`btn ghost small${reaction === "liked" ? " on" : ""}`} aria-pressed={reaction === "liked"}
        aria-label="Curtir este jogo" disabled={busy} onClick={() => toggle("liked")}>
        {compact ? "👍" : "👍 Curtir"}
      </button>
      <button type="button" className={`btn ghost small${reaction === "disliked" ? " on" : ""}`} aria-pressed={reaction === "disliked"}
        aria-label="Não curtir este jogo" disabled={busy} onClick={() => toggle("disliked")}>
        {compact ? "👎" : "👎 Não curtir"}
      </button>
    </div>
  )
}
