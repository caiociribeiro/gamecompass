import { useEffect, useRef, useState } from "react"
import { PageHeader } from "../components/PageHeader"
import { StepFooter } from "../components/StepFooter"
import { StepNav } from "../components/StepNav"
import { useSession } from "../context/SessionContext"
import { useSound } from "../context/SoundContext"
import { GENRES, THEMES } from "../data/preferences"
import "../styles/start.css"

function toggle(list: string[], value: string) {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value]
}

const SPARKS = [
  "translate(-14px,-16px)", "translate(14px,-18px)", "translate(-20px,2px)",
  "translate(20px,4px)", "translate(-8px,16px)", "translate(10px,18px)",
]

export function Preferences() {
  const { user, updateUser, saving, saveError } = useSession()
  const { play } = useSound()
  const [popped, setPopped] = useState<string | null>(null)
  const [flash, setFlash] = useState(0)
  const timer = useRef<number | null>(null)
  useEffect(() => () => { if (timer.current) window.clearTimeout(timer.current) }, [])
  if (!user) return null

  function pick(key: "genres" | "themes", value: string) {
    if (!user) return
    const turningOn = !user[key].includes(value)
    play("select")
    updateUser({ [key]: toggle(user[key], value) })
    setFlash((count) => count + 1)
    if (turningOn) {
      setPopped(`${key}:${value}`)
      if (timer.current) window.clearTimeout(timer.current)
      timer.current = window.setTimeout(() => setPopped(null), 500)
    } else {
      setPopped(null)
    }
  }

  function group(key: "genres" | "themes", title: string, options: readonly string[]) {
    if (!user) return null
    return (
      <div className="pref-group">
        <div className="pref-head">
          <h2>{title}</h2>
          <span className="pref-count" aria-label={`${user[key].length} de ${options.length} escolhidos`}>
            {user[key].length} / {options.length}
          </span>
        </div>
        <div className="chips pref-chips">
          {options.map((option) => {
            const on = user[key].includes(option)
            const fresh = popped === `${key}:${option}`
            return (
              <button
                key={option}
                type="button"
                className={`chip${on ? " on" : ""}${fresh ? " pop" : ""}`}
                aria-pressed={on}
                onClick={() => pick(key, option)}
              >
                {option}
                {fresh &&
                  SPARKS.map((d, index) => (
                    <i key={index} className="spark" aria-hidden="true" style={{ left: "50%", top: "50%", ["--d" as string]: d }} />
                  ))}
              </button>
            )
          })}
        </div>
      </div>
    )
  }

  return (
    <div className="page narrow">
      <StepNav current="prefs" />
      <PageHeader
        eyebrow="FASE 1 · PERFIL"
        title="O que você procura em um jogo"
        lede="Escolha pelo menos um gênero e uma temática. Cada clique é salvo na sua conta na hora, sem precisar de botão de salvar."
      />
      <div className={flash > 0 && !saving && saveError ? "save-flash error" : "save-flash"} key={flash} role="status" aria-live="polite">
        {flash > 0 ? (saving ? "SALVANDO…" : saveError ? "NÃO FOI SALVO" : "SALVO NA CONTA") : ""}
      </div>
      <section>
        {group("genres", "Gêneros", GENRES)}
        {group("themes", "Temáticas", THEMES)}
        <p className="hint" style={{ marginTop: 16 }}>
          As temáticas dos jogos catalogados são classificadas pelo GameCompass e participam da
          afinidade. Jogos consultados fora desse catálogo podem ter essa classificação pendente.
        </p>
      </section>
      <StepFooter id="prefs" />
    </div>
  )
}
