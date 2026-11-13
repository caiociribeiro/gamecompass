import { useEffect, useId, useRef, useState } from "react"
import { searchRanked } from "../lib/hardwareRank"
import "../styles/results.css"

type Option = {
  id: string
  label: string
  hint?: string
}

export function SearchSelect({
  label,
  options,
  value,
  onChange,
  placeholder,
  empty,
  disabled = false,
  topLabel,
}: {
  label: string
  options: Option[]
  value: string
  onChange: (id: string) => void
  placeholder: string
  empty: string
  disabled?: boolean
  /** Título da lista quando nada foi digitado (ex.: "Mais usadas na Steam"). */
  topLabel?: string
}) {
  const [query, setQuery] = useState("")
  const [open, setOpen] = useState(false)
  const box = useRef<HTMLDivElement>(null)
  const listId = useId()
  const inputId = useId()
  const selected = options.find((option) => option.id === value) ?? null
  const filtered = searchRanked(options, query)

  useEffect(() => {
    function onDoc(event: MouseEvent) {
      if (!box.current?.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", onDoc)
    return () => document.removeEventListener("mousedown", onDoc)
  }, [])

  return (
    <div className="search-select" ref={box}>
      <label className="field-label" htmlFor={inputId}>
        {label}
      </label>
      {selected ? (
        <div className="picked">
          <div>
            <strong>{selected.label}</strong>
            {selected.hint && <span>{selected.hint}</span>}
          </div>
          <button type="button" className="picked-x" aria-label="Trocar" title="Trocar" disabled={disabled} onClick={() => onChange("")}>
            <span aria-hidden="true">✕</span>
          </button>
        </div>
      ) : (
        <>
          <input
            id={inputId}
            role="combobox"
            aria-autocomplete="list"
            disabled={disabled}
            value={query}
            placeholder={placeholder}
            aria-expanded={open && !disabled}
            aria-controls={listId}
            onChange={(event) => {
              setQuery(event.target.value)
              setOpen(true)
            }}
            onFocus={() => setOpen(true)}
            onKeyDown={(event) => {
              if (event.key === "Escape") setOpen(false)
              if (event.key === "Enter" && filtered[0]) {
                event.preventDefault()
                onChange(filtered[0].id)
                setQuery("")
                setOpen(false)
              }
            }}
          />
          {open && !disabled && (
            <ul id={listId} role="listbox">
              {!query.trim() && topLabel && filtered.length > 0 && <li className="list-head" role="presentation">{topLabel}</li>}
              {filtered.length === 0 && <li className="muted">{empty}</li>}
              {filtered.map((option) => (
                <li key={option.id}>
                  <button
                    type="button"
                    role="option"
                    aria-selected={false}
                    onClick={() => {
                      onChange(option.id)
                      setQuery("")
                      setOpen(false)
                    }}
                  >
                    <strong>{option.label}</strong>
                    {option.hint && <span>{option.hint}</span>}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  )
}
