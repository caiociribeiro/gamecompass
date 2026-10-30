import { anchorsOf } from "./recommend"
import type { Game, HardwareCatalog, ProfileStep, UserProfile } from "../types"

export function profileSteps(user: UserProfile, games: Game[], hardware: HardwareCatalog): ProfileStep[] {
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
      hint: "Escolha três títulos reais da Steam.",
      done: anchorsOf(user, games).length === 3,
      to: "/app/ancoras",
    },
    {
      id: "hardware",
      label: "Computador",
      hint: "CPU, GPU, memória RAM e sistema operacional.",
      done:
        user.hardware !== null &&
        hardware.CPU.some((part) => part.id === user.hardware?.cpuId) &&
        hardware.GPU.some((part) => part.id === user.hardware?.gpuId),
      to: "/app/hardware",
    },
  ]
}
