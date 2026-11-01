import { useMemo, useState } from "react"
import { useSession } from "../context/SessionContext"
import { discardLegacyAccount, readLegacyChoices } from "../lib/legacyProfile"

/**
 * Migração explícita: oferece copiar para a conta as escolhas que a versão antiga guardou
 * neste navegador, só quando o perfil do servidor ainda está vazio. A senha antiga é ignorada.
 */
export function LegacyImportNotice() {
  const { user, updateUser } = useSession()
  const [hidden, setHidden] = useState(false)
  const empty = Boolean(user && !user.genres.length && !user.themes.length && !user.anchorIds.length && !user.hardware)
  const choices = useMemo(() => (user && empty ? readLegacyChoices(user.email) : null), [user?.id, empty])
  if (!user || !choices || hidden) return null
  const parts = [
    choices.genres.length || choices.themes.length ? "preferências" : null,
    choices.anchorIds.length ? "jogos âncora" : null,
    choices.hardware ? "computador" : null,
  ].filter(Boolean)

  return (
    <section className="stack card-block" role="status">
      <h2>Importar escolhas deste navegador?</h2>
      <p>
        Encontramos {parts.join(", ")} salvos aqui para {user.email}, de antes das contas no servidor. Importar copia essas
        escolhas para a sua conta. A senha antiga não é usada nem enviada.
      </p>
      <div className="row">
        <button
          type="button"
          className="btn"
          onClick={() => {
            updateUser(choices)
            discardLegacyAccount(user.email)
            setHidden(true)
          }}
        >
          Importar escolhas
        </button>
        <button type="button" className="btn ghost" onClick={() => setHidden(true)}>
          Agora não
        </button>
      </div>
    </section>
  )
}
