import { useState } from "react"
import { PageHeader } from "../components/PageHeader"
import { SearchSelect } from "../components/SearchSelect"
import { useSession } from "../context/SessionContext"
import { CPUS, GPUS, RAM_OPTIONS, findCpu, findGpu, hardwareSummary } from "../data/hardware"
import { OPERATING_SYSTEMS, type OperatingSystem } from "../types"

export function Hardware() {
  const { user, updateUser } = useSession()
  const [cpuId, setCpuId] = useState(user?.hardware?.cpuId ?? "")
  const [gpuId, setGpuId] = useState(user?.hardware?.gpuId ?? "")
  const [ramGb, setRamGb] = useState(String(user?.hardware?.ramGb ?? ""))
  const [os, setOs] = useState<OperatingSystem | "">(user?.hardware?.os ?? "")
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  if (!user) return null

  const summary = hardwareSummary(user.hardware)
  const cpu = user.hardware ? findCpu(user.hardware.cpuId) : undefined
  const gpu = user.hardware ? findGpu(user.hardware.gpuId) : undefined

  return (
    <div className="page narrow">
      <PageHeader
        eyebrow="Hardware"
        title="O computador em que você joga"
        lede="Escolha peças da base de demonstração. Um nome que não aparece na busca fica de fora, como fará a validação da API."
      />

      <form
        className="stack"
        onSubmit={(event) => {
          event.preventDefault()
          if (!cpuId || !gpuId || !ramGb || !os) {
            setSaved(false)
            setError("Informe processador, placa de vídeo, memória e sistema.")
            return
          }
          updateUser({
            hardware: { cpuId, gpuId, ramGb: Number(ramGb), os },
          })
          setError(null)
          setSaved(true)
        }}
      >
        <SearchSelect
          label="Processador"
          options={CPUS.map((part) => ({ id: part.id, label: part.name, hint: part.vendor }))}
          value={cpuId}
          onChange={(id) => {
            setCpuId(id)
            setSaved(false)
          }}
          placeholder="Buscar modelo de CPU"
          empty="Nenhum processador com esse nome na base de demonstração."
        />
        <SearchSelect
          label="Placa de vídeo"
          options={GPUS.map((part) => ({ id: part.id, label: part.name, hint: part.vendor }))}
          value={gpuId}
          onChange={(id) => {
            setGpuId(id)
            setSaved(false)
          }}
          placeholder="Buscar modelo de GPU"
          empty="Nenhuma placa com esse nome na base de demonstração."
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
        <button className="btn" type="submit">
          Salvar computador
        </button>
      </form>

      {summary && cpu && gpu && (
        <section className="summary-line">
          <p className="eyebrow">Capacidade usada nas sugestões</p>
          <p>{summary.text}</p>
          <details>
            <summary>Pontuações deste protótipo</summary>
            <p>
              Os números são ilustrativos. Eles não vêm de um benchmark publicado. A comparação é direta: cada peça
              precisa alcançar o mínimo do jogo.
            </p>
            <p>
              Processador: {cpu.score}. Placa de vídeo: {gpu.score}. A faixa “{summary.tier}” usa o menor desses dois
              valores.
            </p>
          </details>
        </section>
      )}
    </div>
  )
}
