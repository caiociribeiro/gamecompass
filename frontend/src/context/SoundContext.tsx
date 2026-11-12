import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react"
import { playSound, readEnabled, saveEnabled, unlockAudio, type SoundName } from "../lib/sound"

type SoundValue = { enabled: boolean; toggle: () => void; play: (name: SoundName) => void }

const SoundContext = createContext<SoundValue | null>(null)

/** Som ligado por padrão; a pessoa desliga no botão do cabeçalho. Toca um "blip" em cada botão ou link. */
export function SoundProvider({ children }: { children: ReactNode }) {
  const [enabled, setEnabled] = useState(readEnabled)

  const play = useCallback((name: SoundName) => { if (enabled) playSound(name) }, [enabled])
  const toggle = useCallback(() => {
    setEnabled((current) => {
      saveEnabled(!current)
      return !current
    })
  }, [])

  useEffect(() => {
    const unlock = () => unlockAudio()
    const onClick = (event: MouseEvent) => {
      unlockAudio()
      const target = event.target as HTMLElement | null
      if (enabled && target?.closest("button, a, [role='button'], .chip")) playSound("click")
    }
    window.addEventListener("keydown", unlock)
    document.addEventListener("click", onClick, true)
    return () => {
      window.removeEventListener("keydown", unlock)
      document.removeEventListener("click", onClick, true)
    }
  }, [enabled])

  const value = useMemo(() => ({ enabled, toggle, play }), [enabled, toggle, play])
  return <SoundContext.Provider value={value}>{children}</SoundContext.Provider>
}

export function useSound(): SoundValue {
  const value = useContext(SoundContext)
  return value ?? { enabled: false, toggle: () => {}, play: () => {} }
}
