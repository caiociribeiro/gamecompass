import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react"
import { ApiError, apiError, apiGet, apiPatch, apiPost } from "../lib/api"
import { purgeLegacyStorage } from "../lib/legacyProfile"
import type { UserProfile } from "../types"

type RegisterInput = {
  name: string
  email: string
  password: string
}

type ProfilePatch = Partial<Omit<UserProfile, "id" | "catalogVersion">>

type SessionContextValue = {
  user: UserProfile | null
  /** "loading" enquanto a API confirma se já existe uma sessão válida. */
  status: "loading" | "ready"
  /** Verdadeiro depois que a pessoa clicou em sair (a Landing é o destino, não o login). */
  signedOut: boolean
  /** Falha ao falar com a API (verificação da sessão ou saída). */
  error: string | null
  /** Falha ao gravar o perfil no servidor. */
  saveError: string | null
  /** Verdadeiro enquanto há alterações do perfil ainda a caminho do servidor. */
  saving: boolean
  dismissSaveError: () => void
  login: (email: string, password: string) => Promise<string | null>
  register: (input: RegisterInput) => Promise<string | null>
  logout: () => Promise<void>
  updateUser: (patch: ProfilePatch) => void
  changePassword: (current: string, next: string) => Promise<string | null>
}

/** Pausa nos cliques antes de enviar as edições do perfil. */
export const SAVE_DELAY_MS = 600

const SessionContext = createContext<SessionContextValue | null>(null)

export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [status, setStatus] = useState<"loading" | "ready">("loading")
  const [signedOut, setSignedOut] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  // Todas as operações que dependem do cookie correm em fila: uma edição feita antes de
  // sair é enviada ainda com a sessão antiga, e nunca chega à conta seguinte.
  const chain = useRef<Promise<unknown>>(Promise.resolve())
  const pendingSaves = useRef(0)
  // Muda a cada entrada ou saída; descarta a resposta atrasada da verificação inicial.
  const epoch = useRef(0)
  // Edições do perfil feitas em sequência (vários cliques) viajam juntas em um único PATCH.
  const draft = useRef<ProfilePatch | null>(null)
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const flushRef = useRef<() => void>(() => undefined)

  const enqueue = useCallback(<T,>(task: () => Promise<T>): Promise<T> => {
    const result = chain.current.then(task)
    chain.current = result.then(() => undefined, () => undefined)
    return result
  }, [])

  useEffect(() => {
    purgeLegacyStorage()
    const controller = new AbortController()
    const started = epoch.current
    apiGet<UserProfile>("/auth/me", controller.signal)
      .then((account) => {
        if (!controller.signal.aborted && epoch.current === started) setUser(account)
      })
      .catch((failure) => {
        if (controller.signal.aborted || epoch.current !== started) return
        if (!(failure instanceof ApiError && failure.status === 401)) setError(apiError(failure))
      })
      .finally(() => {
        if (!controller.signal.aborted) setStatus("ready")
      })
    return () => controller.abort()
  }, [])

  const value = useMemo<SessionContextValue>(() => {
    function enter(path: string, body: unknown) {
      flushRef.current()
      return enqueue(async () => {
        try {
          const account = await apiPost<UserProfile>(path, body)
          epoch.current += 1
          setUser(account)
          setSignedOut(false)
          setError(null)
          setSaveError(null)
          return null
        } catch (failure) {
          return apiError(failure)
        }
      })
    }

    function flush() {
      if (timer.current) clearTimeout(timer.current)
      timer.current = null
      const patch = draft.current
      draft.current = null
      if (!patch) return
      pendingSaves.current += 1
      void enqueue(async () => {
        try {
          await apiPatch("/me/profile", patch)
          setSaveError(null)
        } catch (failure) {
          if (failure instanceof ApiError && failure.status === 401) {
            epoch.current += 1
            setUser(null)
            return
          }
          setSaveError(`Não foi possível salvar no servidor. ${apiError(failure)}`)
          // Sem outras edições pendentes, volta a mostrar o que o servidor realmente guardou.
          if (pendingSaves.current === 1 && !draft.current) {
            try {
              setUser(await apiGet<UserProfile>("/auth/me"))
            } catch {
              // API fora do ar: a edição local continua visível, mas o aviso permanece.
            }
          }
        } finally {
          pendingSaves.current -= 1
          if (pendingSaves.current === 0 && !draft.current) setSaving(false)
        }
      })
    }
    flushRef.current = flush

    return {
      user,
      status,
      error,
      saveError,
      saving,
      signedOut,
      dismissSaveError: () => setSaveError(null),
      login: (email, password) => enter("/auth/login", { email: email.trim().toLowerCase(), password }),
      register: (input) =>
        enter("/auth/register", { name: input.name.trim(), email: input.email.trim().toLowerCase(), password: input.password }),
      logout() {
        // A interface sai na hora; o servidor encerra a sessão logo depois, na ordem da fila.
        // Edições ainda não enviadas saem antes, com a sessão antiga.
        flushRef.current()
        epoch.current += 1
        setUser(null)
        setSignedOut(true)
        setSaveError(null)
        return enqueue(async () => {
          try {
            await apiPost("/auth/logout", {})
          } catch {
            setError("Você saiu, mas não foi possível avisar o servidor. Tente sair novamente antes de fechar este navegador.")
          }
        })
      },
      updateUser(patch) {
        // Atualização otimista; o envio espera uma pausa nos cliques e junta tudo em um PATCH.
        setUser((current) => (current ? { ...current, ...patch } : current))
        draft.current = { ...draft.current, ...patch }
        setSaving(true)
        if (timer.current) clearTimeout(timer.current)
        timer.current = setTimeout(flush, SAVE_DELAY_MS)
      },
      changePassword: (current, next) => {
        flushRef.current()
        return enqueue(async () => {
          try {
            await apiPost("/auth/password", { current, next })
            return null
          } catch (failure) {
            if (failure instanceof ApiError && failure.status === 401) {
              epoch.current += 1
              setUser(null)
            }
            return apiError(failure)
          }
        })
      },
    }
  }, [user, status, error, saveError, saving, signedOut, enqueue])

  // Fechar ou esconder a aba envia o que ainda estiver esperando.
  useEffect(() => {
    const send = () => { if (document.visibilityState === "hidden") flushRef.current() }
    const leave = () => flushRef.current()
    document.addEventListener("visibilitychange", send)
    window.addEventListener("pagehide", leave)
    return () => {
      document.removeEventListener("visibilitychange", send)
      window.removeEventListener("pagehide", leave)
    }
  }, [])

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export function useSession() {
  const value = useContext(SessionContext)
  if (!value) throw new Error("useSession precisa estar dentro de SessionProvider.")
  return value
}
