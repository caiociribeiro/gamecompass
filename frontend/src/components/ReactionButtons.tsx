import { useEffect, useRef, useState } from "react"
import { useSound } from "../context/SoundContext"
import type { Reaction } from "../types"
import { HeartIcon } from "./PixelIcons"

/** Coração cheio = curtiu; coração partido = não curtiu. Tocar no botão ativo remove a reação. */
export function ReactionButtons({ reaction, onReact, busy = false, compact = false }: {
  reaction: Reaction | null | undefined
  onReact: (next: Reaction | null) => void
  busy?: boolean
  compact?: boolean
}) {
  const { play } = useSound()
  const [animated, setAnimated] = useState<Reaction | null>(null)
  const first = useRef(true)
  useEffect(() => { first.current = false }, [])
  const toggle = (target: Reaction) => {
    const next = reaction === target ? null : target
    setAnimated(next)
    if (next === "liked") play("love")
    else if (next === "disliked") play("break")
    onReact(next)
  }
  return (
    <div className={`reactions${compact ? " compact" : ""}`} role="group" aria-label="Sua opinião sobre este jogo">
      <button type="button" className={`rx-btn${reaction === "liked" ? " on" : ""}`} aria-pressed={reaction === "liked"}
        aria-label="Curtir este jogo" disabled={busy} onClick={() => toggle("liked")}>
        <HeartIcon filled={reaction === "liked"} animate={animated === "liked"} />{!compact && <span>{reaction === "liked" ? "CURTIDO" : "CURTIR"}</span>}
      </button>
      <button type="button" className={`rx-btn${reaction === "disliked" ? " on" : ""}`} aria-pressed={reaction === "disliked"}
        aria-label="Não curtir este jogo" disabled={busy} onClick={() => toggle("disliked")}>
        <HeartIcon broken filled={reaction === "disliked"} animate={animated === "disliked"} />{!compact && <span>{reaction === "disliked" ? "NÃO CURTIDO" : "NÃO CURTIR"}</span>}
      </button>
    </div>
  )
}
