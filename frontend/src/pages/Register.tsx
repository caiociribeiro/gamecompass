import { Link } from "react-router-dom"
import { AuthFrame, FormError, useField } from "../components/AuthFrame"
import { useTitle } from "../components/PageHeader"
import { useSession } from "../context/SessionContext"

export function Register() {
  useTitle("Criar conta")
  const { register } = useSession()
  const { error, onSubmit } = useField()

  return (
    <AuthFrame
      title="Criar conta"
      lede="A conta abre o cadastro de gosto, jogos âncora e hardware."
    >
      <form
        className="stack"
        onSubmit={(event) => {
          const data = new FormData(event.currentTarget)
          const password = String(data.get("password") ?? "")
          const confirm = String(data.get("confirm") ?? "")
          onSubmit(event, () => {
            if (password !== confirm) return "A confirmação da senha não confere."
            return register({
              name: String(data.get("name") ?? ""),
              email: String(data.get("email") ?? ""),
              password,
            })
          })
        }}
      >
        <label>
          Nome
          <input name="name" autoComplete="name" required />
        </label>
        <label>
          E-mail
          <input name="email" type="email" autoComplete="email" required />
        </label>
        <label>
          Senha
          <input name="password" type="password" autoComplete="new-password" minLength={6} required />
        </label>
        <label>
          Confirmar senha
          <input name="confirm" type="password" autoComplete="new-password" minLength={6} required />
        </label>
        <FormError message={error} />
        <button className="btn" type="submit">
          Criar conta
        </button>
      </form>
      <p className="form-links">
        <Link to="/entrar">Já tenho conta</Link>
      </p>
    </AuthFrame>
  )
}
