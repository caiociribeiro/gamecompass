import { GENRES, THEMES } from "../data/preferences"
import { migrateProfile, type LegacyProfile } from "./migrateProfile"
import type { UserProfile } from "../types"

// Chaves da versão anterior, em que contas e senhas ficavam só no navegador.
const USERS_KEY = "gamecompass.users.v1"
const SESSION_KEY = "gamecompass.session.v1"

export type LegacyChoices = Pick<UserProfile, "genres" | "themes" | "anchorIds" | "hardware">

function readList(): Record<string, unknown>[] | null {
  try {
    const raw = localStorage.getItem(USERS_KEY)
    const parsed: unknown = raw ? JSON.parse(raw) : null
    return Array.isArray(parsed) ? parsed.filter((item) => item && typeof item === "object") : null
  } catch {
    return null
  }
}

function sameEmail(entry: Record<string, unknown>, email: string) {
  return typeof entry.email === "string" && entry.email.trim().toLowerCase() === email.trim().toLowerCase()
}

/**
 * Remove a sessão antiga e as senhas em texto puro, mantendo as escolhas de jogo
 * para a importação. Senhas antigas nunca são usadas como credencial.
 */
export function scrubLegacyPasswords(): void {
  try {
    localStorage.removeItem(SESSION_KEY)
    const list = readList()
    if (!list || !list.some((entry) => "password" in entry)) return
    localStorage.setItem(
      USERS_KEY,
      JSON.stringify(
        list.map((entry) => {
          const copy = { ...entry }
          delete copy.password
          return copy
        }),
      ),
    )
  } catch {
    // Sem acesso ao armazenamento local não há o que limpar.
  }
}

/** Escolhas guardadas neste navegador para o e-mail informado, ou null se não houver nenhuma. */
export function readLegacyChoices(email: string): LegacyChoices | null {
  const entry = readList()?.find((item) => sameEmail(item, email))
  if (!entry) return null
  const profile = migrateProfile(entry as unknown as LegacyProfile, GENRES, THEMES)
  const choices: LegacyChoices = {
    genres: profile.genres,
    themes: profile.themes,
    anchorIds: profile.anchorIds,
    hardware: profile.hardware,
  }
  return choices.genres.length || choices.themes.length || choices.anchorIds.length || choices.hardware ? choices : null
}

/** Apaga deste navegador a conta antiga do e-mail informado. */
export function discardLegacyAccount(email: string): void {
  try {
    const list = readList()
    if (list) localStorage.setItem(USERS_KEY, JSON.stringify(list.filter((item) => !sameEmail(item, email))))
  } catch {
    // Nada a fazer se o navegador bloquear o armazenamento.
  }
}
