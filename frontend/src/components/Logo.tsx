import { CompassIcon } from "./PixelIcons"

export function Logo({ size = 22 }: { size?: number }) {
  return (
    <span className="logo">
      <CompassIcon size={size} />
      GameCompass
    </span>
  )
}
