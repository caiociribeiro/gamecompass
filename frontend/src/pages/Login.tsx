import { Link } from "react-router-dom"
import { AuthFrame, FormError, useField } from "../components/AuthFrame"
import { useTitle } from "../components/PageHeader"
import { useSession } from "../context/SessionContext"

export function Login() {
  useTitle("Entrar")
  const { login, error: sessionError } = useSession()
  const { error, pending, onSubmit } = useField()

  return (
    <AuthFrame
      title="Entrar"
      lede="Entre para recuperar suas preferências, jogos âncora e computador salvos."
    >
      <form
        className="stack"
        onSubmit={(event) => {
          const data = new FormData(event.currentTarget)
          void onSubmit(event, () => login(String(data.get("email") ?? ""), String(data.get("password") ?? "")))
        }}
      >
        <label>
          E-mail
          <input name="email" type="email" autoComplete="username" required />
        </label>
        <label>
          Senha
          <input name="password" type="password" autoComplete="current-password" required />
        </label>
        <FormError message={error ?? sessionError} />
        <button className="btn" type="submit" disabled={pending}>
          {pending ? "Entrando…" : "Entrar"}
        </button>
      </form>
      <p className="form-links">
        <Link to="/recuperar">Esqueci a senha</Link>
        <Link to="/cadastro">Criar conta</Link>
      </p>
    </AuthFrame>
  )
}
