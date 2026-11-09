import { PageHeader } from "../components/PageHeader"
import { StepFooter } from "../components/StepFooter"
import { StepNav } from "../components/StepNav"
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
      <StepNav current="prefs" />
      <PageHeader
        eyebrow="Preferências"
        title="O que você procura em um jogo"
        lede="Escolha pelo menos um gênero e uma temática. Cada clique é salvo na sua conta na hora, sem precisar de botão de salvar."
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
        <p className="hint">
          As temáticas dos jogos catalogados são classificadas pelo GameCompass e participam da
          afinidade. Jogos consultados fora desse catálogo podem ter essa classificação pendente.
        </p>
      </section>
      <StepFooter id="prefs" />
    </div>
  )
}
