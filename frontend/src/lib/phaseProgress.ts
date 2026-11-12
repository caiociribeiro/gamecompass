import { anchorsOf } from "./recommend.ts"
import type { Game, HardwareCatalog, UserProfile } from "../types"
import { hardwareProfileReady } from "./recommend.ts"

export type PhaseId = "prefs" | "anchors" | "hardware" | "recs"

/** Quanto de cada fase já foi preenchido (0 a 1), só para encher a barra de nível. */
export function phaseProgress(user: UserProfile, games: Game[], hardware: HardwareCatalog): Record<"prefs" | "anchors" | "hardware", number> {
  return {
    prefs: ((user.genres.length > 0 ? 1 : 0) + (user.themes.length > 0 ? 1 : 0)) / 2,
    anchors: Math.min(3, anchorsOf(user, games).length) / 3,
    hardware: hardwareProfileReady(user.hardware, hardware) ? 1 : 0,
  }
}
