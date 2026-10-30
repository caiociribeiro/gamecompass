import { Link } from "react-router-dom"
import { Logo } from "../components/Logo"
import { useTitle } from "../components/PageHeader"
import { useSession } from "../context/SessionContext"

const STEPS = [
  { n: "01", title: "O gosto", text: "Gêneros e temáticas ajudam a descrever suas preferências." },
  {
    n: "02",
    title: "Três âncoras",
    text: "Três jogos que você já aprovou puxam títulos parecidos no catálogo.",
  },
  { n: "03", title: "O computador", text: "Processador, placa, memória e sistema viram um limite concreto." },
  {
    n: "04",
    title: "A lista",
    text: "Veja jogos com afinidade e confira as verificações de compatibilidade.",
  },
]

export function Landing() {
  useTitle("GameCompass")
  const { user } = useSession()

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
        <p className="eyebrow">GameCompass</p>
        <h1>Jogos do seu gosto, no computador que você tem.</h1>
        <p className="lede">
          Explore jogos da Steam, escolha seus favoritos e informe seu computador. O GameCompass mostra
          afinidade e ajuda a conferir os requisitos de cada título.
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
          <p>Jogos da Steam e um catálogo de CPUs e GPUs para comparar os requisitos.</p>
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

      <footer className="site-footer">
        <Logo />
        <p>Interface de teste do TCC. Conta e perfil salvos neste navegador; catálogo consultado pela API.</p>
      </footer>
    </div>
  )
}
