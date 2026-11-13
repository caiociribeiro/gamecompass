import { useCallback, useEffect, useState } from "react"

const GAP = 16
const MIN_CARD = 320

/** Quantos cartões cabem lado a lado numa largura. */
export function cardsPerRow(width: number) {
  return Math.max(1, Math.floor((width + GAP) / (MIN_CARD + GAP)))
}

/** Mede a largura de um elemento e devolve quantos cartões cabem por linha (0 antes de medir). */
export function usePerRow() {
  const [node, setNode] = useState<HTMLElement | null>(null)
  const [perRow, setPerRow] = useState(0)
  const ref = useCallback((element: HTMLElement | null) => setNode(element), [])
  useEffect(() => {
    if (!node) return
    const apply = () => setPerRow(cardsPerRow(node.clientWidth))
    apply()
    if (typeof ResizeObserver === "undefined") return
    const observer = new ResizeObserver(apply)
    observer.observe(node)
    return () => observer.disconnect()
  }, [node])
  return { ref, perRow }
}

/** Escolhe quantas colunas cabem (cartões de 320 a 440px), preferindo completar a última linha. */
export function fitColumns(width: number, count: number, fill = false) {
  const maxC = cardsPerRow(width)
  const minC = Math.max(1, Math.min(maxC, Math.ceil((width + GAP) / (440 + GAP))))
  let best = maxC
  let bestScore = -1
  for (let c = maxC; c >= minC; c -= 1) {
    const rest = count % c
    const filled = count <= c ? count / c : rest === 0 ? 1 : (rest / c) * 0.5 + 0.5
    const score = filled * 1000 + c
    if (score > bestScore) {
      bestScore = score
      best = c
    }
  }
  // Poucos cartões: `fill` estica para ocupar a linha (âncoras do Início); sem ele, mantêm o tamanho normal.
  return count && count < minC ? (fill ? Math.max(count, 2) : minC) : best
}

/** Ref callback para uma .card-grid: mede a largura e define --cols. */
export function useGridCols(count: number, fill = false) {
  const [node, setNode] = useState<HTMLElement | null>(null)
  const ref = useCallback((element: HTMLElement | null) => setNode(element), [])
  useEffect(() => {
    if (!node) return
    const apply = () => node.style.setProperty("--cols", String(fitColumns(node.clientWidth, count, fill)))
    apply()
    if (typeof ResizeObserver === "undefined") return
    const observer = new ResizeObserver(apply)
    observer.observe(node)
    return () => observer.disconnect()
  }, [node, count, fill])
  return ref
}
