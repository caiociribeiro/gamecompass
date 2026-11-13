import type { OPERATING_SYSTEMS, WINDOWS_VERSIONS } from "./data/hardware"

export type OperatingSystem = (typeof OPERATING_SYSTEMS)[number]
export type WindowsVersion = (typeof WINDOWS_VERSIONS)[number]
export type HardwareAlternative = {
  status: "matched" | "not_found"
  component_type: "CPU" | "GPU"
  name: string | null
  performance_score: number | null
  score_version: string | null
  score_status: "classified" | "pending" | "not_found"
}
export type RequirementsBlock = {
  requirements_kind?: "hardware" | "notes_only"
  text: string
  os_text: string | null
  status: "resolved" | "needs_review"
  requirements: { ram_gb: number | null; cpu_score: number | null; gpu_score: number | null }
  issues: string[]
  score_version: string
  curation?: {
    component_type: "CPU" | "GPU"
    method: "manual_reference"
    original_query: string
    reference_models: string[]
    source_url: string
    notes: string
  }[]
  hardware?: Partial<Record<"CPU" | "GPU", {
    query?: string
    alternatives: HardwareAlternative[]
  } | null>>
}
export type Game = {
  id: string
  title: string
  developer: string
  year: number | null
  genres: string[]
  genre_source?: { steam: string[]; editorial: string[]; method: string; notes?: string }
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
export type GameSearchResult = { id: string; title: string; image_url?: string | null }
export type HardwareProfile = {
  cpuId: string
  gpuId: string
  ramGb: number
  os: OperatingSystem
  windowsVersion?: WindowsVersion
}
export type AvatarId = "robo" | "gato" | "fantasma" | "cavaleiro" | "mago" | "alien" | "slime" | "caveira"
export type UserProfile = {
  id: string
  name: string
  genres: string[]
  themes: string[]
  anchorIds: string[]
  hardware: HardwareProfile | null
  /** Personagem escolhido na Conta; null ou ausente usa o avatar padrão. */
  avatar?: AvatarId | null
  /** Só existe em perfis antigos do navegador; a API não usa este campo. */
  catalogVersion?: "steam-v1" | "steam-v2"
}
export type RequirementLevel = "minimum" | "recommended"
export type HardwareSuggestion = {
  name: string
  partId?: string
  detail: string
  alternatives?: { name: string; partId?: string; detail: string }[]
}
export type Check = {
  label: string
  ok: boolean | null
  detail: string
  suggestion?: HardwareSuggestion
  estimated?: boolean
}
export type Compatibility = "compatible" | "incompatible" | "needs_review"
export type HardwareAssessment = {
  available: boolean
  checks: Check[]
  compatibility: Compatibility
}
export type Reaction = "liked" | "disliked"
export type Interaction = {
  gameId: string
  title: string | null
  reaction: Reaction | null
  views: number
  reactedAt: number | null
  firstViewedAt: number | null
  lastViewedAt: number | null
}
export type InteractionSummary = { authenticated: boolean; likedAnchors: string[]; hidden: string[] }
export type GameMatch = {
  game: Game
  reaction?: Reaction | null
  affinity: number
  reasons: string[]
  anchorMatches?: { id: string; title: string; similarity: number; genres: string[]; themes: string[] }[]
  preferredGenres?: string[]
  checks: Check[]
  compatible: boolean
  compatibility: Compatibility
  meets: RequirementLevel | null
  estimated?: boolean
  assessments: Record<RequirementLevel, HardwareAssessment>
  anchor: boolean
}
export type ProfileStep = { id: string; label: string; hint: string; done: boolean; to: string }

export type RecommendationGroups = { items: GameMatch[]; pending: GameMatch[]; excluded: GameMatch[] }
export type CalculationMetadata = {
  engine_version: string
  minimum_affinity: number
  score_version: string
  hardware_sha256: string | null
  curation_sha256: string | null
}
export type RecommendationResult = RecommendationGroups & {
  anchors: Game[]
  issues: { appid: string; message: string }[]
  source: string
  calculation: CalculationMetadata
  interactions?: InteractionSummary
}
export type ComparisonResult = {
  match: GameMatch
  issues: { appid: string; message: string }[]
  calculation: CalculationMetadata
  interactions?: InteractionSummary
}
