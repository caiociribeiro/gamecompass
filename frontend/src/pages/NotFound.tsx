import { Link } from "react-router-dom"
import { useTitle } from "../components/PageHeader"

export function NotFound() {
  useTitle("Página não encontrada")
  return (
    <div className="missing">
      <p className="eyebrow">404</p>
      <h1>Essa página não existe.</h1>
      <Link className="btn" to="/">
        Ir para o início
      </Link>
    </div>
  )
}
