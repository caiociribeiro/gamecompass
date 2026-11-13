// Monta componentes React reais num jsdom, com HTTP fictício. Usado pelos testes de interface.
//
// Cada teste passa o código do "Harness" (um módulo TSX que exporta React, createRoot e Harness),
// e este helper empacota com esbuild, troca os globais do navegador, intercepta o fetch e limpa
// tudo no fim do teste. Nenhuma API, banco ou navegador real é acessado.
import type { TestContext } from "node:test"
import { mkdtemp, rm } from "node:fs/promises"
import { join } from "node:path"
import { fileURLToPath, pathToFileURL } from "node:url"
import * as esbuild from "esbuild"
import { JSDOM } from "jsdom"

/** Pasta frontend/, para os imports do Harness. */
export const FRONTEND = fileURLToPath(new URL("../../", import.meta.url))

/** Caminho de um arquivo de frontend/src pronto para entrar num import do Harness. */
export const src = (path: string) => JSON.stringify(join(FRONTEND, "src", path))

export type FetchHandler = (path: string, options: any, log: string[]) => Response | Promise<Response>

const GLOBALS = ["window", "document", "navigator", "localStorage", "HTMLElement", "Event", "MouseEvent", "IS_REACT_ACT_ENVIRONMENT"]

export async function mountReact(t: TestContext, options: {
  /** Código TSX do módulo de teste; precisa exportar React, createRoot e Harness. */
  source: string
  /** Responde às chamadas de fetch; cada chamada também entra em `log` como "MÉTODO /caminho". */
  fetch: FetchHandler
  /** Roda depois de criar o jsdom e antes de carregar o app (ex.: preparar o localStorage). */
  beforeImport?: () => void
}) {
  const directory = await mkdtemp(join(FRONTEND, "node_modules", ".gamecompass-ui-"))
  const outfile = join(directory, "app.mjs")
  await esbuild.build({
    stdin: { contents: options.source, resolveDir: FRONTEND, loader: "tsx" },
    bundle: true, format: "esm", platform: "browser", outfile, external: ["react", "react-dom", "react-dom/client"],
    define: { "process.env.NODE_ENV": '"development"' }, loader: { ".css": "empty", ".json": "json" }, logLevel: "silent",
  })
  const dom = new JSDOM('<!doctype html><div id="root"></div>', { url: "http://localhost/", pretendToBeVisual: true })
  const saved = new Map<string, PropertyDescriptor | undefined>()
  for (const name of GLOBALS) {
    saved.set(name, Object.getOwnPropertyDescriptor(globalThis, name))
    Object.defineProperty(globalThis, name, { value: name === "IS_REACT_ACT_ENVIRONMENT" ? true : (dom.window as any)[name], configurable: true, writable: true })
  }
  options.beforeImport?.()
  const log: string[] = []
  t.mock.method(globalThis, "fetch", async (url: any, init: any = {}) => {
    const path = new URL(String(url), "http://localhost").pathname
    log.push(`${init.method ?? "GET"} ${path}`)
    return options.fetch(path, init, log)
  })
  const m = await import(pathToFileURL(outfile).href)
  const { act } = m.React
  const root = m.createRoot(document.getElementById("root"))
  t.after(async () => {
    await act(async () => root.unmount())
    dom.window.close()
    for (const [name, descriptor] of saved) {
      if (descriptor) Object.defineProperty(globalThis, name, descriptor)
      else Reflect.deleteProperty(globalThis, name)
    }
    esbuild.stop()
    await rm(directory, { recursive: true, force: true })
  })
  await act(async () => root.render(m.React.createElement(m.Harness)))

  /** Deixa promessas e timers do React andarem por `ms` milissegundos. */
  const settle = (ms = 30) => act(async () => { await new Promise((resolve) => setTimeout(resolve, ms)) })
  /** Clique de mouse real (com bolha), como o navegador dispara. */
  const click = (element: Element) => act(async () => {
    element.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true, cancelable: true, button: 0 }))
  })
  /** Primeiro botão cujo texto (sem espaços nas pontas) é exatamente `label`. */
  const button = (label: string) => [...document.querySelectorAll("button")].find((item) => item.textContent?.trim() === label)
  /** Digita num input controlado pelo React (o setter nativo dispara o onChange). */
  const type = async (input: HTMLInputElement, value: string) => {
    const setter = Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype, "value")!.set!
    await act(async () => { setter.call(input, value); input.dispatchEvent(new dom.window.Event("input", { bubbles: true })) })
  }
  return { m, act, dom, log, settle, click, button, type }
}
