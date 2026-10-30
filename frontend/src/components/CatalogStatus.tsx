import { useCatalog } from "../context/CatalogContext"

export function CatalogStatus({ scope = "games" }: { scope?: "games" | "hardware" }) {
  const catalog = useCatalog()
  const loading = scope === "games" ? catalog.gamesLoading : catalog.hardwareLoading
  const error = scope === "games" ? catalog.gamesError : catalog.hardwareError
  if (loading)
    return (
      <p className="hint" role="status">
        {scope === "games" ? "Consultando os jogos selecionados…" : "Carregando CPUs e GPUs…"}
      </p>
    )
  if (error)
    return (
      <div className="banner warn" role="alert">
        <p>{error}</p>
        <button type="button" className="btn ghost small" onClick={catalog.refresh}>
          Tentar novamente
        </button>
      </div>
    )
  return null
}
