import type { HardwareProfile, UserProfile } from "../types"

const names = (values: string[]) => [...new Set(values.map((v) => v.trim()).filter(Boolean))].sort()
export type CalculationProfile = {
  anchorIds: string[]
  genres: string[]
  themes: string[]
  hardware: HardwareProfile | null
}

export function calculationProfile(user: UserProfile | null): CalculationProfile {
  const part = user?.hardware
  return {
    anchorIds: names(user?.anchorIds ?? []).filter((id) => /^[1-9][0-9]{0,9}$/.test(id)).slice(0, 3),
    genres: names(user?.genres ?? []), themes: names(user?.themes ?? []),
    hardware: part ? { cpuId: part.cpuId, gpuId: part.gpuId, ramGb: part.ramGb, os: part.os,
      ...(part.os === "Windows" ? { windowsVersion: part.windowsVersion } : {}) } : null,
  }
}
