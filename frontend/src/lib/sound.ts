// Sons de 8 bits gerados com a Web Audio API (nenhum arquivo de áudio).
// O navegador só libera o áudio depois de um gesto da pessoa; por isso o contexto nasce no primeiro clique.
export type SoundName = "click" | "select" | "back" | "confirm" | "fanfare" | "love" | "break" | "error"

const KEY = "gc_sound"
let ctx: AudioContext | null = null

export function readEnabled(): boolean {
  try {
    return localStorage.getItem(KEY) !== "off"
  } catch {
    return true
  }
}

export function saveEnabled(value: boolean) {
  try {
    localStorage.setItem(KEY, value ? "on" : "off")
  } catch {
    // sem armazenamento: o estado só vale nesta aba
  }
}

export function unlockAudio() {
  if (ctx) {
    if (ctx.state === "suspended") void ctx.resume()
    return
  }
  const Ctor = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
  if (!Ctor) return
  try {
    ctx = new Ctor()
  } catch {
    ctx = null
  }
}

function tone(freq: number, start: number, length: number, type: OscillatorType = "square", volume = 0.05) {
  if (!ctx) return
  const osc = ctx.createOscillator()
  const gain = ctx.createGain()
  osc.type = type
  osc.frequency.setValueAtTime(freq, ctx.currentTime + start)
  gain.gain.setValueAtTime(volume, ctx.currentTime + start)
  gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + start + length)
  osc.connect(gain).connect(ctx.destination)
  osc.start(ctx.currentTime + start)
  osc.stop(ctx.currentTime + start + length + 0.02)
}

const SCORES: Record<SoundName, [number, number, number][]> = {
  click: [[660, 0, 0.05]],
  select: [[880, 0, 0.06], [1320, 0.06, 0.08]],
  back: [[440, 0, 0.06], [330, 0.06, 0.08]],
  confirm: [[523, 0, 0.08], [659, 0.08, 0.08], [784, 0.16, 0.12]],
  fanfare: [[523, 0, 0.12], [659, 0.12, 0.12], [784, 0.24, 0.12], [1046, 0.36, 0.3]],
  love: [[784, 0, 0.08], [1046, 0.08, 0.14]],
  break: [[392, 0, 0.1], [294, 0.1, 0.1], [196, 0.2, 0.2]],
  error: [[196, 0, 0.12], [147, 0.12, 0.18]],
}

export function playSound(name: SoundName) {
  if (!ctx || ctx.state !== "running") return
  for (const [freq, start, length] of SCORES[name]) tone(freq, start, length)
}
