import { useState } from "react"
import { CatalogStatus } from "../components/CatalogStatus"
import { PageHeader } from "../components/PageHeader"
import { SearchSelect } from "../components/SearchSelect"
import { useCatalog } from "../context/CatalogContext"
import { useSession } from "../context/SessionContext"
import { OPERATING_SYSTEMS, RAM_OPTIONS } from "../data/hardware"
import { hardwareSummary } from "../lib/hardware"
import type { OperatingSystem, Part } from "../types"

export function Hardware() {
  const { user, updateUser } = useSession()
  const { hardware, hardwareLoading, hardwareError, refresh } = useCatalog()
  const [cpuId, setCpuId] = useState(user?.hardware?.cpuId ?? "")
  const [gpuId, setGpuId] = useState(user?.hardware?.gpuId ?? "")
  const [ramGb, setRamGb] = useState(String(user?.hardware?.ramGb ?? ""))
  const [os, setOs] = useState<OperatingSystem | "">(user?.hardware?.os ?? "")
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  if (!user) return null
  const summary = hardwareSummary(user.hardware, hardware)
  const hint = (part: Part) =>
    `${part.vendor} · ${part.performance_score === null ? "Classificação pendente" : `Classe ${part.performance_score}`}`
  return (
    <div className="page narrow">
      <PageHeader
        eyebrow="Hardware"
        title="O computador em que você joga"
        lede="Escolha sua CPU e GPU no catálogo. Informe também a capacidade de RAM e o sistema operacional."
      />
      <CatalogStatus scope="hardware" />
      {!hardwareLoading && !hardwareError && (!hardware.CPU.length || !hardware.GPU.length) && (
        <p className="banner warn">
          O catálogo de hardware está vazio ou incompleto. Carregue as peças para continuar.
        </p>
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
          updateUser({ hardware: { cpuId, gpuId, ramGb: Number(ramGb), os } })
          setError(null)
          setSaved(true)
        }}
      >
        <SearchSelect
          label="Processador"
          options={hardware.CPU.map((part) => ({ id: part.id, label: part.name, hint: hint(part) }))}
          value={cpuId}
          onChange={(id) => {
            setCpuId(id)
            setSaved(false)
          }}
          placeholder="Buscar modelo de CPU"
          empty="Nenhum processador com esse nome no catálogo carregado."
        />
        <SearchSelect
          label="Placa de vídeo"
          options={hardware.GPU.map((part) => ({ id: part.id, label: part.name, hint: hint(part) }))}
          value={gpuId}
          onChange={(id) => {
            setGpuId(id)
            setSaved(false)
          }}
          placeholder="Buscar modelo de GPU"
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
        <button className="btn" type="submit" disabled={hardwareLoading || Boolean(hardwareError)}>
          Salvar computador
        </button>
      </form>
      {summary && (
        <section className="summary-line">
          <p className="eyebrow">Seu computador</p>
          <p>{summary.text}</p>
          <p className="hint">
            CPU: {summary.cpu.performance_score ?? "pendente"}. GPU:{" "}
            {summary.gpu.performance_score ?? "pendente"}. Índice {hardware.score_version}; cada componente
            tem sua própria escala.
          </p>
        </section>
      )}
    </div>
  )
}
