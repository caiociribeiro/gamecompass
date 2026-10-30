import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react"
import { apiError, apiGet } from "../lib/api"
import type { Game, HardwareCatalog } from "../types"
import { useSession } from "./SessionContext"

type Collection = { items: Game[]; issues: { appid: string; message: string }[] }
type CatalogValue = {
  games: Game[]
  hardware: HardwareCatalog
  gamesLoading: boolean
  hardwareLoading: boolean
  gamesError: string | null
  hardwareError: string | null
  gameIssues: Collection["issues"]
  discovered: boolean
  refresh: () => void
  loadGame: (appid: string) => Promise<Game>
  discoverGames: () => Promise<void>
}
const EMPTY: HardwareCatalog = { CPU: [], GPU: [], score_version: "manual_v1", source: "neo4j" }
const CatalogContext = createContext<CatalogValue | null>(null)

export function CatalogProvider({ children }: { children: ReactNode }) {
  const { user } = useSession()
  const userId = user?.id ?? ""
  const anchorIds = (user?.anchorIds ?? [])
    .filter((id) => /^[1-9][0-9]{0,9}$/.test(id))
    .slice(0, 3)
    .join(",")
  const [games, setGames] = useState<Game[]>([])
  const [hardware, setHardware] = useState<HardwareCatalog>(EMPTY)
  const [gamesLoading, setGamesLoading] = useState(false)
  const [hardwareLoading, setHardwareLoading] = useState(true)
  const [gamesError, setGamesError] = useState<string | null>(null)
  const [hardwareError, setHardwareError] = useState<string | null>(null)
  const [gameIssues, setGameIssues] = useState<Collection["issues"]>([])
  const [discovered, setDiscovered] = useState(false)
  const [revision, setRevision] = useState(0)
  const generation = useRef(0)
  const refresh = useCallback(() => setRevision((value) => value + 1), [])
  const loadGame = useCallback(async (appid: string) => {
    const token = generation.current
    const game = await apiGet<Game>(`/games/${encodeURIComponent(appid)}`)
    if (token !== generation.current) throw new DOMException("Consulta cancelada.", "AbortError")
    setGames((current) => [...current.filter((item) => item.id !== game.id), game])
    return game
  }, [])
  const discoverGames = useCallback(async () => {
    const token = generation.current
    setGamesLoading(true)
    setGamesError(null)
    try {
      const data = await apiGet<Collection>("/games/discover")
      if (token !== generation.current) return
      setGames((current) => [
        ...current.filter((game) => !data.items.some((item) => item.id === game.id)),
        ...data.items,
      ])
      setGameIssues(data.issues)
      setDiscovered(true)
    } catch (error) {
      if (token === generation.current) setGamesError(apiError(error))
    } finally {
      if (token === generation.current) setGamesLoading(false)
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    setHardwareLoading(true)
    setHardwareError(null)
    apiGet<HardwareCatalog>("/hardware", controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setHardware(data)
      })
      .catch((error) => {
        if (!controller.signal.aborted) {
          setHardware(EMPTY)
          setHardwareError(apiError(error))
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setHardwareLoading(false)
      })
    return () => controller.abort()
  }, [revision])

  useEffect(() => {
    const controller = new AbortController()
    generation.current += 1
    setGames([])
    setGameIssues([])
    setGamesError(null)
    setDiscovered(false)
    setGamesLoading(Boolean(anchorIds))
    // Nenhuma consulta de jogos para uma conta que ainda não escolheu âncoras.
    if (anchorIds) {
      apiGet<Collection>(`/games?appids=${encodeURIComponent(anchorIds)}`, controller.signal)
        .then((data) => {
          if (!controller.signal.aborted) {
            setGames(data.items)
            setGameIssues(data.issues)
          }
        })
        .catch((error) => {
          if (!controller.signal.aborted) setGamesError(apiError(error))
        })
        .finally(() => {
          if (!controller.signal.aborted) setGamesLoading(false)
        })
    }
    return () => controller.abort()
  }, [revision, anchorIds, userId])

  const value = useMemo(
    () => ({
      games,
      hardware,
      gamesLoading,
      hardwareLoading,
      gamesError,
      hardwareError,
      gameIssues,
      discovered,
      refresh,
      loadGame,
      discoverGames,
    }),
    [
      games,
      hardware,
      gamesLoading,
      hardwareLoading,
      gamesError,
      hardwareError,
      gameIssues,
      discovered,
      refresh,
      loadGame,
      discoverGames,
    ],
  )
  return <CatalogContext.Provider value={value}>{children}</CatalogContext.Provider>
}
export function useCatalog() {
  const value = useContext(CatalogContext)
  if (!value) throw new Error("useCatalog precisa estar dentro de CatalogProvider.")
  return value
}
