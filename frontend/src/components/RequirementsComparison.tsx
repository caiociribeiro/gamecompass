import "../styles/results.css"
import type { Check, GameMatch, HardwareCatalog, HardwareProfile, RequirementLevel } from "../types"

const LEVELS = [
  { key: "minimum", label: "Mínimos", target: "os mínimos" },
  { key: "recommended", label: "Recomendados", target: "os recomendados" },
] as const

function CheckResult({ check, level, available }: {
  check: Check
  level: RequirementLevel
  available: boolean
}) {
  const target = level === "minimum" ? "mínimos" : "recomendados"
  const label = check.ok === true ? `Atende aos ${target}`
    : check.ok === false ? `Não atende aos ${target}`
      : available ? `Validação dos ${target} pendente` : `${level === "minimum" ? "Mínimos" : "Recomendados"} não informados`
  return (
    <>
      <span className={`pill ${check.ok === true ? "ok" : check.ok === false ? "no" : ""}`.trim()}>{label}</span>
      <p className="comparison-detail">{check.detail}</p>
      {check.estimated && <p className="hint">Comparação por referência manual.</p>}
    </>
  )
}

export function RequirementsComparison({ match, profile, catalog }: {
  match: GameMatch
  profile: HardwareProfile
  catalog: HardwareCatalog
}) {
  const current = [
    catalog.CPU.find((part) => part.id === profile.cpuId)?.name ?? "Processador não selecionado",
    catalog.GPU.find((part) => part.id === profile.gpuId)?.name ?? "Placa de vídeo não selecionada",
    `${profile.ramGb} GB de RAM`,
    profile.os === "Windows" && profile.windowsVersion
      ? `Windows ${profile.windowsVersion} (64 bits)` : profile.os,
  ]
  return (
    <div className="comparison-wrap">
      <table className="hardware-comparison">
        <caption className="sr-only">Seu computador comparado aos requisitos mínimos e recomendados do jogo</caption>
        <thead>
          <tr>
            <th scope="col">Seu computador</th>
            <th scope="col">Mínimos</th>
            <th scope="col">Recomendados</th>
            <th scope="col">Sugestão de substituição</th>
          </tr>
        </thead>
        <tbody>
          {match.assessments.minimum.checks.map((check, index) => {
            const failures = LEVELS.filter(({ key }) => match.assessments[key].checks[index].ok === false)
            return (
              <tr key={check.label}>
                <th scope="row">
                  <strong>{check.label}</strong>
                  <p className="comparison-current">{current[index]}</p>
                </th>
                {LEVELS.map(({ key, label }) => (
                  <td data-label={label} key={key}>
                    <CheckResult check={match.assessments[key].checks[index]} level={key} available={match.assessments[key].available} />
                  </td>
                ))}
                <td data-label="Sugestão de substituição">
                  {failures.length ? (
                    <ul className="upgrade-list">
                      {failures.map(({ key, target }) => {
                        const suggestion = match.assessments[key].checks[index].suggestion
                        return (
                          <li key={key}>
                            <span className="upgrade-target">Para {target}</span>
                            {suggestion ? (
                              <>
                                <strong>{suggestion.name}</strong>
                                <p className="comparison-detail">{suggestion.detail}</p>
                                {Boolean(suggestion.alternatives?.length) && (
                                  <ul className="upgrade-alternatives">
                                    {suggestion.alternatives!.map((option) => (
                                      <li key={option.partId ?? option.name}>
                                        <span className="upgrade-target">Outra opção</span>
                                        <strong>{option.name}</strong>
                                        <p className="comparison-detail">{option.detail}</p>
                                      </li>
                                    ))}
                                  </ul>
                                )}
                              </>
                            ) : (
                              <p className="comparison-detail">Nenhuma substituição identificada no catálogo atual.</p>
                            )}
                          </li>
                        )
                      })}
                    </ul>
                  ) : (
                    <p className="comparison-detail">
                      {LEVELS.some(({ key }) => match.assessments[key].checks[index].ok === null)
                        ? "Aguardando a conclusão das verificações."
                        : "Nenhuma substituição necessária para os requisitos comparados."}
                    </p>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
