import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { PageHeader } from "../components/PageHeader"
import { useCatalog } from "../context/CatalogContext"
import { useSession } from "../context/SessionContext"
import { apiError, apiGet } from "../lib/api"
import { Avatar, CHARACTERS, HeartIcon } from "../components/PixelIcons"
import type { AvatarId } from "../types"
import "../styles/results.css"
import type { Interaction } from "../types"

export function Account() {
  const { user, updateUser, changePassword, logout } = useSession()
  const navigate = useNavigate()
  const [name, setName] = useState(user?.name ?? "")
  const [nameNote, setNameNote] = useState<string | null>(null)
  const [passwordNote, setPasswordNote] = useState<string | null>(null)
  const [confirmClear, setConfirmClear] = useState(false)
  const { reactToGame, clearHistory } = useCatalog()
  const [history, setHistory] = useState<Interaction[] | null>(null)
  const [historyNote, setHistoryNote] = useState<string | null>(null)
  const [confirmHistory, setConfirmHistory] = useState(false)
  const [email, setEmail] = useState<string | null>(null)
  const [emailNote, setEmailNote] = useState<string | null>(null)
  const userId = user?.id
  useEffect(() => {
    if (!userId) return
    const controller = new AbortController()
    apiGet<{ items: Interaction[] }>("/me/interactions", controller.signal)
      .then((data) => { if (!controller.signal.aborted) setHistory(data.items) })
      .catch((error) => { if (!controller.signal.aborted) setHistoryNote(apiError(error)) })
    return () => controller.abort()
  }, [userId])
  if (!user) return null
  const reacted = (history ?? []).filter((item) => item.reaction)
  const viewedOnly = (history ?? []).filter((item) => !item.reaction && item.views > 0)

  return (
    <div className="page narrow">
      <PageHeader
        eyebrow="Conta"
        title="Sua conta"
        lede="Nome, senha e perfil de jogo ficam na sua conta e acompanham você em qualquer navegador."
      />
      <div className="account-me">
        <Avatar name={user.name} avatar={user.avatar} />
        <strong>{user.name}</strong>
      </div>

      <section className="panel account-panel">
        <h2>Personagem</h2>
        <p className="hint">Aparece no cabeçalho e fica salvo na sua conta.</p>
        <div className="avatar-picker" role="group" aria-label="Escolha o seu personagem">
          {([null, ...Object.keys(CHARACTERS)] as (AvatarId | null)[]).map((id) => {
            const chosen = (user.avatar ?? null) === id
            return (
              <button key={id ?? "padrao"} type="button" className={chosen ? "avatar-choice on" : "avatar-choice"} aria-pressed={chosen}
                onClick={() => updateUser({ avatar: id })}>
                <Avatar name={user.name} avatar={id} />
                <span>{id ? CHARACTERS[id].name : "Padrão"}</span>
              </button>
            )
          })}
        </div>
      </section>

      <form
        className="panel account-panel"
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
        <p className="hint account-email">
          E-mail da conta:{" "}
          {email ? (
            <>
              <span>{email}</span>{" "}
              <button type="button" className="link-btn" onClick={() => setEmail(null)}>Ocultar</button>
            </>
          ) : (
            <button type="button" className="link-btn" onClick={() => {
              setEmailNote(null)
              apiGet<{ email: string }>("/me/account")
                .then((data) => setEmail(data.email))
                .catch((error) => setEmailNote(apiError(error)))
            }}>
              Mostrar
            </button>
          )}
        </p>
        {emailNote && <p className="hint" role="alert">{emailNote}</p>}
        {nameNote && <p className="hint">{nameNote}</p>}
        <button className="btn" type="submit">
          Salvar nome
        </button>
      </form>

      <form
        className="panel account-panel"
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

      <section className="panel account-panel">
        <h2>Perfil de jogo</h2>
        <p>Limpar remove gêneros, temáticas, jogos âncora e computador. A conta continua existindo.</p>
        {confirmClear ? (
          <div className="row confirm-box">
            <p className="form-error">Tem certeza? Isso não pode ser desfeito.</p>
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

      <section className="panel account-panel">
        <h2>Histórico de jogos</h2>
        <p>
          Guardamos só o código do jogo, se você curtiu ou não, quantas vezes abriu a página dele e as datas. Jogos que
          você não curtiu deixam de ser recomendados; os curtidos reforçam a afinidade das próximas sugestões.
        </p>
        {history === null && !historyNote && <p className="hint" role="status">Carregando o histórico…</p>}
        {history !== null && (
          <p className="hint">{history.length} {history.length === 1 ? "jogo visto" : "jogos vistos"} · {reacted.length} com reação.</p>
        )}
        {reacted.length > 0 && (
          <ul className="plain-list history-list">
            {reacted.map((item) => (
              <li key={item.gameId}>
                <span className="history-game">
                  <span className="history-heart" aria-hidden="true"><HeartIcon broken={item.reaction === "disliked"} filled /></span>
                  <span className="sr-only">{item.reaction === "liked" ? "Curtiu: " : "Não curtiu: "}</span>
                  {item.title ?? `Jogo ${item.gameId}`}
                </span>
                <button type="button" className="btn ghost small" onClick={() => {
                  setHistoryNote(null)
                  reactToGame(item.gameId, null)
                    .then(() => setHistory((current) => (current ?? []).map((entry) => entry.gameId === item.gameId ? { ...entry, reaction: null } : entry)))
                    .catch((error) => setHistoryNote(apiError(error)))
                }}>
                  Remover reação
                </button>
              </li>
            ))}
          </ul>
        )}
        {viewedOnly.length > 0 && (
          <>
            <h3 className="history-sub">Só visualizados</h3>
            <ul className="plain-list history-list">
              {viewedOnly.map((item) => (
                <li key={item.gameId}>
                  <span className="history-game">
                    <span className="history-eye" aria-hidden="true">◉</span>
                    {item.title ?? `Jogo ${item.gameId}`}
                  </span>
                  <span className="hint">{item.views === 1 ? "aberto 1 vez" : `aberto ${item.views} vezes`}</span>
                </li>
              ))}
            </ul>
          </>
        )}
        {historyNote && <p className="hint" role="status">{historyNote}</p>}
        {confirmHistory ? (
          <div className="row confirm-box">
            <p className="form-error">Tem certeza? Isso não pode ser desfeito.</p>
            <button type="button" className="btn danger" onClick={() => {
              clearHistory()
                .then((removed) => { setHistory([]); setHistoryNote(`Histórico removido (${removed} ${removed === 1 ? "registro" : "registros"}).`) })
                .catch((error) => setHistoryNote(apiError(error)))
                .finally(() => setConfirmHistory(false))
            }}>
              Confirmar limpeza do histórico
            </button>
            <button type="button" className="btn ghost" onClick={() => setConfirmHistory(false)}>Cancelar</button>
          </div>
        ) : (
          <button type="button" className="btn ghost" disabled={!history?.length} onClick={() => setConfirmHistory(true)}>
            Limpar histórico de jogos
          </button>
        )}
      </section>

      <button
        type="button"
        className="btn danger"
        onClick={() => {
          navigate("/")
          void logout()
        }}
      >
        Sair da conta
      </button>
    </div>
  )
}
