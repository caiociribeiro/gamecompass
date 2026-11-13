import { useEffect, useState } from "react"

/** Fatia uma lista em páginas. Volta para a primeira página quando `resetKey` muda (filtro, busca). */
export function usePage<T>(list: T[], size: number, resetKey: string) {
  const [page, setPage] = useState(0)
  useEffect(() => setPage(0), [resetKey])
  const pages = Math.max(1, Math.ceil(list.length / size))
  const current = Math.min(page, pages - 1)
  return { items: list.slice(current * size, current * size + size), page: current, pages, setPage }
}

/** Controles de página: ◀, números e ▶. Some quando há uma página só. */
export function Pager({ page, pages, onChange, label }: { page: number; pages: number; onChange: (page: number) => void; label: string }) {
  if (pages <= 1) return null
  const go = (next: number) => {
    onChange(next)
    // Leva o topo da seção de volta à vista, sem pular a página inteira.
    requestAnimationFrame(() => document.getElementById(`pager-${label}`)?.scrollIntoView({ block: "start", behavior: "smooth" }))
  }
  return (
    <nav className="pager" aria-label={`Páginas de ${label}`}>
      <button type="button" className="chip" disabled={page === 0} onClick={() => go(page - 1)} aria-label="Página anterior">◀</button>
      {Array.from({ length: pages }, (_, index) => (
        <button key={index} type="button" className={`chip${index === page ? " on" : ""}`} aria-current={index === page ? "page" : undefined}
          aria-label={`Página ${index + 1}`} onClick={() => go(index)}>
          {index + 1}
        </button>
      ))}
      <button type="button" className="chip" disabled={page === pages - 1} onClick={() => go(page + 1)} aria-label="Próxima página">▶</button>
    </nav>
  )
}
