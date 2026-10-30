import type { UserProfile } from "../types"

export function migrateProfile(
  user: UserProfile,
  genres: readonly string[],
  themes: readonly string[],
): UserProfile {
  const steamProfile = user.catalogVersion === "steam-v1" || user.catalogVersion === "steam-v2"
  return {
    id: user.id,
    name: user.name,
    email: user.email,
    password: user.password,
    genres: Array.isArray(user.genres) ? user.genres.filter((genre) => genres.includes(genre)) : [],
    themes: Array.isArray(user.themes) ? user.themes.filter((theme) => themes.includes(theme)) : [],
    anchorIds:
      steamProfile && Array.isArray(user.anchorIds)
        ? [
            ...new Set(user.anchorIds.filter((id) => typeof id === "string" && /^[1-9][0-9]{0,9}$/.test(id))),
          ].slice(0, 3)
        : [],
    hardware: steamProfile ? user.hardware : null,
    catalogVersion: "steam-v2",
  }
}
