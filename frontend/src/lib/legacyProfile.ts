// Chaves da versão anterior, em que contas (com e-mail, senha e preferências) ficavam só no navegador.
const LEGACY_KEYS = ["gamecompass.users.v1", "gamecompass.session.v1"]

/** Apaga deste navegador tudo o que a versão antiga guardou. Os dados da conta ficam só no servidor. */
export function purgeLegacyStorage(): void {
  try {
    for (const key of LEGACY_KEYS) localStorage.removeItem(key)
  } catch {
    // Nada a fazer se o navegador bloquear o armazenamento.
  }
}
