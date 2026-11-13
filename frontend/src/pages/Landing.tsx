import { Link } from "react-router-dom"
import { Logo } from "../components/Logo"
import { useTitle } from "../components/PageHeader"
import { useSession } from "../context/SessionContext"
import { CompassIcon } from "../components/PixelIcons"
import "../styles/public.css"

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

const SPRITES: Record<string, { rows: string[]; color: string }> = {
  coin: { color: "#ffd86b", rows: ["..1111..", ".111111.", "11122111", "11122111", "11122111", "11122111", ".111111.", "..1111.."] },
  heart: { color: "#ff5c6c", rows: [".11..11.", "11111111", "11111111", "11111111", ".111111.", "..1111..", "...11...", "........"] },
  pad: { color: "#6be1ff", rows: ["........", ".111111.", "11111111", "12211221", "12211111", "11111111", ".11..11.", "........"] },
  star: { color: "#5cff9d", rows: ["...11...", "...11...", "11111111", ".111111.", "..1111..", ".111111.", ".11..11.", "11....11"] },
  sword: { color: "#cfd8ff", rows: ["......11", ".....111", "....111.", "1..111..", ".1111...", "..11....", ".1.11...", "1...1..."] },
  ghost: { color: "#ffffff", rows: ["..1111..", ".111111.", "11211211", "11111111", "11111111", "11111111", "11.11.11", "1..11..1"] },
  shroom: { color: "#ff5c6c", rows: ["..1111..", ".112211.", "11122111", "11111111", "..2222..", "..2222..", "..2222..", "........"] },
  potion: { color: "#5cff9d", rows: ["..2222..", "...22...", "..1111..", ".111111.", "11111111", "11111111", ".111111.", "..1111.."] },
  key: { color: "#ffd86b", rows: [".1111...", "11..11..", "11..11..", ".1111...", "..11....", "..111...", "..11....", "..111..."] },
  shield: { color: "#6be1ff", rows: ["11111111", "11222211", "11222211", "11222211", ".122221.", ".112211.", "..1221..", "...11..."] },
  gem: { color: "#c9a7ff", rows: ["..1111..", ".111111.", "11111111", ".111111.", "..1111..", "...11...", "........", "........"] },
}
const FLOATERS = [
  ["coin", 4, 18, 0], ["heart", 12, 26, 4], ["pad", 21, 22, 9], ["star", 30, 30, 2], ["gem", 38, 20, 7],
  ["coin", 47, 28, 12], ["heart", 55, 18, 5], ["pad", 63, 24, 10], ["star", 71, 32, 1], ["gem", 79, 22, 14],
  ["sword", 87, 30, 6], ["ghost", 95, 28, 11], ["shroom", 8, 34, 15], ["potion", 26, 26, 3], ["key", 43, 24, 8],
  ["shield", 59, 30, 13], ["sword", 75, 24, 2], ["potion", 91, 22, 9], ["ghost", 34, 22, 16], ["shroom", 67, 26, 5],
] as const

function Sprite({ kind }: { kind: string }) {
  const { rows, color } = SPRITES[kind]
  return (
    <svg viewBox="0 0 8 8" shapeRendering="crispEdges" width="100%" height="100%">
      {rows.flatMap((row, y) =>
        [...row].map((c, x) => (c === "." ? null : <rect key={`${x}-${y}`} x={x} y={y} width="1.02" height="1.02" fill={c === "2" ? "#fff" : color} />)),
      )}
    </svg>
  )
}

function Backdrop() {
  return (
    <div className="lp-bg" aria-hidden="true">
      <div className="lp-stars lp-stars-a" />
      <div className="lp-stars lp-stars-b" />
      <i className="lp-shoot" style={{ top: "14%", animationDelay: "1s" }} />
      <i className="lp-shoot" style={{ top: "34%", animationDelay: "6s" }} />
      {FLOATERS.map(([kind, left, size, delay], i) => (
        <span key={i} className="lp-float" style={{ left: `${left}%`, width: size, height: size, animationDelay: `-${delay}s`, animationDuration: `${16 + (i % 4) * 3}s` }}>
          <Sprite kind={kind} />
        </span>
      ))}
      <i className="lp-cloud" style={{ top: "12%", animationDuration: "80s" }} />
      <i className="lp-cloud lp-cloud-2" style={{ top: "42%", animationDuration: "120s", animationDelay: "-50s" }} />
      <div className="lp-hills lp-hills-far" />
      <div className="lp-hills lp-hills-near" />
      <i className="lp-hero" />
    </div>
  )
}

const PHASES = ["PERFIL", "ÂNCORAS", "COMPUTADOR", "SUGESTÕES"]

export function Landing() {
  useTitle("GameCompass")
  const { user } = useSession()

  return (
    <div className="public">
      <Backdrop />
      <header className="topbar">
        <Logo />
        <nav>
          <a href="#como">Como funciona</a>
          {user ? (
            <Link className="btn" to="/app">
              Abrir o painel
            </Link>
          ) : (
            <>
              <Link className="btn ghost" to="/entrar">Entrar</Link>
              <Link className="btn" to="/cadastro">
                Criar conta
              </Link>
            </>
          )}
        </nav>
      </header>

      <section className="hero">
        <div className="hero-compass">
          <CompassIcon spin size={76} />
        </div>
        <div className="hero-title" aria-hidden="true">
          {"GAMECOMPASS".split("").map((ch, i) => (
            <span key={i}>{ch}</span>
          ))}
        </div>
        <h1>Jogos do seu gosto, no computador que você tem.</h1>
        <p className="lede">
          Explore jogos da Steam, escolha seus favoritos e informe seu computador. O GameCompass mostra
          afinidade e ajuda a conferir os requisitos de cada título.
        </p>
        <div className="hero-actions">
          <Link className="btn" to={user ? "/app" : "/cadastro"}>
            {user ? "Continuar" : "Começar o cadastro"}
          </Link>
        </div>
      </section>

      <div className="lp-trail" aria-hidden="true">
        <div className="lp-road" />
        {PHASES.map((label, i) => {
          const left = `calc(${(i * 100) / 3}% - 20px)`
          return (
            <span key={label} style={{ display: "contents" }}>
              <div className="lp-nd" style={{ left }}>{i + 1}</div>
              <div className="lp-nl" style={{ left: `calc(${(i * 100) / 3}% - 20px + 20px - 45px + 25px)` }}>{label}</div>
            </span>
          )
        })}
      </div>

      <section className="band" id="como">
        <div className="lp-head">
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

    </div>
  )
}
