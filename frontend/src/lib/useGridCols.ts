import { useCallback, useEffect, useState } from "react"

const GAP = 16

/** Escolhe quantas colunas cabem (cartões de 240 a 360px), preferindo completar a última linha. */
export function fitColumns(width: number, count: number) {
  const maxC = Math.max(2, Math.floor((width + GAP) / (240 + GAP)))
  const minC = Math.max(2, Math.min(maxC, Math.ceil((width + GAP) / (360 + GAP))))
  let best = maxC
  let bestScore = -1
  for (let c = maxC; c >= minC; c -= 1) {
    const rest = count % c
    const fill = count <= c ? count / c : rest === 0 ? 1 : (rest / c) * 0.5 + 0.5
    const score = fill * 1000 + c
    if (score > bestScore) {
      bestScore = score
      best = c
    }
  }
  return count && count < minC ? Math.max(count, 2) : best
}

/** Ref callback para uma .card-grid: mede a largura e define --cols. */
export function useGridCols(count: number) {
  const [node, setNode] = useState<HTMLElement | null>(null)
  const ref = useCallback((element: HTMLElement | null) => setNode(element), [])
  useEffect(() => {
    if (!node) return
    const apply = () => node.style.setProperty("--cols", String(fitColumns(node.clientWidth, count)))
    apply()
    if (typeof ResizeObserver === "undefined") return
    const observer = new ResizeObserver(apply)
    observer.observe(node)
    return () => observer.disconnect()
  }, [node, count])
  return ref
}
