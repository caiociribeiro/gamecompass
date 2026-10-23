import { useState } from "react"
import { Link } from "react-router-dom"
import { AuthFrame } from "../components/AuthFrame"
import { useTitle } from "../components/PageHeader"
import { DEMO_EMAIL, DEMO_PASSWORD } from "../data/demo"

const USERS_KEY = "gamecompass.users.v1"

export function Recover() {
  useTitle("Recuperar senha")
  const [message, setMessage] = useState<string | null>(null)

  return (
    <AuthFrame
      title="Recuperar senha"
      lede="Informe o e-mail da conta para localizá-la."
    >
      <form
        className="stack"
        onSubmit={(event) => {
          event.preventDefault()
          const email = String(new FormData(event.currentTarget).get("email") ?? "")
            .trim()
            .toLowerCase()
          let found = false
          try {
            const raw = localStorage.getItem(USERS_KEY)
            const users = raw ? (JSON.parse(raw) as { email?: string }[]) : []
            found = Array.isArray(users) && users.some((user) => user.email === email)
          } catch {
            found = false
          }
          if (!found) {
            setMessage("Não encontramos essa conta neste navegador.")
            return
          }
          if (email === DEMO_EMAIL) {
            setMessage(`A conta de demonstração usa a senha ${DEMO_PASSWORD}, se ela não tiver sido alterada.`)
            return
          }
          setMessage("A conta existe neste navegador. Como não há servidor, a senha não pode ser redefinida por e-mail. Entre com a senha que você escolheu ou crie outra conta.")
        }}
      >
        <label>
          E-mail
          <input name="email" type="email" required />
        </label>
        {message && <p className="hint">{message}</p>}
        <button className="btn" type="submit">
          Procurar conta
        </button>
      </form>
      <p className="form-links">
        <Link to="/entrar">Voltar ao login</Link>
      </p>
    </AuthFrame>
  )
}
