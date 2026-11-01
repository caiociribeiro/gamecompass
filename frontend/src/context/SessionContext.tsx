import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react"
import { ApiError, apiError, apiGet, apiPatch, apiPost } from "../lib/api"
import { scrubLegacyPasswords } from "../lib/legacyProfile"
import type { UserProfile } from "../types"

type RegisterInput = {
  name: string
  email: string
  password: string
}

type ProfilePatch = Partial<Omit<UserProfile, "id" | "email" | "catalogVersion">>

type SessionContextValue = {
  user: UserProfile | null
  /** "loading" enquanto a API confirma se já existe uma sessão válida. */
  status: "loading" | "ready"
  /** Falha ao falar com a API (verificação da sessão ou saída). */
  error: string | null
  /** Falha ao gravar o perfil no servidor. */
  saveError: string | null
  dismissSaveError: () => void
  login: (email: string, password: string) => Promise<string | null>
  register: (input: RegisterInput) => Promise<string | null>
  logout: () => Promise<void>
  updateUser: (patch: ProfilePatch) => void
  changePassword: (current: string, next: string) => Promise<string | null>
}

const SessionContext = createContext<SessionContextValue | null>(null)

export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [status, setStatus] = useState<"loading" | "ready">("loading")
  const [error, setError] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  // Todas as operações que dependem do cookie correm em fila: uma edição feita antes de
  // sair é enviada ainda com a sessão antiga, e nunca chega à conta seguinte.
  const chain = useRef<Promise<unknown>>(Promise.resolve())
  const pendingSaves = useRef(0)
  // Muda a cada entrada ou saída; descarta a resposta atrasada da verificação inicial.
  const epoch = useRef(0)

  const enqueue = useCallback(<T,>(task: () => Promise<T>): Promise<T> => {
    const result = chain.current.then(task)
    chain.current = result.then(() => undefined, () => undefined)
    return result
  }, [])

  useEffect(() => {
    scrubLegacyPasswords()
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
      return enqueue(async () => {
        try {
          const account = await apiPost<UserProfile>(path, body)
          epoch.current += 1
          setUser(account)
          setError(null)
          setSaveError(null)
          return null
        } catch (failure) {
          return apiError(failure)
        }
      })
    }

    return {
      user,
      status,
      error,
      saveError,
      dismissSaveError: () => setSaveError(null),
      login: (email, password) => enter("/auth/login", { email: email.trim().toLowerCase(), password }),
      register: (input) =>
        enter("/auth/register", { name: input.name.trim(), email: input.email.trim().toLowerCase(), password: input.password }),
      logout() {
        // A interface sai na hora; o servidor encerra a sessão logo depois, na ordem da fila.
        epoch.current += 1
        setUser(null)
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
        // Atualização otimista; o servidor confirma em seguida.
        setUser((current) => (current ? { ...current, ...patch } : current))
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
            if (pendingSaves.current === 1) {
              try {
                setUser(await apiGet<UserProfile>("/auth/me"))
              } catch {
                // API fora do ar: a edição local continua visível, mas o aviso permanece.
              }
            }
          } finally {
            pendingSaves.current -= 1
          }
        })
      },
      changePassword: (current, next) =>
        enqueue(async () => {
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
        }),
    }
  }, [user, status, error, saveError, enqueue])

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export function useSession() {
  const value = useContext(SessionContext)
  if (!value) throw new Error("useSession precisa estar dentro de SessionProvider.")
  return value
}
