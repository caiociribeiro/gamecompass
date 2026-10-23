import { Link } from "react-router-dom"
import { GameCard } from "../components/GameCard"
import { Logo } from "../components/Logo"
import { useTitle } from "../components/PageHeader"
import { useSession } from "../context/SessionContext"
import { DEMO_USER } from "../data/demo"
import { buildRecommendations } from "../lib/recommend"

const STEPS = [
  { n: "01", title: "O gosto", text: "Gêneros e temáticas dizem o tipo de experiência, não só a prateleira da loja." },
  { n: "02", title: "Três âncoras", text: "Três jogos que você já aprovou puxam títulos parecidos no catálogo." },
  { n: "03", title: "O computador", text: "Processador, placa, memória e sistema viram um limite concreto." },
  { n: "04", title: "A lista", text: "Entra quem combina com o perfil e cabe no hardware. O resto fica de fora." },
]

export function Landing() {
  useTitle("GameCompass")
  const { user } = useSession()
  const preview = buildRecommendations(DEMO_USER).items.slice(0, 3)

  return (
    <div className="public">
      <header className="topbar">
        <Logo />
        <nav>
          <a href="#como">Como funciona</a>
          {user ? (
            <Link className="btn small" to="/app">
              Abrir o painel
            </Link>
          ) : (
            <>
              <Link to="/entrar">Entrar</Link>
              <Link className="btn small" to="/cadastro">
                Criar conta
              </Link>
            </>
          )}
        </nav>
      </header>

      <section className="hero">
        <p className="eyebrow">Protótipo de interface</p>
        <h1>Jogos do seu gosto, no computador que você tem.</h1>
        <p className="lede">
          O GameCompass cruza o que você gosta de jogar com o que a sua máquina consegue rodar. A lista chega pronta:
          sem comparar modelo de placa e sem descobrir a incompatibilidade depois da compra.
        </p>
        <div className="hero-actions">
          <Link className="btn" to={user ? "/app" : "/cadastro"}>
            {user ? "Continuar" : "Começar o cadastro"}
          </Link>
          <Link className="btn ghost" to="/entrar">
            Entrar na demonstração
          </Link>
        </div>
      </section>

      <section className="band" id="como">
        <div className="section-head">
          <h2>Quatro passos, uma lista só sua.</h2>
          <p>O fluxo que a interface cobre hoje, com dados de demonstração no próprio navegador.</p>
        </div>
        <ol className="steps">
          {STEPS.map((step) => (
            <li key={step.n}>
              <span>{step.n}</span>
              <h3>{step.title}</h3>
              <p>{step.text}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="band">
        <div className="section-head">
          <h2>Um exemplo já calculado.</h2>
          <p>
            Conta de demonstração: RPG, aventura e indie, com Hades, Hollow Knight e The Witcher 3 de âncora, em um PC
            intermediário com Windows.
          </p>
        </div>
        <div className="card-grid">
          {preview.map((match) => (
            <GameCard
              key={match.game.id}
              game={match.game}
              affinity={match.affinity}
              href={user ? `/app/jogos/${match.game.id}` : `/entrar?next=/app/jogos/${match.game.id}`}
              note="Roda no PC da demonstração"
            />
          ))}
        </div>
      </section>

      <footer className="site-footer">
        <Logo />
        <p>Interface de teste do TCC. Contas, perfil e recomendações ficam só neste navegador.</p>
      </footer>
    </div>
  )
}
