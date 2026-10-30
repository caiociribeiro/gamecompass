import type { OPERATING_SYSTEMS } from "./data/hardware"

export type OperatingSystem = (typeof OPERATING_SYSTEMS)[number]
export type RequirementsBlock = {
  text: string
  os_text: string | null
  status: "resolved" | "needs_review"
  requirements: { ram_gb: number | null; cpu_score: number | null; gpu_score: number | null }
  issues: string[]
  score_version: string
}
export type Game = {
  id: string
  title: string
  developer: string
  year: number | null
  genres: string[]
  themes: string[]
  themes_status: "pending" | "classified"
  summary: string
  image_url: string | null
  store_url: string
  price_text: string | null
  platforms: Record<
    OperatingSystem,
    {
      native_support: boolean | null
      minimum: RequirementsBlock | null
      recommended: RequirementsBlock | null
    }
  >
  source: { source_url: string; collected_at: string; response_sha256: string }
}
export type Part = {
  id: string
  name: string
  vendor: string
  performance_score: number | null
  score_version: string
}
export type HardwareCatalog = { CPU: Part[]; GPU: Part[]; score_version: string; source: "neo4j" }
export type GameSearchResult = { id: string; title: string }
export type HardwareProfile = { cpuId: string; gpuId: string; ramGb: number; os: OperatingSystem }
export type UserProfile = {
  id: string
  name: string
  email: string
  password: string
  genres: string[]
  themes: string[]
  anchorIds: string[]
  hardware: HardwareProfile | null
  catalogVersion?: "steam-v1" | "steam-v2"
}
export type Check = { label: string; ok: boolean | null; detail: string }
export type GameMatch = {
  game: Game
  affinity: number
  reasons: string[]
  checks: Check[]
  compatible: boolean
  compatibility: "compatible" | "incompatible" | "needs_review"
  anchor: boolean
}
export type ProfileStep = { id: string; label: string; hint: string; done: boolean; to: string }
