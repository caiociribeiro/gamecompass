export function Logo({ size = 28 }: { size?: number }) {
  return (
    <span className="logo">
      <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
        <circle cx="16" cy="16" r="11.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
        <path d="M16 5.2 18.7 16.2 16 14.1 13.3 16.2Z" fill="currentColor" />
        <path d="M16 26.8 13.3 15.8 16 17.9 18.7 15.8Z" fill="currentColor" opacity="0.35" />
      </svg>
      GameCompass
    </span>
  )
}
