import { useEffect, useMemo, useRef, useState, type ReactNode } from "react"
import { CatalogStatus } from "../components/CatalogStatus"
import { PageHeader } from "../components/PageHeader"
import { SearchSelect } from "../components/SearchSelect"
import { StepFooter } from "../components/StepFooter"
import { StepNav } from "../components/StepNav"
import { useCatalog } from "../context/CatalogContext"
import { useSession } from "../context/SessionContext"
import { useSound } from "../context/SoundContext"
import { OPERATING_SYSTEMS, RAM_OPTIONS, WINDOWS_VERSIONS } from "../data/hardware"
import { hardwareSummary } from "../lib/hardware"
import { rankParts, surveyLabel } from "../lib/hardwareRank"
import gpuSurvey from "../data/steamGpuSurvey.json"
import type { OperatingSystem, WindowsVersion } from "../types"
import "../styles/results.css"

function bitmap(rows: string[], palette: Record<string, string>) {
  const cells: ReactNode[] = []
  rows.forEach((row, y) => {
    for (let x = 0; x < row.length; x += 1) {
      if (palette[row[x]]) cells.push(<rect key={`${x}-${y}`} x={x} y={y} width={1.03} height={1.03} fill={palette[row[x]]} />)
    }
  })
  return <svg viewBox="0 0 8 8" shapeRendering="crispEdges" aria-hidden="true" focusable="false">{cells}</svg>
}

const SLOT_ICONS = [
  bitmap(["KKKKKKKK", "KGGGGGGK", "KGKKKKGK", "KGKYYKGK", "KGKYYKGK", "KGKKKKGK", "KGGGGGGK", "KKKKKKKK"], { K: "#000", G: "#6be1ff", Y: "#ffd86b" }),
  bitmap(["........", "KKKKKKKK", "KGGGGGGK", "KGKKGKKK", "KGKKGGGK", "KGGGGGGK", "KKKKKKKK", "K.K.K.K."], { K: "#000", G: "#5cff9d" }),
  bitmap(["........", "KKKKKKKK", "KRKRKRKK", "KRKRKRKK", "KRKRKRKK", "KKKKKKKK", "K.K.K.K.", "........"], { K: "#000", R: "#ff9bb5" }),
  bitmap(["..KKKK..", ".KOOOOK.", "KOOKKOOK", "KOKOOKOK", "KOKOOKOK", "KOOKKOOK", ".KOOOOK.", "..KKKK.."], { K: "#000", O: "#ffd86b" }),
]
const SLOT_LABELS = ["CPU", "GPU", "RAM", "SISTEMA"]

export function Hardware() {
  const { user, updateUser, saving, saveError } = useSession()
  const { play } = useSound()
  const { hardware, hardwareLoading, hardwareError, refresh } = useCatalog()
  const cpuOptions = useMemo(() => rankParts(hardware.CPU), [hardware.CPU])
  const gpuOptions = useMemo(() => rankParts(hardware.GPU, gpuSurvey), [hardware.GPU])
  const [cpuId, setCpuId] = useState(user?.hardware?.cpuId ?? "")
  const [gpuId, setGpuId] = useState(user?.hardware?.gpuId ?? "")
  const [ramGb, setRamGb] = useState(String(user?.hardware?.ramGb ?? ""))
  const [os, setOs] = useState<OperatingSystem | "">(user?.hardware?.os ?? "")
  const [windowsVersion, setWindowsVersion] = useState<WindowsVersion | "">(
    user?.hardware?.windowsVersion ?? "",
  )
  const [saved, setSaved] = useState(false)
  const [justFilled, setJustFilled] = useState<number | null>(null)
  const lastSent = useRef<string | null>(null)
  const stored = user?.hardware
  const cpuKnown = hardware.CPU.some((part) => part.id === cpuId)
  const gpuKnown = hardware.GPU.some((part) => part.id === gpuId)
  const ramValid = RAM_OPTIONS.some((value) => value === Number(ramGb))
  const windowsValid = os !== "Windows" || WINDOWS_VERSIONS.some((version) => version === windowsVersion)
  const catalogReady = !hardwareLoading && !hardwareError
  const complete = catalogReady && cpuKnown && gpuKnown && ramValid && Boolean(os) && windowsValid

  // Salva sozinho: assim que as quatro peças estão válidas e diferentes do que está na conta.
  useEffect(() => {
    if (!complete || !os) return
    const next = {
      cpuId, gpuId, ramGb: Number(ramGb), os,
      windowsVersion: os === "Windows" ? windowsVersion as WindowsVersion : undefined,
    }
    const same = stored && stored.cpuId === next.cpuId && stored.gpuId === next.gpuId && stored.ramGb === next.ramGb &&
      stored.os === next.os && (next.os !== "Windows" || (stored.windowsVersion ?? "") === next.windowsVersion)
    const key = JSON.stringify(next)
    if (same) { lastSent.current = key; return }
    if (lastSent.current === key) return
    lastSent.current = key
    updateUser({ hardware: next })
    setSaved(true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [complete, cpuId, gpuId, ramGb, os, windowsVersion])

  if (!user) return null
  const cpuUnavailable = hardwareLoading || Boolean(hardwareError) || !hardware.CPU.length
  const gpuUnavailable = hardwareLoading || Boolean(hardwareError) || !hardware.GPU.length
  const summary = hardwareSummary(user.hardware, hardware)
  const catalogFilled = catalogReady && hardware.CPU.length > 0 && hardware.GPU.length > 0
  let error: string | null = null
  if (catalogFilled && ((cpuId && !cpuKnown) || (gpuId && !gpuKnown) || (ramGb && !ramValid))) {
    error = "Selecione uma CPU, uma GPU, a RAM e o sistema operacional disponíveis."
  } else if (cpuKnown && gpuKnown && ramValid && os === "Windows" && !windowsValid) {
    error = "Selecione sua versão do Windows de 64 bits."
  }

  const nameOf = (list: { id: string; name: string }[], id: string) => list.find((part) => part.id === id)?.name ?? ""
  const osText = os ? (os === "Windows" && windowsVersion ? `Windows ${windowsVersion}` : os) : ""
  const slotValues = [
    cpuKnown ? nameOf(hardware.CPU, cpuId) : "",
    gpuKnown ? nameOf(hardware.GPU, gpuId) : "",
    ramValid ? `${ramGb} GB` : "",
    os && windowsValid ? osText : "",
  ]
  const filled = slotValues.filter(Boolean).length
  const changed = (slot: number) => { setSaved(false); setJustFilled(slot) }

  return (
    <div className="page">
      <StepNav current="hardware" live={{ hardware: filled / 4 }} />
      <PageHeader
        eyebrow="Hardware"
        title="O computador em que você joga"
        lede="Escolha sua CPU e GPU no catálogo. Informe também a capacidade de RAM e o sistema operacional."
      />
      <CatalogStatus scope="hardware" />
      {!hardwareLoading && !hardwareError && (!hardware.CPU.length || !hardware.GPU.length) && (
        <div className="banner warn" role="status">
          <p>O servidor respondeu, mas faltam componentes no catálogo deste ambiente.</p>
          <p>
            Processadores: {hardware.CPU.length} · Placas de vídeo: {hardware.GPU.length}.
          </p>
          <p>Atualize o catálogo depois que os componentes estiverem disponíveis.</p>
        </div>
      )}
      <button type="button" className="btn ghost small" disabled={hardwareLoading} onClick={refresh}>
        Atualizar catálogo
      </button>
      <div className="pc-cols">
        <aside className="pc" aria-label="Seu computador montado">
          <div className={`pc-mon${filled === 4 ? " on" : ""}`}>
            {filled === 4 ? <span className="on1">PC PRONTO<br /><i>▮</i></span> : <span className="off">SEM SINAL<br />MONTE O PC</span>}
          </div>
          <div className="pc-power" aria-hidden="true">
            {[0, 1, 2, 3].map((index) => <i key={index} className={index < filled ? "on" : ""} />)}
          </div>
          {SLOT_LABELS.map((label, index) => (
            <div key={label} className={`pc-slot${slotValues[index] ? " fl" : ""}${slotValues[index] && justFilled === index ? " ins" : ""}`}>
              {SLOT_ICONS[index]}
              <div>
                <b>{label}</b>
                <span>{slotValues[index] || "vazio"}</span>
              </div>
            </div>
          ))}
        </aside>
        <form className="pc-form" onSubmit={(event) => event.preventDefault()}>
          <SearchSelect
            label="Processador"
            disabled={cpuUnavailable}
            options={cpuOptions}
            topLabel="Mais potentes do catálogo"
            value={cpuId}
            onChange={(id) => { setCpuId(id); changed(0) }}
            placeholder={
              hardwareLoading
                ? "Carregando processadores…"
                : cpuUnavailable
                  ? "Catálogo de CPUs indisponível"
                  : "Buscar modelo de CPU"
            }
            empty="Nenhum processador com esse nome no catálogo carregado."
          />
          <SearchSelect
            label="Placa de vídeo"
            disabled={gpuUnavailable}
            options={gpuOptions}
            topLabel={`Mais usadas na Steam (${surveyLabel(gpuSurvey.survey_month)})`}
            value={gpuId}
            onChange={(id) => { setGpuId(id); changed(1) }}
            placeholder={
              hardwareLoading
                ? "Carregando placas de vídeo…"
                : gpuUnavailable
                  ? "Catálogo de GPUs indisponível"
                  : "Buscar modelo de GPU"
            }
            empty="Nenhuma placa com esse nome no catálogo carregado."
          />
          <div className="pc-field">
            <span className="field-label" id="ram-label">Memória RAM</span>
            <div className="chips" role="group" aria-labelledby="ram-label">
              {RAM_OPTIONS.map((ram) => (
                <button
                  key={ram}
                  type="button"
                  className={`chip${Number(ramGb) === ram ? " on" : ""}`}
                  aria-pressed={Number(ramGb) === ram}
                  onClick={() => { play("select"); setRamGb(String(ram)); changed(2) }}
                >
                  {ram} GB
                </button>
              ))}
            </div>
          </div>
          <div className="pc-field">
            <span className="field-label" id="os-label">Sistema operacional</span>
            <div className="chips" role="group" aria-labelledby="os-label">
              {OPERATING_SYSTEMS.map((system) => (
                <button
                  key={system}
                  type="button"
                  className={`chip${os === system ? " on" : ""}`}
                  aria-pressed={os === system}
                  onClick={() => {
                    play("select")
                    if (os !== system) { setOs(system); setWindowsVersion("") }
                    changed(3)
                  }}
                >
                  {system}
                </button>
              ))}
            </div>
            {os === "Windows" && (
              <>
                <span className="field-label" id="wv-label" style={{ marginTop: 12 }}>Versão do Windows</span>
                <div className="chips" role="group" aria-labelledby="wv-label">
                  {WINDOWS_VERSIONS.map((version) => (
                    <button
                      key={version}
                      type="button"
                      className={`chip${windowsVersion === version ? " on" : ""}`}
                      aria-pressed={windowsVersion === version}
                      onClick={() => { play("select"); setWindowsVersion(version); changed(3) }}
                    >
                      Windows {version} (64 bits)
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <p className={saved && !saving && saveError ? "pc-saved error" : "pc-saved"} role="status">{saved ? (saving ? "▮ SALVANDO…" : saveError ? "▮ NÃO FOI SALVO" : "▮ SALVO NA CONTA") : ""}</p>
        </form>
      </div>
      {summary && (
        <section className="panel">
          <p className="eyebrow">Seu computador</p>
          <p>{summary.text}</p>
        </section>
      )}
      <StepFooter id="hardware" />
    </div>
  )
}
