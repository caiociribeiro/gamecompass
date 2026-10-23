import { GENRES, THEMES } from "../data/catalog"
import { PageHeader } from "../components/PageHeader"
import { useSession } from "../context/SessionContext"

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
          {GENRES.map((genre) => {
            const on = user.genres.includes(genre)
            return (
              <button
                key={genre}
                type="button"
                className={on ? "chip on" : "chip"}
                aria-pressed={on}
                onClick={() => updateUser({ genres: toggle(user.genres, genre) })}
              >
                {genre}
              </button>
            )
          })}
        </div>
        <h2>Temáticas</h2>
        <div className="chips">
          {THEMES.map((theme) => {
            const on = user.themes.includes(theme)
            return (
              <button
                key={theme}
                type="button"
                className={on ? "chip on" : "chip"}
                aria-pressed={on}
                onClick={() => updateUser({ themes: toggle(user.themes, theme) })}
              >
                {theme}
              </button>
            )
          })}
        </div>
        <p className="hint" aria-live="polite">
          {user.genres.length} {user.genres.length === 1 ? "gênero" : "gêneros"} · {user.themes.length}{" "}
          {user.themes.length === 1 ? "temática" : "temáticas"}
        </p>
      </section>
    </div>
  )
}
