import type { ReactNode } from "react"
import type { AvatarId } from "../types"

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

/** Personagens que a pessoa pode escolher na Conta (12×12 pixels; K é o contorno). */
export const CHARACTERS: Record<AvatarId, { name: string; rows: string[]; palette: Record<string, string> }> = {
  robo: { name: "Robô", palette: { K: "#000", G: "#9aa7c7", C: "#6be1ff", R: "#ff5c6c" }, rows: [
    ".....RR.....", ".....KK.....", "..KKKKKKKK..", "..KGGGGGGK..", "..KGCCGCCK..", "..KGCCGCCK..",
    "..KGGGGGGK..", "..KGKKKKGK..", "..KGGGGGGK..", "..KKKKKKKK..", "...KGK.KGK..", "...KKK.KKK.."] },
  gato: { name: "Gato", palette: { K: "#000", O: "#ff9f43", P: "#ff9bb5", W: "#fff3b0" }, rows: [
    "..K......K..", ".KOK....KOK.", ".KOOKKKKOOK.", ".KOOOOOOOOK.", "KOOKOOOOKOOK", "KOOKOOOOKOOK",
    "KOOOOPPOOOOK", "KWOOKOOKOOWK", ".KOOOKKOOOK.", "..KKOOOOKK..", "....KKKK....", "............"] },
  fantasma: { name: "Fantasma", palette: { K: "#000", W: "#f2f2ff", B: "#6b5cff" }, rows: [
    "....KKKK....", "..KKWWWWKK..", ".KWWWWWWWWK.", ".KWWBWWBWWK.", "KWWWBWWBWWWK", "KWWWWWWWWWWK",
    "KWWWWKKWWWWK", "KWWWWWWWWWWK", "KWWWWWWWWWWK", "KWWKWWWKWWWK", "KWK.KWK.KWK.", ".K...K...K.."] },
  cavaleiro: { name: "Cavaleiro", palette: { K: "#000", S: "#c0c6d8", D: "#4a5068", Y: "#ff5c6c" }, rows: [
    ".....YY.....", "....YYYY....", "...KKKKKK...", "..KSSSSSSK..", ".KSSSSSSSSK.", ".KSDDDDDDSK.",
    ".KSSSSSSSSK.", ".KSSSSSSSSK.", ".KSDSDSDSSK.", "..KSSSSSSK..", "...KKKKKK...", "............"] },
  mago: { name: "Mago", palette: { K: "#000", P: "#7b4dff", Y: "#ffd86b", F: "#ffcf9f", W: "#f2f2ff" }, rows: [
    ".....KK.....", "....KPPK....", "...KPPYPK...", "..KPPPPPPK..", ".KKKKKKKKKK.", "..KFFFFFFK..",
    "..KFKFFKFK..", "..KWWWWWWK..", "..KWWWWWWK..", "...KWWWWK...", "....KWWK....", ".....KK....."] },
  alien: { name: "Alien", palette: { K: "#000", G: "#5cff9d" }, rows: [
    "............", "..KKKKKKKK..", ".KGGGGGGGGK.", "KGGGGGGGGGGK", "KGKKKGGKKKGK", "KGKKKGGKKKGK",
    "KGGKGGGGKGGK", "KGGGGGGGGGGK", ".KGGGKKGGGK.", "..KGGGGGGK..", "...KKKKKK...", "............"] },
  slime: { name: "Slime", palette: { K: "#000", B: "#6be1ff", L: "#d8f8ff" }, rows: [
    "............", "............", ".....KK.....", "....KBBK....", "...KBLBBK...", "..KBLBBBBK..",
    ".KBBBBBBBBK.", ".KBKBBBBKBK.", "KBBKBBBBKBBK", "KBBBBKKBBBBK", "KBBBBBBBBBBK", ".KKKKKKKKKK."] },
  caveira: { name: "Caveira", palette: { K: "#000", W: "#f2f2ff" }, rows: [
    "...KKKKKK...", "..KWWWWWWK..", ".KWWWWWWWWK.", ".KWWWWWWWWK.", ".KWKKWWKKWK.", ".KWKKWWKKWK.",
    ".KWWWWKWWWK.", "..KWWWWWWK..", "...KWKWKWK..", "...KWKWKWK..", "....KKKKK...", "............"] },
}

/** Avatar da conta: o personagem escolhido, ou o rosto padrão com a cor tirada do nome. */
export function Avatar({ name, avatar }: { name?: string; avatar?: AvatarId | null }) {
  const character = avatar ? CHARACTERS[avatar] : undefined
  if (character) {
    return (
      <span className="avatar character" aria-hidden="true">
        <PixelBitmap rows={character.rows} palette={character.palette} size={22} />
      </span>
    )
  }
  let hash = 0
  for (const char of name ?? "") hash = (hash * 31 + char.charCodeAt(0)) % 997
  return <span className="avatar" style={{ background: AVATAR_COLORS[hash % AVATAR_COLORS.length] }} aria-hidden="true" />
}
