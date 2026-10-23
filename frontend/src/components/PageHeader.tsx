import { useEffect, type ReactNode } from "react"

export function useTitle(title: string) {
  useEffect(() => {
    document.title = title === "GameCompass" ? title : `${title} · GameCompass`
  }, [title])
}

export function PageHeader({
  eyebrow,
  title,
  lede,
  children,
}: {
  eyebrow?: string
  title: string
  lede?: string
  children?: ReactNode
}) {
  useTitle(title)
  return (
    <header className="page-header">
      {eyebrow && <p className="eyebrow">{eyebrow}</p>}
      <h1>{title}</h1>
      {lede && <p className="lede">{lede}</p>}
      {children}
    </header>
  )
}
