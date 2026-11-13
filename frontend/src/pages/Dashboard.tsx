import { Link } from "react-router-dom"
import { CatalogStatus } from "../components/CatalogStatus"
import { GameCard } from "../components/GameCard"
import { CompassIcon } from "../components/PixelIcons"
import { useCatalog } from "../context/CatalogContext"
import { useSession } from "../context/SessionContext"
import { hardwareSummary } from "../lib/hardware"
import { nextPendingStep, profileSteps } from "../lib/profile"
import { compatibilityLabel, profileReady } from "../lib/recommend"
import { useGridCols } from "../lib/useGridCols"
import "../styles/start.css"

const PHASES = [
  { name: "PERFIL", to: "/app/preferencias", text: "Escolha gêneros e temas que você curte." },
  { name: "ÂNCORAS", to: "/app/ancoras", text: "Escolha três jogos que representam você." },
  { name: "COMPUTADOR", to: "/app/hardware", text: "Conte as peças do seu PC: processador, placa de vídeo e memória." },
  { name: "SUGESTÕES", to: "/app/recomendacoes", text: "Veja os jogos com a afinidade e se o seu PC aguenta." },
]

type Bitmap = { rows: string[]; palette: Record<string, string> }
const ICONS: Bitmap[] = [
  { rows: ["..KKKK..", ".KCCCCK.", ".KCKKCK.", ".KCCCCK.", "..KKKK..", ".KGGGGK.", "KGGGGGGK", "KKKKKKKK"], palette: { K: "#000", C: "#6be1ff", G: "#5cff9d" } },
  { rows: ["...KK...", "..KYYK..", "KKKYYKKK", "KYYYYYYK", ".KYYYYK.", ".KYYYYK.", "KYYKKYYK", "KKK..KKK"], palette: { K: "#000", Y: "#ffd86b" } },
  { rows: ["KKKKKKKK", "KCCCCCCK", "KCBBBBCK", "KCBBBBCK", "KCCCCCCK", "KKKKKKKK", "..KKKK..", ".KKKKKK."], palette: { K: "#000", C: "#8a7fb0", B: "#6be1ff" } },
  { rows: ["KKKKKKKK", "KYYYYYYK", ".KYYYYK.", "..KYYK..", "..KYYK..", "..KYYK..", ".KKKKKK.", "KRRRRRRK"], palette: { K: "#000", Y: "#ffd86b", R: "#ff5c6c" } },
]

function PhaseIcon({ index }: { index: number }) {
  const { rows, palette } = ICONS[index]
  return (
    <svg viewBox="0 0 8 8" shapeRendering="crispEdges" aria-hidden="true" focusable="false">
      {rows.flatMap((row, y) =>
        [...row].map((char, x) => (palette[char] ? <rect key={`${x}-${y}`} x={x} y={y} width={1.03} height={1.03} fill={palette[char]} /> : null)),
      )}
    </svg>
  )
}

export function Dashboard() {
  const { user } = useSession()
  const catalog = useCatalog()
  const affinityItems = (() => {
    const result = catalog.recommendations ?? { items: [], pending: [] }
    return [...result.items, ...result.pending].slice(0, 3)
  })()
  const anchorGames = user ? catalog.games.filter((game) => user.anchorIds.includes(game.id)) : []
  const affinityRef = useGridCols(affinityItems.length)
  const anchorRef = useGridCols(anchorGames.length, true)
  if (!user) return null
  const { games, hardware } = catalog
  const steps = profileSteps(user, games, hardware)
  const next = nextPendingStep(steps)
  const ready = profileReady(user, games, hardware)
  const result = catalog.recommendations ?? { items: [], pending: [], excluded: [] }
  const summary = hardwareSummary(user.hardware, hardware)
  const doneCount = steps.filter((step) => step.done).length
  const nextIndex = next ? steps.findIndex((step) => step.id === next.id) : 3
  const fresh = doneCount === 0
  const letters = "GAMECOMPASS".split("")
  return (
    <div className="page">
      <section className="start-hero">
        <CompassIcon size={72} spin />
        <h1 className="start-title" aria-label="GameCompass">
          {letters.map((letter, index) => (
            <span key={index} aria-hidden="true">{letter}</span>
          ))}
        </h1>
        <p className="start-sub">Descubra quais jogos combinam com você e rodam no seu PC</p>
        <p className="start-hello">Olá, {user.name}.</p>
      </section>

      <nav className={fresh ? "trail intro" : "trail"} style={{ ["--step" as string]: nextIndex }} aria-label="Fases do seu perfil">
        <div className="trail-road" aria-hidden="true" />
        <span className="trail-lane" aria-hidden="true"><span className="trail-track"><span className="trail-walker" /></span></span>
        {PHASES.map((phase, index) => {
          const done = index < 3 && steps[index].done
          const cls = index === nextIndex ? "trail-node cur" : done ? "trail-node done" : "trail-node"
          return (
            <Link
              key={phase.name}
              className={cls}
              to={phase.to}
              style={{ left: `calc((100% - 40px) * ${index / 3})` }}
              aria-label={`Fase ${index + 1}: ${phase.name}${done ? " (concluída)" : ""}`}
            >
              <b aria-hidden="true">{done ? "✓" : index + 1}</b>
              <span aria-hidden="true">{phase.name}</span>
            </Link>
          )
        })}
      </nav>

      <div className="progress-head">
        <h2>
          {doneCount} de {steps.length} prontos
        </h2>
        <p className="lede" style={{ margin: 0 }}>
          {ready
            ? "Seu perfil está preenchido. Confira a afinidade e as pendências técnicas de cada título."
            : "Complete seu perfil e explore os jogos consultados na Steam."}
        </p>
      </div>

      <ol className="step-cards">
        {steps.map((step, index) => {
          const isNext = step.id === next?.id
          return (
            <li key={step.id} className={`step-card${step.done ? " done" : ""}${isNext ? " next" : ""}`}>
              <span className="tag">FASE {index + 1}</span>
              <PhaseIcon index={index} />
              <h3>{PHASES[index].name}</h3>
              <strong className="sr-only">{step.label}</strong>
              {isNext && <span className="next-tag">Próxima etapa</span>}
              <p>{step.hint}</p>
              <Link className={isNext ? "btn small" : "btn ghost small"} to={step.to}>
                {step.done ? "Rever" : isNext ? "Continuar" : "Preencher"}
              </Link>
            </li>
          )
        })}
        <li className="step-card">
          <span className="tag">FASE 4</span>
          <PhaseIcon index={3} />
          <h3>SUGESTÕES</h3>
          <p>{PHASES[3].text}</p>
          {ready ? (
            <Link className="btn small" to="/app/recomendacoes">
              Ver recomendações
            </Link>
          ) : (
            <span className="hint">Termine as fases 1 a 3.</span>
          )}
        </li>
      </ol>

      {next && (
        <div className="go">
          <Link className="btn big" to={next.to}>
            <span className="ar" aria-hidden="true">▶</span> {fresh ? "COMEÇAR" : `CONTINUAR: FASE ${nextIndex + 1} · ${PHASES[nextIndex].name}`}
          </Link>
          <p className="go-hint">{fresh ? "APERTE PARA INICIAR A FASE 1" : "DE ONDE VOCÊ PAROU"}</p>
        </div>
      )}

      {summary && (
        <section className="panel summary-panel" style={{ marginTop: 18 }}>
          <div className="section-head">
            <p className="eyebrow">Seu computador</p>
            <Link to="/app/hardware">Alterar</Link>
          </div>
          <p>{summary.text}</p>
        </section>
      )}
      {ready && catalog.discovered && (
        <section className="stack">
          <div className="section-head">
            <h2>Jogos com afinidade</h2>
            <Link to="/app/recomendacoes">Ver análise completa</Link>
          </div>
          <div className="card-grid" ref={affinityRef}>
            {affinityItems.map((match) => (
              <GameCard
                key={match.game.id}
                game={match.game}
                affinity={match.affinity}
                href={`/app/jogos/${match.game.id}`}
                note={compatibilityLabel(match)}
              />
            ))}
          </div>
          {!result.items.length && !result.pending.length && (
            <p className="empty">
              Nenhum título passou pelo filtro de afinidade e pelas verificações disponíveis.
            </p>
          )}
        </section>
      )}
      <section className="stack">
        <div className="section-head">
          <h2>Seus jogos âncora</h2>
          <Link to="/app/ancoras">Escolher jogos</Link>
        </div>
        <CatalogStatus />
        {catalog.gameIssues.length > 0 && (
          <p className="hint">Alguns jogos salvos não foram disponibilizados pela Steam nesta consulta.</p>
        )}
        <div className="card-grid" ref={anchorRef}>
          {anchorGames.map((game) => (
            <GameCard key={game.id} game={game} href={`/app/jogos/${game.id}`} note={game.price_text ?? undefined} />
          ))}
        </div>
        {!user.anchorIds.length && (
          <p className="empty">Nenhum jogo selecionado. Pesquise pelo nome para escolher suas âncoras.</p>
        )}
        {ready && !catalog.discovered && <Link to="/app/recomendacoes">Buscar sugestões para meu perfil</Link>}
      </section>
    </div>
  )
}
