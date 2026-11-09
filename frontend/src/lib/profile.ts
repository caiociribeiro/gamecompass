import { anchorsOf, hardwareProfileReady } from "./recommend.ts"
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
      hint: "CPU, GPU, memória RAM e sistema operacional. Para Windows, informe a versão.",
      done: hardwareProfileReady(user.hardware, hardware),
      to: "/app/hardware",
    },
  ]
}

/** Primeira etapa ainda incompleta, ou null quando o perfil está todo preenchido. */
export function nextPendingStep(steps: ProfileStep[]): ProfileStep | null {
  return steps.find((step) => !step.done) ?? null
}

export type StepId = "prefs" | "anchors" | "hardware"

export type StepGuide = {
  /** Posição da etapa, começando em 1. */
  position: number
  total: number
  done: boolean
  /** Frase mostrada quando a etapa está completa. */
  status: string
  /** Frase mostrada enquanto falta algo, dizendo exatamente o que falta. */
  missing: string
  next: { to: string; label: string }
}

const NEXT: Record<StepId, { to: string; label: string }> = {
  prefs: { to: "/app/ancoras", label: "Continuar para jogos âncora" },
  anchors: { to: "/app/hardware", label: "Continuar para o computador" },
  hardware: { to: "/app/recomendacoes", label: "Ver recomendações" },
}

const plural = (count: number, one: string, many: string) => (count === 1 ? one : many)

/** O que a pessoa precisa saber ao fim de cada etapa: terminou? falta algo? para onde vai agora? */
export function stepGuide(
  user: UserProfile,
  games: Game[],
  hardware: HardwareCatalog,
  id: StepId,
): StepGuide {
  const steps = profileSteps(user, games, hardware)
  const index = steps.findIndex((step) => step.id === id)
  const done = steps[index].done
  const base = { position: index + 1, total: steps.length, done, next: NEXT[id] }
  if (id === "prefs") {
    const genres = user.genres.length
    const themes = user.themes.length
    const lacking = genres === 0 && themes === 0 ? "um gênero e uma temática"
      : genres === 0 ? "um gênero" : "uma temática"
    return {
      ...base,
      status: `${genres} ${plural(genres, "gênero", "gêneros")} e ${themes} ${plural(themes, "temática", "temáticas")} escolhidos.`,
      missing: `Escolha pelo menos ${lacking} para continuar.`,
    }
  }
  if (id === "anchors") {
    const left = Math.max(0, 3 - anchorsOf(user, games).length)
    return {
      ...base,
      status: "Os três jogos âncora estão escolhidos.",
      missing: `Escolha mais ${left} ${plural(left, "jogo", "jogos")} para continuar.`,
    }
  }
  return {
    ...base,
    status: "Computador salvo.",
    missing: "Preencha os campos e clique em Salvar computador para continuar.",
  }
}
