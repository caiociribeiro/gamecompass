// Apresentação e preenchimento do formulário. O cálculo é feito pela FastAPI.
import type { Game, GameMatch, HardwareCatalog, HardwareProfile, UserProfile } from "../types"

export function compatibilityLabel(match: Pick<GameMatch, "compatibility" | "meets" | "estimated">): string {
  const label = match.meets === "recommended" ? "Atende aos recomendados"
    : match.meets === "minimum" ? "Atende aos mínimos"
      : match.compatibility === "incompatible" ? "Não atende aos mínimos" : "Validação dos mínimos pendente"
  return match.estimated && match.compatibility !== "needs_review" ? `${label} (estimativa)` : label
}

export function anchorsOf(user: UserProfile, games: Game[]) {
  return [...new Set(user.anchorIds)].map((id) => games.find((game) => game.id === id))
    .filter((game): game is Game => Boolean(game))
}

export function hardwareProfileReady(profile: HardwareProfile | null, hardware: HardwareCatalog) {
  return Boolean(profile && Number.isFinite(profile.ramGb) && profile.ramGb > 0 &&
    ["Windows", "Linux", "macOS"].includes(profile.os) &&
    (profile.os !== "Windows" || profile.windowsVersion === "10" || profile.windowsVersion === "11") &&
    hardware.CPU.some((part) => part.id === profile.cpuId) && hardware.GPU.some((part) => part.id === profile.gpuId))
}

export function profileReady(user: UserProfile, games: Game[], hardware: HardwareCatalog) {
  return user.genres.length > 0 && user.themes.length > 0 && anchorsOf(user, games).length === 3 &&
    hardwareProfileReady(user.hardware, hardware)
}
