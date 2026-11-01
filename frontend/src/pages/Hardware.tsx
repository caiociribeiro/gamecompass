import { useState } from "react"
import { CatalogStatus } from "../components/CatalogStatus"
import { PageHeader } from "../components/PageHeader"
import { SearchSelect } from "../components/SearchSelect"
import { useCatalog } from "../context/CatalogContext"
import { useSession } from "../context/SessionContext"
import { OPERATING_SYSTEMS, RAM_OPTIONS, WINDOWS_VERSIONS } from "../data/hardware"
import { hardwareSummary } from "../lib/hardware"
import type { OperatingSystem, WindowsVersion } from "../types"

export function Hardware() {
  const { user, updateUser } = useSession()
  const { hardware, hardwareLoading, hardwareError, refresh } = useCatalog()
  const [cpuId, setCpuId] = useState(user?.hardware?.cpuId ?? "")
  const [gpuId, setGpuId] = useState(user?.hardware?.gpuId ?? "")
  const [ramGb, setRamGb] = useState(String(user?.hardware?.ramGb ?? ""))
  const [os, setOs] = useState<OperatingSystem | "">(user?.hardware?.os ?? "")
  const [windowsVersion, setWindowsVersion] = useState<WindowsVersion | "">(
    user?.hardware?.windowsVersion ?? "",
  )
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  if (!user) return null
  const cpuUnavailable = hardwareLoading || Boolean(hardwareError) || !hardware.CPU.length
  const gpuUnavailable = hardwareLoading || Boolean(hardwareError) || !hardware.GPU.length
  const summary = hardwareSummary(user.hardware, hardware)
  return (
    <div className="page narrow">
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
      <form
        className="stack"
        onSubmit={(event) => {
          event.preventDefault()
          if (
            hardwareLoading ||
            hardwareError ||
            !hardware.CPU.some((part) => part.id === cpuId) ||
            !hardware.GPU.some((part) => part.id === gpuId) ||
            !RAM_OPTIONS.some((value) => value === Number(ramGb)) ||
            !os
          ) {
            setSaved(false)
            setError("Selecione uma CPU, uma GPU, a RAM e o sistema operacional disponíveis.")
            return
          }
          if (os === "Windows" && !WINDOWS_VERSIONS.some((version) => version === windowsVersion)) {
            setSaved(false)
            setError("Selecione sua versão do Windows de 64 bits.")
            return
          }
          updateUser({
            hardware: {
              cpuId, gpuId, ramGb: Number(ramGb), os,
              windowsVersion: os === "Windows" ? windowsVersion as WindowsVersion : undefined,
            },
          })
          setError(null)
          setSaved(true)
        }}
      >
        <SearchSelect
          label="Processador"
          disabled={cpuUnavailable}
          options={hardware.CPU.map((part) => ({ id: part.id, label: part.name, hint: part.vendor }))}
          value={cpuId}
          onChange={(id) => {
            setCpuId(id)
            setSaved(false)
          }}
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
          options={hardware.GPU.map((part) => ({ id: part.id, label: part.name, hint: part.vendor }))}
          value={gpuId}
          onChange={(id) => {
            setGpuId(id)
            setSaved(false)
          }}
          placeholder={
            hardwareLoading
              ? "Carregando placas de vídeo…"
              : gpuUnavailable
                ? "Catálogo de GPUs indisponível"
                : "Buscar modelo de GPU"
          }
          empty="Nenhuma placa com esse nome no catálogo carregado."
        />
        <label>
          Memória RAM
          <select
            value={ramGb}
            onChange={(event) => {
              setRamGb(event.target.value)
              setSaved(false)
            }}
          >
            <option value="">Selecione</option>
            {RAM_OPTIONS.map((ram) => (
              <option key={ram} value={ram}>
                {ram} GB
              </option>
            ))}
          </select>
        </label>
        <label>
          Sistema operacional
          <select
            value={os}
            onChange={(event) => {
              setOs(event.target.value as OperatingSystem | "")
              setWindowsVersion("")
              setSaved(false)
            }}
          >
            <option value="">Selecione</option>
            {OPERATING_SYSTEMS.map((system) => (
              <option key={system} value={system}>
                {system}
              </option>
            ))}
          </select>
        </label>
        {os === "Windows" && (
          <label>
            Versão do Windows
            <select
              value={windowsVersion}
              onChange={(event) => {
                setWindowsVersion(event.target.value as WindowsVersion | "")
                setSaved(false)
              }}
            >
              <option value="">Selecione</option>
              {WINDOWS_VERSIONS.map((version) => (
                <option key={version} value={version}>Windows {version} (64 bits)</option>
              ))}
            </select>
          </label>
        )}
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        {saved && (
          <p className="hint" role="status">
            Computador salvo neste navegador.
          </p>
        )}
        <button className="btn" type="submit" disabled={cpuUnavailable || gpuUnavailable}>
          Salvar computador
        </button>
      </form>
      {summary && (
        <section className="summary-line">
          <p className="eyebrow">Seu computador</p>
          <p>{summary.text}</p>
        </section>
      )}
    </div>
  )
}
