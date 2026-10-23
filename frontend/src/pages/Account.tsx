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
        title="Sua conta neste navegador"
        lede="Nome, senha e perfil ficam no localStorage. Trocar de computador ou limpar o navegador apaga tudo."
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
        onSubmit={(event) => {
          event.preventDefault()
          const data = new FormData(event.currentTarget)
          const message = changePassword(String(data.get("current") ?? ""), String(data.get("next") ?? ""))
          setPasswordNote(message ?? "Senha alterada neste navegador.")
          if (!message) event.currentTarget.reset()
        }}
      >
        <h2>Senha</h2>
        <label>
          Senha atual
          <input name="current" type="password" autoComplete="current-password" required />
        </label>
        <label>
          Nova senha
          <input name="next" type="password" autoComplete="new-password" minLength={6} required />
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
          logout()
          navigate("/entrar")
        }}
      >
        Sair da conta
      </button>
    </div>
  )
}
