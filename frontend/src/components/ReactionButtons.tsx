import type { Reaction } from "../types"

// Silhueta do polegar: só o contorno quando está inativo e preenchida depois da reação.
export function ThumbIcon({ down = false, filled = false }: { down?: boolean; filled?: boolean }) {
  return (
    <svg className={`thumb${down ? " down" : ""}`} viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false"
      fill={filled ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      {!filled && <path d="M7 10v12" />}
      <path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z" />
    </svg>
  )
}

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
        <ThumbIcon filled={reaction === "liked"} />{!compact && <span>Curtir</span>}
      </button>
      <button type="button" className={`btn ghost small${reaction === "disliked" ? " on" : ""}`} aria-pressed={reaction === "disliked"}
        aria-label="Não curtir este jogo" disabled={busy} onClick={() => toggle("disliked")}>
        <ThumbIcon down filled={reaction === "disliked"} />{!compact && <span>Não curtir</span>}
      </button>
    </div>
  )
}
