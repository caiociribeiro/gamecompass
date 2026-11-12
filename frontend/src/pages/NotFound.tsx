import { Link } from "react-router-dom"
import "../styles/public.css"
import { useTitle } from "../components/PageHeader"

export function NotFound() {
  useTitle("Página não encontrada")
  return (
    <div className="missing">
      <p className="big404" aria-hidden="true">
        404
      </p>
      <h1 className="gameover">
        FIM DE JOGO!
        <br />
        Essa página não existe.
      </h1>
      <Link className="btn" to="/">
        Ir para o início
      </Link>
    </div>
  )
}
