import { anchorsOf } from "./recommend"
import type { ProfileStep, UserProfile } from "../types"

export function profileSteps(user: UserProfile): ProfileStep[] {
  return [
    {
      id: "prefs",
      label: "Gêneros e temáticas",
      hint: "O que você costuma buscar em um jogo.",
      done: user.genres.length > 0 && user.themes.length > 0,
      to: "/app/preferencias",
    },
    {
      id: "anchors",
      label: "Três jogos âncora",
      hint: "Três títulos que você já jogou e jogaria de novo.",
      done: anchorsOf(user).length === 3,
      to: "/app/ancoras",
    },
    {
      id: "hardware",
      label: "Computador",
      hint: "Processador, placa de vídeo, memória e sistema.",
      done: user.hardware !== null,
      to: "/app/hardware",
    },
  ]
}
