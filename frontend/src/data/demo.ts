import type { UserProfile } from "../types"

export const DEMO_EMAIL = "demo@gamecompass.dev"
export const DEMO_PASSWORD = "demo123"

export const DEMO_USER: UserProfile = {
  id: "demo-user",
  name: "Demo",
  email: DEMO_EMAIL,
  password: DEMO_PASSWORD,
  genres: ["RPG", "Aventura", "Indie"],
  themes: ["Exploração", "Narrativa", "Fantasia"],
  anchorIds: ["hades", "hollow-knight", "the-witcher-3"],
  hardware: {
    cpuId: "r5-5600",
    gpuId: "rtx-3060",
    ramGb: 16,
    os: "Windows",
  },
}
