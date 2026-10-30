import { PageHeader } from "../components/PageHeader"
import { useSession } from "../context/SessionContext"
import { GENRES, THEMES } from "../data/preferences"

function toggle(list: string[], value: string) {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value]
}

export function Preferences() {
  const { user, updateUser } = useSession()
  if (!user) return null
  return (
    <div className="page narrow">
      <PageHeader
        eyebrow="Preferências"
        title="O que você procura em um jogo"
        lede="Escolha pelo menos um gênero e uma temática. A escolha é salva na hora, neste navegador."
      />
      <section className="stack">
        <h2>Gêneros</h2>
        <div className="chips">
          {GENRES.map((genre) => (
            <button
              key={genre}
              type="button"
              className={user.genres.includes(genre) ? "chip on" : "chip"}
              aria-pressed={user.genres.includes(genre)}
              onClick={() => updateUser({ genres: toggle(user.genres, genre) })}
            >
              {genre}
            </button>
          ))}
        </div>
        <h2>Temáticas</h2>
        <div className="chips">
          {THEMES.map((theme) => (
            <button
              key={theme}
              type="button"
              className={user.themes.includes(theme) ? "chip on" : "chip"}
              aria-pressed={user.themes.includes(theme)}
              onClick={() => updateUser({ themes: toggle(user.themes, theme) })}
            >
              {theme}
            </button>
          ))}
        </div>
        <p className="hint" aria-live="polite">
          {user.genres.length} gêneros · {user.themes.length} temáticas.
        </p>
        <p className="hint">
          Suas temáticas ficam salvas no perfil. A associação temática dos jogos da Steam ainda será
          preenchida; por enquanto a afinidade considera gêneros e jogos âncora.
        </p>
      </section>
    </div>
  )
}
