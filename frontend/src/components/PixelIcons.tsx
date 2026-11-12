import type { ReactNode } from "react"

type Bitmap = { rows: string[]; palette: Record<string, string> }

function PixelBitmap({ rows, palette, size, className }: Bitmap & { size: number; className?: string }) {
  const cells: ReactNode[] = []
  rows.forEach((row, y) => {
    for (let x = 0; x < row.length; x += 1) {
      const color = palette[row[x]]
      if (color) cells.push(<rect key={`${x}-${y}`} x={x} y={y} width={1.03} height={1.03} fill={color} />)
    }
  })
  return (
    <svg className={className} width={size} height={size} viewBox={`0 0 ${rows[0].length} ${rows.length}`} shapeRendering="crispEdges" aria-hidden="true" focusable="false">
      {cells}
    </svg>
  )
}

const COMPASS = [
  "....KK......", "..KKYYKK....", ".KYYYRYYK...", ".KYYYRYYYK..", "KYYYYRYYYYK.", "KYWWWRWWWYK.",
  "KYYYYBYYYYK.", ".KYYYBYYYK..", ".KYYYBYYYK..", "..KKYYYKK...", "....KKKK....", "............",
]

/** Bússola pixel da marca. */
export function CompassIcon({ size = 24, spin = false }: { size?: number; spin?: boolean }) {
  return (
    <span className={spin ? "compass-spin" : undefined} style={{ display: "inline-flex", animation: spin ? "compass 3s steps(8) infinite" : undefined }}>
      <PixelBitmap rows={COMPASS} size={size} palette={{ K: "#000", Y: "#ffd86b", R: "#ff5c6c", B: "#6be1ff", W: "#fff" }} />
    </span>
  )
}

const HEART = [
  "..1111.1111..", ".11111111111.", "1111111111111", "1111111111111", "1111111111111", ".11111111111.",
  "..111111111..", "...1111111...", "....11111....", ".....111.....", "......1......",
]
const CRACK = [6, 6, 7, 5, 7, 5, 6, 5, 6, 6, 6]
const filled = (r: number, c: number) => r >= 0 && c >= 0 && r < HEART.length && c < 13 && HEART[r][c] === "1"

/**
 * Coração pixel. `broken` desenha o coração partido (em zigue-zague). Sem `filled`, só o contorno
 * na cor do texto atual (currentColor), para o CSS cuidar do branco e do amarelo.
 */
export function HeartIcon({ broken = false, filled: solid = false, animate = false }: { broken?: boolean; filled?: boolean; animate?: boolean }) {
  const left: ReactNode[] = []
  const right: ReactNode[] = []
  const whole: ReactNode[] = []
  const solidColor = broken ? "#9b8cc4" : "#ff5c6c"
  for (let r = 0; r < HEART.length; r += 1) {
    for (let c = 0; c < 13; c += 1) {
      if (!filled(r, c)) continue
      const edge = !filled(r - 1, c) || !filled(r + 1, c) || !filled(r, c - 1) || !filled(r, c + 1)
      if (broken) {
        const crack = CRACK[r]
        if (c === crack) continue
        const isLeft = c < crack
        const nearCrack = isLeft ? c === crack - 1 : c === crack + 1
        if (solid || edge || nearCrack) {
          const rect = <rect key={`${r}-${c}`} x={c} y={r} width={1.03} height={1.03} fill={solid ? solidColor : "currentColor"} />
          ;(isLeft ? left : right).push(rect)
        }
      } else if (solid || edge) {
        whole.push(<rect key={`${r}-${c}`} x={c} y={r} width={1.03} height={1.03} fill={solid ? solidColor : "currentColor"} />)
      }
    }
  }
  return (
    <svg viewBox="-1 -1 15 13" shapeRendering="crispEdges" aria-hidden="true" focusable="false">
      {broken ? (
        <>
          <g className={solid && animate ? "heart-l" : undefined}>{left}</g>
          <g className={solid && animate ? "heart-r" : undefined}>{right}</g>
        </>
      ) : (
        <g className={solid && animate ? "heart-pop" : undefined}>{whole}</g>
      )}
    </svg>
  )
}

const AVATAR_COLORS = ["#6be1ff", "#5cff9d", "#ffd86b", "#ff9bb5", "#cbbcff", "#ff7a59"]

/** Personagem pixel padrão; a cor sai do nome, então é estável sem precisar guardar nada. */
export function Avatar({ name }: { name?: string }) {
  let hash = 0
  for (const char of name ?? "") hash = (hash * 31 + char.charCodeAt(0)) % 997
  return <span className="avatar" style={{ background: AVATAR_COLORS[hash % AVATAR_COLORS.length] }} aria-hidden="true" />
}
