import type { UserProfile } from "../types"

export const DEMO_EMAIL = "demo@gamecompass.dev"
export const DEMO_PASSWORD = "demo123"

export const DEMO_USER: UserProfile = {
  id: "demo-user",
  name: "Demo",
  email: DEMO_EMAIL,
  password: DEMO_PASSWORD,
  genres: [],
  themes: [],
  anchorIds: [],
  hardware: null,
  catalogVersion: "steam-v2",
}
