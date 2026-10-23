import { createContext, useContext, useMemo, useState, type ReactNode } from "react"
import { DEMO_USER } from "../data/demo"
import type { UserProfile } from "../types"

const USERS_KEY = "gamecompass.users.v1"
const SESSION_KEY = "gamecompass.session.v1"

type RegisterInput = {
  name: string
  email: string
  password: string
}

type SessionContextValue = {
  user: UserProfile | null
  login: (email: string, password: string) => string | null
  register: (input: RegisterInput) => string | null
  logout: () => void
  updateUser: (patch: Partial<Omit<UserProfile, "id" | "email">>) => void
  changePassword: (current: string, next: string) => string | null
}

const SessionContext = createContext<SessionContextValue | null>(null)

function isUser(value: unknown): value is UserProfile {
  if (!value || typeof value !== "object") return false
  const user = value as UserProfile
  return typeof user.id === "string" && typeof user.email === "string" && typeof user.password === "string"
}

function loadUsers() {
  try {
    const raw = localStorage.getItem(USERS_KEY)
    const parsed: unknown = raw ? JSON.parse(raw) : []
    const users = Array.isArray(parsed) ? parsed.filter(isUser) : []
    if (!users.some((user) => user.email === DEMO_USER.email)) {
      const next = [DEMO_USER, ...users]
      localStorage.setItem(USERS_KEY, JSON.stringify(next))
      return next
    }
    return users
  } catch {
    localStorage.setItem(USERS_KEY, JSON.stringify([DEMO_USER]))
    return [DEMO_USER]
  }
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [users, setUsers] = useState<UserProfile[]>(loadUsers)
  const [sessionId, setSessionId] = useState<string | null>(() => localStorage.getItem(SESSION_KEY))

  const user = users.find((item) => item.id === sessionId) ?? null

  const value = useMemo<SessionContextValue>(() => {
    function persist(next: UserProfile[]) {
      localStorage.setItem(USERS_KEY, JSON.stringify(next))
      setUsers(next)
    }

    function setSession(id: string | null) {
      setSessionId(id)
      if (id) localStorage.setItem(SESSION_KEY, id)
      else localStorage.removeItem(SESSION_KEY)
    }

    return {
      user,
      login(email, password) {
        const found = users.find(
          (item) => item.email === email.trim().toLowerCase() && item.password === password,
        )
        if (!found) return "E-mail ou senha não conferem."
        setSession(found.id)
        return null
      },
      register(input) {
        const name = input.name.trim()
        const email = input.email.trim().toLowerCase()
        if (name.length < 2) return "Informe seu nome."
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return "Informe um e-mail válido."
        if (input.password.length < 6) return "A senha precisa ter pelo menos 6 caracteres."
        if (users.some((item) => item.email === email)) {
          return "Já existe uma conta com esse e-mail neste navegador."
        }
        const created: UserProfile = {
          id: crypto.randomUUID(),
          name,
          email,
          password: input.password,
          genres: [],
          themes: [],
          anchorIds: [],
          hardware: null,
        }
        persist([...users, created])
        setSession(created.id)
        return null
      },
      logout() {
        setSession(null)
      },
      updateUser(patch) {
        if (!user) return
        persist(users.map((item) => (item.id === user.id ? { ...item, ...patch, id: item.id, email: item.email } : item)))
      },
      changePassword(current, next) {
        if (!user) return "Sessão expirada."
        if (user.password !== current) return "A senha atual não confere."
        if (next.length < 6) return "A nova senha precisa ter pelo menos 6 caracteres."
        persist(users.map((item) => (item.id === user.id ? { ...item, password: next } : item)))
        return null
      },
    }
  }, [user, users])

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export function useSession() {
  const value = useContext(SessionContext)
  if (!value) throw new Error("useSession precisa estar dentro de SessionProvider.")
  return value
}
