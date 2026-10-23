export const OPERATING_SYSTEMS = ["Windows", "Linux", "macOS"] as const

export type OperatingSystem = (typeof OPERATING_SYSTEMS)[number]

export type Game = {
  id: string
  title: string
  developer: string
  year: number
  genres: string[]
  themes: string[]
  summary: string
  minCpu: number
  minGpu: number
  minRam: number
  systems: OperatingSystem[]
}

export type Part = {
  id: string
  name: string
  vendor: string
  score: number
}

export type HardwareProfile = {
  cpuId: string
  gpuId: string
  ramGb: number
  os: OperatingSystem
}

export type UserProfile = {
  id: string
  name: string
  email: string
  password: string
  genres: string[]
  themes: string[]
  anchorIds: string[]
  hardware: HardwareProfile | null
}

export type Check = {
  label: string
  ok: boolean
  detail: string
}

export type GameMatch = {
  game: Game
  affinity: number
  reasons: string[]
  checks: Check[]
  compatible: boolean
  anchor: boolean
}

export type ProfileStep = {
  id: string
  label: string
  hint: string
  done: boolean
  to: string
}
