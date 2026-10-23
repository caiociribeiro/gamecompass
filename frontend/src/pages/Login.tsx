import { Link } from "react-router-dom"
import { AuthFrame, FormError, useField } from "../components/AuthFrame"
import { useTitle } from "../components/PageHeader"
import { useSession } from "../context/SessionContext"
import { DEMO_EMAIL, DEMO_PASSWORD } from "../data/demo"

export function Login() {
  useTitle("Entrar")
  const { login } = useSession()
  const { error, onSubmit } = useField()

  return (
    <AuthFrame
      title="Entrar"
      lede="Use a conta de demonstração ou uma conta criada neste navegador."
    >
      <form
        className="stack"
        onSubmit={(event) => {
          const data = new FormData(event.currentTarget)
          onSubmit(event, () => login(String(data.get("email") ?? ""), String(data.get("password") ?? "")))
        }}
      >
        <label>
          E-mail
          <input name="email" type="email" autoComplete="username" defaultValue={DEMO_EMAIL} required />
        </label>
        <label>
          Senha
          <input name="password" type="password" autoComplete="current-password" defaultValue={DEMO_PASSWORD} required />
        </label>
        <FormError message={error} />
        <button className="btn" type="submit">
          Entrar
        </button>
      </form>
      <p className="form-links">
        <Link to="/recuperar">Esqueci a senha</Link>
        <Link to="/cadastro">Criar conta</Link>
      </p>
      <p className="hint">
        Demonstração: {DEMO_EMAIL} · senha {DEMO_PASSWORD}
      </p>
    </AuthFrame>
  )
}
