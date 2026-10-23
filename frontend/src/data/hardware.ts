import type { HardwareProfile, Part } from "../types"

export const CPUS: Part[] = [
  { id: "i3-10100", name: "Intel Core i3-10100", vendor: "Intel", score: 7000 },
  { id: "i5-10400f", name: "Intel Core i5-10400F", vendor: "Intel", score: 10000 },
  { id: "i5-12400f", name: "Intel Core i5-12400F", vendor: "Intel", score: 15000 },
  { id: "i7-12700f", name: "Intel Core i7-12700F", vendor: "Intel", score: 20000 },
  { id: "i5-13600k", name: "Intel Core i5-13600K", vendor: "Intel", score: 23000 },
  { id: "i7-14700k", name: "Intel Core i7-14700K", vendor: "Intel", score: 28000 },
  { id: "r5-3600", name: "AMD Ryzen 5 3600", vendor: "AMD", score: 11000 },
  { id: "r5-5600", name: "AMD Ryzen 5 5600", vendor: "AMD", score: 16000 },
  { id: "r7-5700x", name: "AMD Ryzen 7 5700X", vendor: "AMD", score: 19000 },
  { id: "r5-7600", name: "AMD Ryzen 5 7600", vendor: "AMD", score: 20000 },
  { id: "r7-7800x3d", name: "AMD Ryzen 7 7800X3D", vendor: "AMD", score: 26000 },
  { id: "r7-9800x3d", name: "AMD Ryzen 7 9800X3D", vendor: "AMD", score: 30000 },
]

export const GPUS: Part[] = [
  { id: "gtx-1650", name: "NVIDIA GeForce GTX 1650", vendor: "NVIDIA", score: 6000 },
  { id: "gtx-1660s", name: "NVIDIA GeForce GTX 1660 Super", vendor: "NVIDIA", score: 9000 },
  { id: "rtx-2060", name: "NVIDIA GeForce RTX 2060", vendor: "NVIDIA", score: 11000 },
  { id: "rtx-3060", name: "NVIDIA GeForce RTX 3060", vendor: "NVIDIA", score: 15000 },
  { id: "rtx-3070", name: "NVIDIA GeForce RTX 3070", vendor: "NVIDIA", score: 19000 },
  { id: "rtx-4060", name: "NVIDIA GeForce RTX 4060", vendor: "NVIDIA", score: 16000 },
  { id: "rtx-4070", name: "NVIDIA GeForce RTX 4070", vendor: "NVIDIA", score: 23000 },
  { id: "rtx-4080", name: "NVIDIA GeForce RTX 4080", vendor: "NVIDIA", score: 30000 },
  { id: "rx-580", name: "AMD Radeon RX 580", vendor: "AMD", score: 5000 },
  { id: "rx-6600", name: "AMD Radeon RX 6600", vendor: "AMD", score: 13000 },
  { id: "rx-6700xt", name: "AMD Radeon RX 6700 XT", vendor: "AMD", score: 18000 },
  { id: "rx-7800xt", name: "AMD Radeon RX 7800 XT", vendor: "AMD", score: 24000 },
]

export const RAM_OPTIONS = [4, 8, 16, 32, 64]

export function findCpu(id: string) {
  return CPUS.find((part) => part.id === id)
}

export function findGpu(id: string) {
  return GPUS.find((part) => part.id === id)
}

export function machineTier(cpuScore: number, gpuScore: number) {
  const limit = Math.min(cpuScore, gpuScore)
  if (limit < 9000) return "entrada"
  if (limit < 16000) return "intermediário"
  if (limit < 24000) return "alto"
  return "topo de linha"
}

export function hardwareSummary(hardware: HardwareProfile | null) {
  if (!hardware) return null
  const cpu = findCpu(hardware.cpuId)
  const gpu = findGpu(hardware.gpuId)
  if (!cpu || !gpu) return null
  const tier = machineTier(cpu.score, gpu.score)
  return {
    cpu,
    gpu,
    tier,
    text: `${cpu.name}, ${gpu.name}, ${hardware.ramGb} GB de RAM, ${hardware.os}. Faixa estimada: ${tier}.`,
  }
}
