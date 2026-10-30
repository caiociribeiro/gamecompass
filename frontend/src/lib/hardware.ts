import type { HardwareCatalog, HardwareProfile, Part } from "../types"

export function findPart(parts: Part[], id: string) {
  return parts.find((part) => part.id === id)
}
export function hardwareSummary(profile: HardwareProfile | null, catalog: HardwareCatalog) {
  if (!profile) return null
  const cpu = findPart(catalog.CPU, profile.cpuId)
  const gpu = findPart(catalog.GPU, profile.gpuId)
  if (!cpu || !gpu) return null
  return { cpu, gpu, text: `${cpu.name}, ${gpu.name}, ${profile.ramGb} GB de RAM, ${profile.os}.` }
}
