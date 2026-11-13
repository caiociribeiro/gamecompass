import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react"
import { apiDelete, apiError, apiGet, apiPost, apiPut } from "../lib/api"
import { calculationProfile, type CalculationProfile } from "../lib/calculation"
import { discoveryFilters, RequestScope } from "../lib/discovery"
import type { ComparisonResult, Game, GameMatch, HardwareCatalog, Interaction, Reaction, RecommendationResult } from "../types"
import { useSession } from "./SessionContext"

type Collection = { items: Game[]; issues: { appid: string; message: string }[]; source?: string }
type CatalogValue = {
  games: Game[]; hardware: HardwareCatalog; gamesLoading: boolean; hardwareLoading: boolean
  gamesError: string | null; hardwareError: string | null; gameIssues: Collection["issues"]
  discovered: boolean; candidateSource: string | null; recommendations: RecommendationResult | null
  calculationKey: string
  refresh: () => void
  loadGame: (appid: string) => Promise<Game>
  compareGame: (appid: string, signal: AbortSignal) => Promise<GameMatch>
  discoverGames: () => Promise<void>
  /** Reações já enviadas nesta sessão; valem mais que o que veio na última resposta da API. */
  reactions: Record<string, Reaction | null>
  /** Jogos não curtidos que estão caindo da lista (animação) antes de sair de vez. */
  leaving: ReadonlySet<string>
  /** Verdadeiro quando uma curtida foi salva depois do último cálculo: a afinidade ainda não a considera. */
  reactionsStale: boolean
  reactToGame: (appid: string, reaction: Reaction | null) => Promise<void>
  recordView: (appid: string) => void
  clearHistory: () => Promise<number>
}
/** Duração da queda do card não curtido; sem animação para quem pede movimento reduzido. */
function fallMs() {
  return typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ? 0 : 700
}
const EMPTY: HardwareCatalog = { CPU: [], GPU: [], score_version: "manual_v1", source: "neo4j" }
const CatalogContext = createContext<CatalogValue | null>(null)

export function CatalogProvider({ children }: { children: ReactNode }) {
  const { user } = useSession()
  const userId = user?.id ?? ""
  const { anchor_ids: anchorIds, genres, tags } = discoveryFilters(user)
  const profileJson = JSON.stringify(calculationProfile(user))
  const profile = useMemo<CalculationProfile>(() => JSON.parse(profileJson), [profileJson])
  const [games, setGames] = useState<Game[]>([])
  const [hardware, setHardware] = useState<HardwareCatalog>(EMPTY)
  const [anchorLoading, setAnchorLoading] = useState(false)
  const [discoveryLoading, setDiscoveryLoading] = useState(false)
  const [hardwareLoading, setHardwareLoading] = useState(true)
  const [gamesError, setGamesError] = useState<string | null>(null)
  const [hardwareError, setHardwareError] = useState<string | null>(null)
  const [gameIssues, setGameIssues] = useState<Collection["issues"]>([])
  const [cache, setCache] = useState<{ key: string; data: RecommendationResult } | null>(null)
  const [revision, setRevision] = useState(0)
  const [reactions, setReactions] = useState<Record<string, Reaction | null>>({})
  const [reactionsStale, setReactionsStale] = useState(false)
  const [leaving, setLeaving] = useState<ReadonlySet<string>>(new Set())
  const generation = useRef(0)
  const discovery = useRef(new RequestScope())
  const requestedContent = useRef<string | null>(null)
  const contentKey = JSON.stringify([revision, userId, anchorIds, genres, tags])
  const calculationKey = JSON.stringify([revision, userId, profileJson])
  const previousKey = useRef(calculationKey)
  const recommendations = cache?.key === calculationKey ? cache.data : null
  const refresh = useCallback(() => setRevision((value) => value + 1), [])
  const loadGame = useCallback(async (appid: string) => {
    const token = generation.current
    const game = await apiGet<Game>(`/games/${encodeURIComponent(appid)}`)
    if (token !== generation.current) throw new DOMException("Consulta cancelada.", "AbortError")
    setGames((current) => [...current.filter((item) => item.id !== game.id), game])
    return game
  }, [])
  const compareGame = useCallback(async (appid: string, signal: AbortSignal) => {
    const token = generation.current
    const result = await apiPost<ComparisonResult>(`/games/${encodeURIComponent(appid)}/comparison`, profile, signal)
    if (signal.aborted || token !== generation.current) throw new DOMException("Consulta cancelada.", "AbortError")
    setGames((current) => [...current.filter((item) => item.id !== result.match.game.id), result.match.game])
    return result.match
  }, [profile])
  const discoverGames = useCallback(async () => {
    discovery.current.cancel()
    setCache(null)
    if (!userId || profile.anchorIds.length !== 3 || !profile.genres.length || !profile.themes.length || !profile.hardware) {
      setDiscoveryLoading(false)
      setGamesError("Complete as âncoras, preferências e o hardware antes de buscar sugestões.")
      return
    }
    const token = generation.current
    const ticket = discovery.current.start()
    requestedContent.current = contentKey
    setDiscoveryLoading(true)
    setGamesError(null)
    setCache(null)
    try {
      const data = await apiPost<RecommendationResult>("/recommendations", profile, ticket.signal)
      if (token !== generation.current || !ticket.isCurrent()) return
      const received = [...data.anchors, ...data.items.map((m) => m.game), ...data.pending.map((m) => m.game), ...data.excluded.map((m) => m.game)]
      setGames([...new Map(received.map((game) => [game.id, game])).values()])
      setGameIssues(data.issues)
      setCache({ key: calculationKey, data })
      setReactionsStale(false)
    } catch (error) {
      if (token === generation.current && ticket.isCurrent()) setGamesError(apiError(error))
    } finally {
      if (token === generation.current && ticket.isCurrent()) setDiscoveryLoading(false)
    }
  }, [userId, profile, contentKey, calculationKey])

  const reactToGame = useCallback(async (appid: string, reaction: Reaction | null) => {
    await apiPut<Interaction>(`/me/games/${encodeURIComponent(appid)}/reaction`, { reaction })
    setReactions((current) => ({ ...current, [appid]: reaction }))
    // Não curtir tira o jogo da lista (depois da queda do card); a curtida só entra na afinidade no próximo cálculo.
    if (reaction === "disliked") {
      const without = (matches: GameMatch[]) => matches.filter((match) => match.game.id !== appid)
      const remove = () => {
        setCache((current) => current && { ...current, data: {
          ...current.data, items: without(current.data.items), pending: without(current.data.pending), excluded: without(current.data.excluded) } })
        setLeaving((current) => { const next = new Set(current); next.delete(appid); return next })
      }
      const delay = fallMs()
      if (delay) {
        setLeaving((current) => new Set(current).add(appid))
        setTimeout(remove, delay)
      } else {
        remove()
      }
    }
    setReactionsStale(true)
  }, [])
  const recordView = useCallback((appid: string) => {
    // Registro silencioso: jogo fora do catálogo ou falha de rede não devem atrapalhar a leitura.
    apiPost(`/me/games/${encodeURIComponent(appid)}/view`, {}).catch(() => undefined)
  }, [])
  const clearHistory = useCallback(async () => {
    const result = await apiDelete<{ removed: number }>("/me/interactions")
    setReactions({})
    setReactionsStale(true)
    return result.removed
  }, [])

  useEffect(() => {
    setReactions({})
    setReactionsStale(false)
  }, [userId])

  useEffect(() => {
    const scope = discovery.current
    scope.cancel()
    requestedContent.current = null
    setDiscoveryLoading(false)
    setCache(null)
    setGameIssues([])
    setGamesError(null)
    setGames((current) => current.filter((game) => anchorIds.split(",").includes(game.id)))
    return () => scope.cancel()
  }, [contentKey, anchorIds])

  useEffect(() => {
    const changed = previousKey.current !== calculationKey
    previousKey.current = calculationKey
    // Após uma busca solicitada, trocar somente o hardware refaz o cálculo na API.
    if (changed && requestedContent.current === contentKey) void discoverGames()
  }, [calculationKey, contentKey, discoverGames])

  useEffect(() => {
    const controller = new AbortController()
    setHardwareLoading(true)
    setHardwareError(null)
    apiGet<HardwareCatalog>("/hardware", controller.signal)
      .then((data) => { if (!controller.signal.aborted) setHardware(data) })
      .catch((error) => {
        if (!controller.signal.aborted) { setHardware(EMPTY); setHardwareError(apiError(error)) }
      })
      .finally(() => { if (!controller.signal.aborted) setHardwareLoading(false) })
    return () => controller.abort()
  }, [revision])

  useEffect(() => {
    const controller = new AbortController()
    generation.current += 1
    setGames([])
    setGameIssues([])
    setGamesError(null)
    setCache(null)
    setAnchorLoading(Boolean(anchorIds))
    if (anchorIds) {
      apiGet<Collection>(`/games?appids=${encodeURIComponent(anchorIds)}`, controller.signal)
        .then((data) => {
          if (!controller.signal.aborted) { setGames(data.items); setGameIssues(data.issues) }
        })
        .catch((error) => { if (!controller.signal.aborted) setGamesError(apiError(error)) })
        .finally(() => { if (!controller.signal.aborted) setAnchorLoading(false) })
    }
    return () => controller.abort()
  }, [revision, anchorIds, userId])

  const value = useMemo(() => ({ games, hardware, gamesLoading: anchorLoading || discoveryLoading,
    hardwareLoading, gamesError, hardwareError, gameIssues, discovered: Boolean(recommendations), leaving,
    candidateSource: recommendations?.source ?? null, recommendations, calculationKey,
    refresh, loadGame, compareGame, discoverGames, reactions, reactionsStale, reactToGame, recordView, clearHistory }), [games, hardware, anchorLoading, discoveryLoading,
    hardwareLoading, gamesError, hardwareError, gameIssues, recommendations, calculationKey, refresh, loadGame, compareGame, discoverGames,
    reactions, reactionsStale, reactToGame, recordView, clearHistory, leaving])
  return <CatalogContext.Provider value={value}>{children}</CatalogContext.Provider>
}
export function useCatalog() {
  const value = useContext(CatalogContext)
  if (!value) throw new Error("useCatalog precisa estar dentro de CatalogProvider.")
  return value
}
