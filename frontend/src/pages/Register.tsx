import { Link } from "react-router-dom"
import { AuthFrame, FormError, useField } from "../components/AuthFrame"
import { useTitle } from "../components/PageHeader"
import { useSession } from "../context/SessionContext"

export function Register() {
  useTitle("Criar conta")
  const { register } = useSession()
  const { error, pending, onSubmit } = useField()

  return (
    <AuthFrame
      title="Criar conta"
      lede="A conta guarda seu gosto, jogos âncora e hardware para você usar em qualquer navegador."
    >
      <form
        className="stack"
        onSubmit={(event) => {
          const data = new FormData(event.currentTarget)
          const password = String(data.get("password") ?? "")
          const confirm = String(data.get("confirm") ?? "")
          void onSubmit(event, () => {
            if (password !== confirm) return Promise.resolve("A confirmação da senha não confere.")
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
          <input name="password" type="password" autoComplete="new-password" minLength={8} maxLength={128} required />
        </label>
        <label>
          Confirmar senha
          <input name="confirm" type="password" autoComplete="new-password" minLength={8} maxLength={128} required />
        </label>
        <FormError message={error} />
        <p className="hint">Use pelo menos 8 caracteres.</p>
        <button className="btn" type="submit" disabled={pending}>
          {pending ? "Criando…" : "Criar conta"}
        </button>
      </form>
      <p className="form-links">
        <Link to="/entrar">Já tenho conta</Link>
      </p>
    </AuthFrame>
  )
}
