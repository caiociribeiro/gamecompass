import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { PageHeader } from "../components/PageHeader"
import { useSession } from "../context/SessionContext"

export function Account() {
  const { user, updateUser, changePassword, logout } = useSession()
  const navigate = useNavigate()
  const [name, setName] = useState(user?.name ?? "")
  const [nameNote, setNameNote] = useState<string | null>(null)
  const [passwordNote, setPasswordNote] = useState<string | null>(null)
  const [confirmClear, setConfirmClear] = useState(false)
  if (!user) return null

  return (
    <div className="page narrow">
      <PageHeader
        eyebrow="Conta"
        title="Sua conta"
        lede="Nome, senha e perfil de jogo ficam na sua conta e acompanham você em qualquer navegador."
      />

      <form
        className="stack card-block"
        onSubmit={(event) => {
          event.preventDefault()
          const next = name.trim()
          if (next.length < 2) {
            setNameNote("O nome precisa ter pelo menos 2 caracteres.")
            return
          }
          updateUser({ name: next })
          setNameNote("Nome salvo.")
        }}
      >
        <h2>Nome</h2>
        <label>
          Como quer ser chamado
          <input value={name} onChange={(event) => setName(event.target.value)} />
        </label>
        <p className="hint">E-mail da conta: {user.email}</p>
        {nameNote && <p className="hint">{nameNote}</p>}
        <button className="btn" type="submit">
          Salvar nome
        </button>
      </form>

      <form
        className="stack card-block"
        onSubmit={async (event) => {
          event.preventDefault()
          const form = event.currentTarget
          const data = new FormData(form)
          const message = await changePassword(String(data.get("current") ?? ""), String(data.get("next") ?? ""))
          setPasswordNote(message ?? "Senha alterada. As demais sessões desta conta foram encerradas.")
          if (!message) form.reset()
        }}
      >
        <h2>Senha</h2>
        <label>
          Senha atual
          <input name="current" type="password" autoComplete="current-password" required />
        </label>
        <label>
          Nova senha
          <input name="next" type="password" autoComplete="new-password" minLength={8} maxLength={128} required />
        </label>
        {passwordNote && <p className="hint">{passwordNote}</p>}
        <button className="btn" type="submit">
          Alterar senha
        </button>
      </form>

      <section className="stack card-block">
        <h2>Perfil de jogo</h2>
        <p>Limpar remove gêneros, temáticas, jogos âncora e computador. A conta continua existindo.</p>
        {confirmClear ? (
          <div className="row">
            <button
              type="button"
              className="btn danger"
              onClick={() => {
                updateUser({ genres: [], themes: [], anchorIds: [], hardware: null })
                setConfirmClear(false)
              }}
            >
              Confirmar limpeza
            </button>
            <button type="button" className="btn ghost" onClick={() => setConfirmClear(false)}>
              Cancelar
            </button>
          </div>
        ) : (
          <button type="button" className="btn ghost" onClick={() => setConfirmClear(true)}>
            Limpar perfil
          </button>
        )}
      </section>

      <button
        type="button"
        className="btn ghost"
        onClick={() => {
          void logout()
          navigate("/entrar")
        }}
      >
        Sair da conta
      </button>
    </div>
  )
}
