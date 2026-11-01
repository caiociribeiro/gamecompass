import type { UserProfile } from "../types"

type Preferences = Pick<UserProfile, "anchorIds" | "genres" | "themes">
const names = (values: string[]) => [...new Set(values.map((value) => value.trim()).filter(Boolean))].sort()

export function discoveryFilters(user: Preferences | null) {
  return {
    anchor_ids: names(user?.anchorIds ?? []).filter((id) => /^[1-9][0-9]{0,9}$/.test(id)).slice(0, 3).join(","),
    genres: names(user?.genres ?? []).join(","),
    tags: names(user?.themes ?? []).join(","),
  }
}

// Uma resposta antiga nunca deve substituir uma busca iniciada para outro perfil.
export class RequestScope {
  private version = 0
  private controller: AbortController | null = null

  cancel() {
    this.version += 1
    this.controller?.abort()
    this.controller = null
  }

  start() {
    this.cancel()
    const controller = new AbortController()
    this.controller = controller
    const version = this.version
    return { signal: controller.signal,
      isCurrent: () => version === this.version && !controller.signal.aborted }
  }
}
