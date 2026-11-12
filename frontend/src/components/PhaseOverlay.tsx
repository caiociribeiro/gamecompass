import { useEffect } from "react"
import { useSound } from "../context/SoundContext"

const COLORS = ["#ff7a59", "#5cff9d", "#ffd86b", "#6be1ff", "#ff9bb5"]

/** "FASE CONCLUÍDA": aviso grande no centro da janela, com confete. */
export function PhaseCleared({ title, subtitle }: { title: string; subtitle?: string }) {
  const { play } = useSound()
  useEffect(() => { play("fanfare") }, [play])
  return (
    <div className="overlay" role="status" aria-live="polite">
      {Array.from({ length: 28 }, (_, index) => (
        <i key={index} className="confetti" style={{ left: `${index * 3.6}%`, background: COLORS[index % 5], animationDelay: `${(index % 7) * 0.15}s` }} />
      ))}
      <div className="overlay-text">
        {title}
        {subtitle && <small>{subtitle}</small>}
      </div>
    </div>
  )
}

/** Barra de carregamento em blocos, no lugar do "aguarde". */
export function LoadingBar({ label = "PROCURANDO JOGOS..." }: { label?: string }) {
  return (
    <div role="status" aria-live="polite" style={{ padding: "50px 0" }}>
      <div className="loadbar"><i /></div>
      <p className="loading-text">{label}</p>
    </div>
  )
}
