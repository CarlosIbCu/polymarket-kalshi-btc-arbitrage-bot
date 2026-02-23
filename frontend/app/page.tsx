"use client"

import React, { useEffect, useState, useRef, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Button } from "@/components/ui/button"
import { AlertCircle, TrendingUp, Calculator, Volume2, VolumeX, ChevronDown, ChevronRight, Clock, Timer, Pause, Play } from "lucide-react"

// ─── Types ────────────────────────────────────────────────────────────────────

type MarketType = "15m" | "1h"
type AssetType = "btc" | "eth" | "sol" | "xrp"

interface MarketData {
  timestamp: string
  market_type: MarketType
  asset: string
  polymarket: {
    price_to_beat: number | null
    current_price: number | null
    prices: { Up: number; Down: number }
    slug: string
  } | null
  kalshi: {
    event_ticker: string
    // 15m fields
    yes_ask?: number
    no_ask?: number
    floor_strike?: number
    market?: { title: string; status: string; close_time: string }
    // 1h fields
    markets?: Array<{
      strike: number
      yes_ask: number     // cents
      no_ask: number
      yes_ask_dec: number // decimal
      no_ask_dec: number
      subtitle: string
    }>
  } | null
  checks: Array<{
    type: string
    poly_leg: string
    kalshi_leg: string
    kalshi_strike?: number
    poly_cost: number
    kalshi_cost: number
    total_cost: number
    is_valid: boolean
    overlap_size: number
    is_arbitrage: boolean
    margin: number
    poly_price_to_beat?: number
    kalshi_floor_strike?: number
    current_price?: number
  }>
  opportunities: Array<any>
  errors: string[]
}

interface ArbitrageHistoryItem {
  id: string
  timestamp: Date
  firstSeen: Date
  lastSeen: Date
  marketSlug: string
  asset: string
  type: string
  poly_leg: string
  kalshi_leg: string
  kalshi_strike?: number
  poly_cost: number
  kalshi_cost: number
  total_cost: number
  margin: number
  overlap_size?: number
  poly_price_to_beat?: number
  kalshi_floor_strike?: number
  kalshi_strike_label?: string
  kalshi_market_ticker?: string
  poly_outcome?: string
  kalshi_outcome?: string
  realized_return?: number
  priceRange: { low: number; high: number }
  duration: number
  isActive: boolean
  is_valid?: boolean
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const ASSET_LABELS: Record<AssetType, string> = { "btc": "Bitcoin", "eth": "Ethereum", "sol": "Solana", "xrp": "XRP" }

const MARKET_LABELS = (asset: AssetType, mt: MarketType) => `${ASSET_LABELS[asset]} ${mt}`

const HISTORY_KEY = (asset: AssetType, mt: MarketType) => `arbitrageHistory_${asset}_${mt}`

const GET_API_URL = (asset: AssetType, mt: MarketType) => `http://localhost:8000/arbitrage/${asset}/${mt}`

const formatStrikeLabel = (item: { kalshi_strike_label?: string, kalshi_strike?: number, kalshi_leg: string }) => {
  if (item.kalshi_strike_label) return item.kalshi_strike_label
  if (item.kalshi_strike != null) {
    const precision = item.kalshi_strike < 10 ? 5 : 2
    return `$${item.kalshi_strike.toLocaleString(undefined, { minimumFractionDigits: precision, maximumFractionDigits: 5 })} or ${item.kalshi_leg.toLowerCase() === 'yes' ? 'above' : 'below'}`
  }
  return null
}

function loadHistory(key: string): ArbitrageHistoryItem[] {
  try {
    const stored = localStorage.getItem(key)
    if (!stored) return []
    return JSON.parse(stored).map((item: any) => ({
      ...item,
      timestamp: new Date(item.timestamp),
      firstSeen: new Date(item.firstSeen),
      lastSeen: new Date(item.lastSeen),
    }))
  } catch { return [] }
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function Dashboard() {
  // Tab state
  const [selectedAsset, setSelectedAsset] = useState<AssetType>("btc")
  const [activeTab, setActiveTab] = useState<MarketType>("15m")
  const [enabled, setEnabled] = useState<Record<AssetType, Record<MarketType, boolean>>>({
    "btc": { "15m": true, "1h": true },
    "eth": { "15m": true, "1h": true },
    "sol": { "15m": true, "1h": true },
    "xrp": { "15m": true, "1h": true },
  })

  // Per-market data (Asset -> MarketType -> Data)
  const [marketData, setMarketData] = useState<Record<AssetType, Record<MarketType, MarketData | null>>>({
    "btc": { "15m": null, "1h": null },
    "eth": { "15m": null, "1h": null },
    "sol": { "15m": null, "1h": null },
    "xrp": { "15m": null, "1h": null },
  })
  const [lastUpdated, setLastUpdated] = useState<Record<AssetType, Record<MarketType, Date | null>>>({
    "btc": { "15m": null, "1h": null },
    "eth": { "15m": null, "1h": null },
    "sol": { "15m": null, "1h": null },
    "xrp": { "15m": null, "1h": null },
  })
  const [loading, setLoading] = useState<Record<AssetType, Record<MarketType, boolean>>>({
    "btc": { "15m": true, "1h": true },
    "eth": { "15m": true, "1h": true },
    "sol": { "15m": true, "1h": true },
    "xrp": { "15m": true, "1h": true },
  })

  // Table display options
  const [viewMode, setViewMode] = useState<"overlap" | "gap">("overlap")
  const [maxCostPct, setMaxCostPct] = useState<number>(100)
  const [minLegPct, setMinLegPct] = useState<number>(10)
  const [maxLegPct, setMaxLegPct] = useState<number>(90)
  const [historyView, setHistoryView] = useState<"all" | "dryrun">("all")

  // Per-market history
  const [historyBTC15m, setHistoryBTC15m] = useState<ArbitrageHistoryItem[]>(() => loadHistory(HISTORY_KEY("btc", "15m")))
  const [historyBTC1h, setHistoryBTC1h] = useState<ArbitrageHistoryItem[]>(() => loadHistory(HISTORY_KEY("btc", "1h")))
  const [historyETH15m, setHistoryETH15m] = useState<ArbitrageHistoryItem[]>(() => loadHistory(HISTORY_KEY("eth", "15m")))
  const [historyETH1h, setHistoryETH1h] = useState<ArbitrageHistoryItem[]>(() => loadHistory(HISTORY_KEY("eth", "1h")))
  const [historySOL15m, setHistorySOL15m] = useState<ArbitrageHistoryItem[]>(() => loadHistory(HISTORY_KEY("sol", "15m")))
  const [historySOL1h, setHistorySOL1h] = useState<ArbitrageHistoryItem[]>(() => loadHistory(HISTORY_KEY("sol", "1h")))
  const [historyXRP15m, setHistoryXRP15m] = useState<ArbitrageHistoryItem[]>(() => loadHistory(HISTORY_KEY("xrp", "15m")))
  const [historyXRP1h, setHistoryXRP1h] = useState<ArbitrageHistoryItem[]>(() => loadHistory(HISTORY_KEY("xrp", "1h")))
  const [expandedHistory, setExpandedHistory] = useState<Set<string>>(new Set())

  // Investment / profit calculator (merged into settings)
  const INVEST_PRESETS = ["None", "10", "100", "1000"] as const
  const [investPreset, setInvestPreset] = useState<"None" | "10" | "100" | "1000" | "custom">("None")
  const [customInvest, setCustomInvest] = useState<number>(0)
  const betAmount = investPreset === "None" ? 0 : investPreset === "custom" ? customInvest : Number(investPreset)
  const showCalculator = betAmount > 0

  // Sound
  const [soundEnabled, setSoundEnabled] = useState(true)
  const lastOppCounts = useRef<Record<MarketType, number>>({ "15m": 0, "1h": 0 })
  const audioContextRef = useRef<AudioContext | null>(null)

  // Track settings in a ref so they can be accessed in fetchMarket without recreating the interval
  const settingsRef = useRef({ maxCostPct, minLegPct, maxLegPct })
  useEffect(() => {
    settingsRef.current = { maxCostPct, minLegPct, maxLegPct }
  }, [maxCostPct, minLegPct, maxLegPct])

  // Opportunity counts per tab (for badge)
  const getOppCount = (asset: AssetType, mt: MarketType) => marketData[asset][mt]?.opportunities.length ?? 0

  const getHistory = (asset: AssetType, mt: MarketType) => {
    if (asset === "btc") return mt === "15m" ? historyBTC15m : historyBTC1h
    if (asset === "eth") return mt === "15m" ? historyETH15m : historyETH1h
    if (asset === "sol") return mt === "15m" ? historySOL15m : historySOL1h
    return mt === "15m" ? historyXRP15m : historyXRP1h
  }
  const setHistory = (asset: AssetType, mt: MarketType, update: (prev: ArbitrageHistoryItem[]) => ArbitrageHistoryItem[]) => {
    if (asset === "btc") {
      if (mt === "15m") setHistoryBTC15m(update); else setHistoryBTC1h(update)
    } else if (asset === "eth") {
      if (mt === "15m") setHistoryETH15m(update); else setHistoryETH1h(update)
    } else if (asset === "sol") {
      if (mt === "15m") setHistorySOL15m(update); else setHistorySOL1h(update)
    } else {
      if (mt === "15m") setHistoryXRP15m(update); else setHistoryXRP1h(update)
    }
  }

  // ── Audio ──────────────────────────────────────────────────────────────────

  const initAudio = () => {
    if (!audioContextRef.current)
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
    return audioContextRef.current
  }

  const playAlertSound = () => {
    if (!soundEnabled) return
    try {
      const ctx = initAudio()
      const beep = (delay: number, freq: number) => setTimeout(() => {
        const osc = ctx.createOscillator()
        const gain = ctx.createGain()
        osc.connect(gain); gain.connect(ctx.destination)
        osc.frequency.value = freq; osc.type = "sine"; gain.gain.value = 0.4
        osc.start(); osc.stop(ctx.currentTime + 0.15)
      }, delay)
      beep(0, 880); beep(200, 880); beep(400, 1100)
    } catch (e) { console.error("Audio error:", e) }
  }

  // ── Lookup key ─────────────────────────────────────────────────────────────

  const getOppKey = (opp: any, mt: MarketType) =>
    mt === "1h"
      ? `${opp.type}-${opp.poly_leg}-${opp.kalshi_strike ?? 0}`
      : `${opp.type}-${opp.poly_leg}`

  // ── History update logic ───────────────────────────────────────────────────

  const updateHistory = useCallback((asset: AssetType, mt: MarketType, currentOpps: any[], currentSlug: string) => {
    const setter = (update: (prev: ArbitrageHistoryItem[]) => ArbitrageHistoryItem[]) => setHistory(asset, mt, update)
    const now = new Date()
    const currentKeys = new Set(currentOpps.map(o => getOppKey(o, mt)))

    setter(prev => {
      let updated = prev.map(item => ({ ...item, priceRange: { ...item.priceRange } }))

      // Mark stale items inactive
      updated = updated.map(item => {
        if (!currentKeys.has(getOppKey(item, mt)) && item.isActive)
          return { ...item, isActive: false, duration: Math.floor((now.getTime() - item.firstSeen.getTime()) / 1000) }
        return item
      })

      currentOpps.forEach(opp => {
        if (opp.poly_cost <= 0 || opp.kalshi_cost <= 0) return
        const key = getOppKey(opp, mt)
        const existingIdx = updated.findIndex(i => getOppKey(i, mt) === key && i.isActive)

        if (existingIdx === -1) {
          updated.push({
            id: `${key}-${now.getTime()}`,
            timestamp: now, firstSeen: now, lastSeen: now,
            marketSlug: currentSlug,
            asset: asset.toUpperCase(),
            type: opp.type,
            poly_leg: opp.poly_leg,
            kalshi_leg: opp.kalshi_leg,
            kalshi_strike: opp.kalshi_strike,
            poly_cost: opp.poly_cost,
            kalshi_cost: opp.kalshi_cost,
            total_cost: opp.total_cost,
            margin: opp.margin,
            overlap_size: opp.overlap_size,
            poly_price_to_beat: opp.poly_price_to_beat,
            kalshi_floor_strike: opp.kalshi_floor_strike,
            kalshi_strike_label: opp.kalshi_strike_label,
            kalshi_market_ticker: opp.kalshi_market_ticker,
            priceRange: { low: opp.total_cost, high: 1.0 },
            duration: 0, isActive: true,
            is_valid: opp.is_valid ?? true,
          })
        } else {
          updated[existingIdx] = {
            ...updated[existingIdx],
            lastSeen: now,
            poly_cost: opp.poly_cost,
            kalshi_cost: opp.kalshi_cost,
            total_cost: opp.total_cost,
            margin: opp.margin,
            priceRange: {
              low: Math.min(updated[existingIdx].priceRange.low, opp.total_cost),
              high: 1.0,
            },
          }
        }
      })

      return updated.slice(-200)
    })
  }, [])

  // ── Fetch ──────────────────────────────────────────────────────────────────

  const fetchFailCounts = useRef<Record<MarketType, number>>({ "15m": 0, "1h": 0 })

  const fetchMarket = useCallback(async (asset: AssetType, mt: MarketType) => {
    if (!enabled[asset][mt]) return
    try {
      const res = await fetch(GET_API_URL(asset, mt))
      const json: MarketData = await res.json()

      fetchFailCounts.current[mt] = 0  // reset on success

      // Filter opportunities based on UI settings before checking for sound alert
      const filteredOppCount = (json.opportunities ?? []).filter((o: any) =>
        o.is_valid !== false &&
        o.total_cost * 100 <= settingsRef.current.maxCostPct &&
        o.poly_cost * 100 >= settingsRef.current.minLegPct && o.poly_cost * 100 <= settingsRef.current.maxLegPct &&
        o.kalshi_cost * 100 >= settingsRef.current.minLegPct && o.kalshi_cost * 100 <= settingsRef.current.maxLegPct
      ).length

      if (filteredOppCount > 0 && filteredOppCount > lastOppCounts.current[mt]) playAlertSound()
      lastOppCounts.current[mt] = filteredOppCount

      updateHistory(asset, mt, json.opportunities ?? [], json.polymarket?.slug ?? "unknown")

      setMarketData(prev => ({ ...prev, [asset]: { ...prev[asset], [mt]: json } }))
      setLastUpdated(prev => ({ ...prev, [asset]: { ...prev[asset], [mt]: new Date() } }))
      setLoading(prev => ({ ...prev, [asset]: { ...prev[asset], [mt]: false } }))
    } catch (err) {
      fetchFailCounts.current[mt]++
      const n = fetchFailCounts.current[mt]
      if (n === 1) console.warn(`[${asset} ${mt}] Backend unreachable — retrying...`)
      else if (n % 10 === 0) console.warn(`[${asset} ${mt}] Still unreachable after ${n} attempts`)
    }
  }, [enabled, updateHistory])

  useEffect(() => {
    const intervals: Record<string, NodeJS.Timeout> = {}

      ; (["btc", "eth", "sol", "xrp"] as AssetType[]).forEach(asset => {
        (["15m", "1h"] as MarketType[]).forEach(mt => {
          if (enabled[asset][mt]) {
            fetchMarket(asset, mt)
            intervals[`${asset}_${mt}`] = setInterval(() => fetchMarket(asset, mt), 250)
          }
        })
      })

    return () => Object.values(intervals).forEach(clearInterval)
  }, [enabled, fetchMarket])

  // Persist histories
  useEffect(() => {
    try { localStorage.setItem(HISTORY_KEY("btc", "15m"), JSON.stringify(historyBTC15m)) } catch { }
  }, [historyBTC15m])
  useEffect(() => {
    try { localStorage.setItem(HISTORY_KEY("btc", "1h"), JSON.stringify(historyBTC1h)) } catch { }
  }, [historyBTC1h])
  useEffect(() => {
    try { localStorage.setItem(HISTORY_KEY("eth", "15m"), JSON.stringify(historyETH15m)) } catch { }
  }, [historyETH15m])
  useEffect(() => {
    try { localStorage.setItem(HISTORY_KEY("eth", "1h"), JSON.stringify(historyETH1h)) } catch { }
  }, [historyETH1h])
  useEffect(() => {
    try { localStorage.setItem(HISTORY_KEY("sol", "15m"), JSON.stringify(historySOL15m)) } catch { }
  }, [historySOL15m])
  useEffect(() => {
    try { localStorage.setItem(HISTORY_KEY("sol", "1h"), JSON.stringify(historySOL1h)) } catch { }
  }, [historySOL1h])
  useEffect(() => {
    try { localStorage.setItem(HISTORY_KEY("xrp", "15m"), JSON.stringify(historyXRP15m)) } catch { }
  }, [historyXRP15m])
  useEffect(() => {
    try { localStorage.setItem(HISTORY_KEY("xrp", "1h"), JSON.stringify(historyXRP1h)) } catch { }
  }, [historyXRP1h])

  // ── Utils ──────────────────────────────────────────────────────────────────

  const toggleHistoryExpand = (id: string) => setExpandedHistory(prev => {
    const s = new Set(prev)
    s.has(id) ? s.delete(id) : s.add(id)
    return s
  })

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
  }

  const getRealizedProfit = (opp: { margin: number; total_cost: number }) => {
    if (!showCalculator || betAmount <= 0) return null
    return (betAmount / opp.total_cost) - betAmount
  }

  const getContractDetails = (opp: { poly_cost: number; kalshi_cost: number; total_cost: number }) => {
    if (!showCalculator || betAmount <= 0 || opp.total_cost <= 0) return null
    const polyAlloc = betAmount * (opp.poly_cost / opp.total_cost)
    const kalshiAlloc = betAmount * (opp.kalshi_cost / opp.total_cost)
    const units = betAmount / opp.total_cost
    return {
      polyAllocation: polyAlloc,
      kalshiAllocation: kalshiAlloc,
      polyContracts: opp.poly_cost > 0 ? polyAlloc / opp.poly_cost : 0,
      kalshiContracts: opp.kalshi_cost > 0 ? kalshiAlloc / opp.kalshi_cost : 0,
      totalUnits: units,
      payout: units,
    }
  }

  // ── Resolution Syncing ─────────────────────────────────────────────────────

  const checkResolutions = useCallback(async () => {
    const assets: AssetType[] = ["btc", "eth", "sol", "xrp"];
    const timeframes: MarketType[] = ["15m", "1h"];

    for (const asset of assets) {
      for (const mt of timeframes) {
        const history = getHistory(asset, mt);
        const setHistory = asset === "btc" ? (mt === "15m" ? setHistoryBTC15m : setHistoryBTC1h) :
          asset === "eth" ? (mt === "15m" ? setHistoryETH15m : setHistoryETH1h) :
            asset === "sol" ? (mt === "15m" ? setHistorySOL15m : setHistorySOL1h) :
              (mt === "15m" ? setHistoryXRP15m : setHistoryXRP1h);

        // Find items that need resolution: inactive, has ticker, no final outcome recorded
        const needsSync = history.filter(i => !i.isActive && i.kalshi_market_ticker && i.poly_outcome === undefined);

        for (const item of needsSync) {
          try {
            const res = await fetch(`http://localhost:8000/market-outcome?poly_slug=${item.marketSlug}&kalshi_ticker=${item.kalshi_market_ticker}`);
            const data = await res.json();

            if (data.resolved) {
              setHistory(prev => prev.map(old => {
                if (old.id !== item.id) return old;

                // Calculate return
                const units = betAmount / old.total_cost;
                const polyWon = data.poly_outcome?.toLowerCase() === old.poly_leg.toLowerCase();
                const kalshiWon = data.kalshi_outcome?.toLowerCase() === old.kalshi_leg.toLowerCase();
                const winCount = (polyWon ? 1 : 0) + (kalshiWon ? 1 : 0);

                return {
                  ...old,
                  poly_outcome: data.poly_outcome,
                  kalshi_outcome: data.kalshi_outcome,
                  realized_return: units * winCount
                };
              }));
            }
          } catch (e) {
            console.error("Error syncing resolution:", e);
          }
        }
      }
    }
  }, [betAmount, historyBTC15m, historyBTC1h, historyETH15m, historyETH1h, historySOL15m, historySOL1h, historyXRP15m, historyXRP1h]);

  useEffect(() => {
    const timer = setInterval(checkResolutions, 60000); // Check every 60s
    return () => clearInterval(timer);
  }, [checkResolutions]);

  // ── Render helpers ─────────────────────────────────────────────────────────

  const data = marketData[selectedAsset][activeTab]
  const historyForTab = getHistory(selectedAsset, activeTab)
  const isTabEnabled = enabled[selectedAsset][activeTab]
  const isTabLoading = loading[selectedAsset][activeTab]
  const tabLastUpdated = lastUpdated[selectedAsset][activeTab]

  const visibleOpps = data
    ? data.opportunities.filter((o: any) =>
      o.is_valid !== false &&
      o.total_cost * 100 <= maxCostPct &&
      o.poly_cost * 100 >= minLegPct && o.poly_cost * 100 <= maxLegPct &&
      o.kalshi_cost * 100 >= minLegPct && o.kalshi_cost * 100 <= maxLegPct
    )
    : []

  const bestOpp = visibleOpps.length > 0
    ? visibleOpps.reduce((p, c) => p.margin > c.margin ? p : c)
    : null

  const groupedHistory = historyForTab.reduce((groups, item) => {
    const slug = item.marketSlug || "unknown"
    if (!groups[slug]) groups[slug] = []
    groups[slug].push(item)
    return groups
  }, {} as Record<string, ArbitrageHistoryItem[]>)

  const groupedHistoryArray = Object.entries(groupedHistory).map(([slug, items]) => ({
    slug, opportunities: items,
    activeCount: items.filter(i => i.isActive).length,
  }))

  // ── JSX ────────────────────────────────────────────────────────────────────

  return (
    <div className="p-8 space-y-6 bg-slate-50 min-h-screen">

      {/* ── Header ── */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold tracking-tight">Arbitrage Bot Dashboard</h1>
          <Badge variant="outline" className="animate-pulse bg-green-100 text-green-800 border-green-200">
            <span className="w-2 h-2 rounded-full bg-green-500 mr-2"></span>Live
          </Badge>
        </div>
        <div className="flex items-center gap-4">
          <Button
            variant={soundEnabled ? "default" : "outline"}
            size="sm"
            onClick={() => setSoundEnabled(!soundEnabled)}
            className={soundEnabled ? "bg-green-600 hover:bg-green-700" : ""}
            title="Sound Alert"
          >
            {soundEnabled ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
          </Button>
          {tabLastUpdated && (
            <div className="text-sm text-muted-foreground">
              Last updated: {tabLastUpdated.toLocaleTimeString()}
            </div>
          )}
        </div>
      </div>

      {/* ── Asset & Market Tabs ── */}
      <Card className="border-slate-200">
        <CardContent className="pt-4 pb-4">
          <div className="flex flex-wrap gap-6 items-center">

            {/* Asset Selector */}
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-slate-600">Asset:</span>
              <div className="flex bg-slate-100 p-1 rounded-lg">
                {(["btc", "eth", "sol", "xrp"] as AssetType[]).map(asset => (
                  <button
                    key={asset}
                    onClick={() => setSelectedAsset(asset)}
                    className={`px-4 py-1.5 rounded-md text-sm font-bold transition-all ${selectedAsset === asset
                      ? "bg-white text-blue-700 shadow-sm"
                      : "text-slate-500 hover:text-slate-700"
                      }`}
                  >
                    {ASSET_LABELS[asset]}
                  </button>
                ))}
              </div>
            </div>

            <div className="h-8 w-px bg-slate-200 hidden md:block" />

            {/* Market Selector */}
            <div className="flex flex-wrap gap-3 items-center">
              <span className="text-sm font-medium text-slate-600">Period:</span>

              {(["15m", "1h"] as MarketType[]).map(mt => {
                const oppCount = getOppCount(selectedAsset, mt)
                const isActive = activeTab === mt
                const isOn = enabled[selectedAsset][mt]

                return (
                  <div key={mt} className="flex items-center gap-1">
                    {/* Tab button */}
                    <button
                      onClick={() => setActiveTab(mt)}
                      className={`relative flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all border-2 ${isActive
                        ? "border-blue-500 bg-blue-50 text-blue-700 shadow-sm"
                        : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50"
                        } ${!isOn ? "opacity-50" : ""}`}
                    >
                      <Clock className="h-4 w-4" />
                      {mt === "15m" ? "15-Minute" : "1-Hour"}
                      {oppCount > 0 && isOn && (
                        <span className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-green-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center animate-pulse">
                          {oppCount}
                        </span>
                      )}
                    </button>

                    {/* Enable/Disable toggle */}
                    <button
                      onClick={() => setEnabled(prev => ({
                        ...prev,
                        [selectedAsset]: { ...prev[selectedAsset], [mt]: !prev[selectedAsset][mt] }
                      }))}
                      title={isOn ? `Disable polling` : `Enable polling`}
                      className={`p-1.5 rounded-md border transition-all ${isOn
                        ? "border-green-300 bg-green-50 text-green-600 hover:bg-green-100"
                        : "border-red-300 bg-red-50 text-red-500 hover:bg-red-100"
                        }`}
                    >
                      {isOn ? <Play className="h-3 w-3 fill-current" /> : <Pause className="h-3 w-3 fill-current" />}
                    </button>
                  </div>
                )
              })}

              <div className="ml-auto text-xs text-slate-400">
                {isTabEnabled ? "Polling every 1s" : "Polling paused"}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ── Paused Banner ── */}
      {!isTabEnabled && (
        <div className="bg-amber-50 border border-amber-200 text-amber-700 px-4 py-3 rounded-md flex items-center gap-2 text-sm">
          <Pause className="h-4 w-4" />
          <span>
            <strong>{MARKET_LABELS(selectedAsset, activeTab)}</strong> polling is paused. Data shown is from the last fetch.
            Click the <Play className="h-3 w-3 inline mx-0.5" /> button to resume.
          </span>
        </div>
      )}

      {/* ── Loading ── */}
      {isTabLoading && isTabEnabled && (
        <div className="text-center py-8 text-muted-foreground">Loading {MARKET_LABELS(selectedAsset, activeTab)} market data…</div>
      )}

      {!isTabLoading && data && (
        <>
          {/* ── Errors ── */}
          {data.errors.length > 0 && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md flex items-start gap-2">
              <AlertCircle className="h-5 w-5 mt-0.5" />
              <div>
                <strong className="font-bold block mb-1">Errors:</strong>
                <ul className="list-disc ml-5 text-sm">
                  {data.errors.map((err, i) => <li key={i}>{err}</li>)}
                </ul>
              </div>
            </div>
          )}

          {/* Calculator card removed — now inline in Arbitrage Analysis header */}



          {/* ── Best Opportunity Banner ── */}

          {bestOpp && (
            <Card className="bg-gradient-to-r from-green-50 to-emerald-50 border-green-200 shadow-sm">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2 text-green-700">
                  <TrendingUp className="h-5 w-5" />
                  <CardTitle>Best Opportunity — {MARKET_LABELS(selectedAsset, activeTab)}</CardTitle>
                </div>
                <CardDescription>Risk-free arbitrage with highest margin</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col md:flex-row justify-between items-center gap-4">
                  <div className="text-center md:text-left">
                    <div className="text-sm text-muted-foreground">Profit Margin</div>
                    <div className="text-4xl font-bold text-green-700">${bestOpp.margin.toFixed(3)}</div>
                    <div className="text-xs text-green-600 font-medium">per unit</div>
                    {showCalculator && betAmount > 0 && (
                      <div className="mt-2 pt-2 border-t border-green-200">
                        <div className="text-xs text-green-600">Realized Profit</div>
                        <div className="text-2xl font-bold text-green-700">${getRealizedProfit(bestOpp)?.toFixed(2)}</div>
                      </div>
                    )}
                  </div>
                  <div className="flex-1 bg-white p-4 rounded-lg border border-green-100 w-full">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-semibold text-slate-700">Strategy</span>
                      <Badge className="bg-green-600">Buy Both</Badge>
                    </div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Polymarket {bestOpp.poly_leg}</span>
                      <span className="font-mono">${bestOpp.poly_cost.toFixed(3)}</span>
                    </div>
                    <div className="flex justify-between text-sm mb-3">
                      <span>
                        Kalshi {bestOpp.kalshi_leg}
                        {bestOpp.kalshi_strike ? ` ($${bestOpp.kalshi_strike.toLocaleString()})` : ""}
                      </span>
                      <span className="font-mono">${bestOpp.kalshi_cost.toFixed(3)}</span>
                    </div>
                    <div className="pt-2 border-t border-dashed border-slate-200 flex justify-between font-bold">
                      <span>Total Cost</span>
                      <span>${bestOpp.total_cost.toFixed(3)}</span>
                    </div>
                    {showCalculator && betAmount > 0 && getContractDetails(bestOpp) && (
                      <>
                        <div className="mt-3 pt-3 border-t border-green-200">
                          <div className="text-xs text-green-600 font-medium mb-2">Contract Breakdown</div>
                          <div className="space-y-1 text-xs">
                            <div className="flex justify-between">
                              <span className="text-slate-600">Polymarket {bestOpp.poly_leg}:</span>
                              <span className="font-mono">${getContractDetails(bestOpp)?.polyAllocation.toFixed(2)} → {getContractDetails(bestOpp)?.polyContracts.toFixed(2)} contracts</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-600">Kalshi {bestOpp.kalshi_leg}:</span>
                              <span className="font-mono">${getContractDetails(bestOpp)?.kalshiAllocation.toFixed(2)} → {getContractDetails(bestOpp)?.kalshiContracts.toFixed(2)} contracts</span>
                            </div>
                            <div className="flex justify-between font-medium pt-1 border-t border-green-100">
                              <span>Investment: ${betAmount}</span>
                              <span className="font-mono text-green-700">→ Profit: ${getRealizedProfit(bestOpp)?.toFixed(2)}</span>
                            </div>
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* ── Market Info Cards ── */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Polymarket */}
            <Card>
              <CardHeader>
                <CardTitle>Polymarket</CardTitle>
                <CardDescription>{data.polymarket?.slug ?? "—"}</CardDescription>
              </CardHeader>
              <CardContent>
                {data.polymarket ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-slate-100 p-3 rounded-md">
                        <div className="text-xs text-muted-foreground uppercase font-bold">Price to Beat</div>
                        <div className="text-xl font-mono font-semibold">
                          {data.polymarket.price_to_beat != null
                            ? `$${data.polymarket.price_to_beat.toLocaleString(undefined, { maximumFractionDigits: 2 })}`
                            : "—"}
                        </div>
                      </div>
                      <div className="bg-slate-100 p-3 rounded-md">
                        <div className="text-xs text-muted-foreground uppercase font-bold">Current Price</div>
                        <div className="text-xl font-mono font-semibold">
                          {data.polymarket.current_price != null
                            ? `$${data.polymarket.current_price.toLocaleString(undefined, { maximumFractionDigits: 2 })}`
                            : "—"}
                        </div>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center text-sm">
                        <span>YES (Up) Contract</span>
                        <span className="font-mono font-medium">
                          {Math.round((data.polymarket.prices.Up ?? 0) * 100)}¢ (${data.polymarket.prices.Up?.toFixed(3) ?? "—"})
                        </span>
                      </div>
                      <Progress value={data.polymarket.prices.Up * 100} className="h-2 bg-slate-100" indicatorClassName="bg-green-500" />
                      <div className="flex justify-between items-center text-sm mt-2">
                        <span>NO (Down) Contract</span>
                        <span className="font-mono font-medium">
                          {Math.round((data.polymarket.prices.Down ?? 0) * 100)}¢ (${data.polymarket.prices.Down?.toFixed(3) ?? "—"})
                        </span>
                      </div>
                      <Progress value={data.polymarket.prices.Down * 100} className="h-2 bg-slate-100" indicatorClassName="bg-red-500" />
                    </div>

                  </div>
                ) : <div className="text-muted-foreground text-sm">No data</div>}
              </CardContent>
            </Card>

            {/* Kalshi */}
            <Card>
              <CardHeader>
                <CardTitle>Kalshi</CardTitle>
                <CardDescription>{data.kalshi?.event_ticker ?? "—"}</CardDescription>
              </CardHeader>
              <CardContent>
                {data.kalshi ? (
                  activeTab === "15m" ? (
                    /* 15m: binary Yes/No */
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-slate-100 p-3 rounded-md">
                          <div className="text-xs text-muted-foreground uppercase font-bold">Price to Beat</div>
                          <div className="text-xl font-mono font-semibold">
                            ${data.kalshi.floor_strike?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? "—"}
                          </div>
                        </div>
                        <div className="bg-slate-100 p-3 rounded-md">
                          <div className="text-xs text-muted-foreground uppercase font-bold">Status</div>
                          <div className="text-sm font-semibold capitalize">{data.kalshi.market?.status ?? "active"}</div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between items-center text-sm">
                          <span>YES (Up) Contract</span>
                          <span className="font-mono font-medium">
                            {Math.round((data.kalshi.yes_ask ?? 0) * 100)}¢ (${data.kalshi.yes_ask?.toFixed(3) ?? "—"})
                          </span>
                        </div>
                        <Progress value={(data.kalshi.yes_ask ?? 0) * 100} className="h-2 bg-slate-100" indicatorClassName="bg-green-500" />
                        <div className="flex justify-between items-center text-sm mt-2">
                          <span>NO (Down) Contract</span>
                          <span className="font-mono font-medium">
                            {Math.round((data.kalshi.no_ask ?? 0) * 100)}¢ (${data.kalshi.no_ask?.toFixed(3) ?? "—"})
                          </span>
                        </div>
                        <Progress value={(data.kalshi.no_ask ?? 0) * 100} className="h-2 bg-slate-100" indicatorClassName="bg-red-500" />
                      </div>
                    </div>
                  ) : (
                    /* 1h: multi-strike ladder */
                    <div className="space-y-3 max-h-[220px] overflow-y-auto pr-2">
                      {(data.kalshi.markets ?? [])
                        .filter(m => {
                          const ptb = data.polymarket?.price_to_beat ?? 0
                          return ptb === 0 || Math.abs(m.strike - ptb) < 2500
                        })
                        .map((m, i) => (
                          <div key={i} className="text-sm border-b pb-2 last:border-0">
                            <div className="flex justify-between font-medium mb-1">
                              <span>{m.subtitle || `$${m.strike.toLocaleString()}`}</span>
                            </div>
                            <div className="flex justify-between text-xs text-muted-foreground mb-1">
                              <span>Yes: {m.yes_ask}¢</span>
                              <span>No: {m.no_ask}¢</span>
                            </div>
                            <div className="flex h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                              <div className="bg-green-500 h-full" style={{ width: `${m.yes_ask}%` }}></div>
                              <div className="bg-red-500 h-full" style={{ width: `${m.no_ask}%` }}></div>
                            </div>
                          </div>
                        ))
                      }
                    </div>
                  )
                ) : <div className="text-muted-foreground text-sm">No data</div>}
              </CardContent>
            </Card>
          </div>

          {/* ── Live Opportunity Cards ── */}
          {visibleOpps.length > 0 && (
            <div className="space-y-3">
              {visibleOpps.map((opp: any, i: number) => {
                const profit = getRealizedProfit(opp)
                const details = getContractDetails(opp)
                return (
                  <div
                    key={i}
                    className="border-l-4 border-green-500 bg-green-50 rounded-lg p-4 flex flex-wrap items-center justify-between gap-4"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse" />
                      <div>
                        <div className="font-semibold text-green-800 text-sm">Arbitrage Opportunity Detected</div>
                        <div className="text-xs text-green-700 mt-0.5">
                          Poly {opp.poly_leg} @ ${opp.poly_cost.toFixed(3)} + Kalshi {opp.kalshi_leg} @ ${opp.kalshi_cost.toFixed(3)}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="text-center">
                        <div className="text-[10px] uppercase text-green-600 font-medium">Total Cost</div>
                        <div className="font-mono font-bold text-green-800">${opp.total_cost.toFixed(3)}</div>
                        <div className="text-[10px] text-green-600">{Math.round(opp.total_cost * 100)}%</div>
                      </div>
                      <div className="text-center">
                        <div className="text-[10px] uppercase text-green-600 font-medium">Margin</div>
                        <div className="font-mono font-bold text-green-800">+${opp.margin.toFixed(4)}</div>
                        <div className="text-[10px] text-green-600">{(opp.margin * 100).toFixed(2)}%</div>
                      </div>
                      {betAmount > 0 && profit != null && (
                        <div className="text-center">
                          <div className="text-[10px] uppercase text-blue-600 font-medium">Profit (${betAmount})</div>
                          <div className="font-mono font-bold text-blue-800">+${profit.toFixed(2)}</div>
                          {details && (
                            <div className="text-[10px] text-blue-600">
                              {details.polyContracts.toFixed(1)}p + {details.kalshiContracts.toFixed(1)}k
                            </div>
                          )}
                        </div>
                      )}
                      <Badge className="bg-green-600 text-white">{opp.type}</Badge>
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {/* ── Arbitrage Analysis Table ── */}
          <Card>
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <CardTitle>Arbitrage Analysis — {MARKET_LABELS(selectedAsset, activeTab)}</CardTitle>
                  <CardDescription>Real-time comparison of all potential strategies</CardDescription>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  {/* Overlap / Gap segmented toggle */}
                  <div className="flex rounded-md border border-slate-200 overflow-hidden text-xs font-medium">
                    <button
                      onClick={() => setViewMode("overlap")}
                      className={`px-3 py-1.5 transition-colors ${viewMode === "overlap"
                        ? "bg-green-600 text-white"
                        : "bg-white text-slate-600 hover:bg-slate-50"
                        }`}
                    >
                      Overlap
                    </button>
                    <button
                      onClick={() => setViewMode("gap")}
                      className={`px-3 py-1.5 transition-colors border-l border-slate-200 ${viewMode === "gap"
                        ? "bg-amber-500 text-white"
                        : "bg-white text-slate-600 hover:bg-slate-50"
                        }`}
                    >
                      Gap
                    </button>
                  </div>
                  {/* Max total cost % filter */}
                  <div className="flex items-center gap-1.5 text-xs">
                    <span className="text-slate-500 whitespace-nowrap">Max cost:</span>
                    <input
                      type="number"
                      value={maxCostPct}
                      min={1}
                      max={100}
                      step={1}
                      onChange={e => setMaxCostPct(Math.min(100, Math.max(1, Number(e.target.value))))}
                      className="w-16 px-2 py-1 border border-slate-200 rounded-md text-xs text-right"
                    />
                    <span className="text-slate-500">%</span>
                  </div>
                  {/* Leg price range filter */}
                  <div className="flex items-center gap-1.5 text-xs">
                    <span className="text-slate-500 whitespace-nowrap">Leg range:</span>
                    <input
                      type="number"
                      value={minLegPct}
                      min={1}
                      max={maxLegPct - 1}
                      step={1}
                      onChange={e => setMinLegPct(Math.min(maxLegPct - 1, Math.max(1, Number(e.target.value))))}
                      className="w-14 px-2 py-1 border border-slate-200 rounded-md text-xs text-right"
                      title="Min leg price %"
                    />
                    <span className="text-slate-400">–</span>
                    <input
                      type="number"
                      value={maxLegPct}
                      min={minLegPct + 1}
                      max={99}
                      step={1}
                      onChange={e => setMaxLegPct(Math.min(99, Math.max(minLegPct + 1, Number(e.target.value))))}
                      className="w-14 px-2 py-1 border border-slate-200 rounded-md text-xs text-right"
                      title="Max leg price %"
                    />
                    <span className="text-slate-500">%</span>
                    <span className="text-slate-400 text-[10px] ml-0.5">per leg</span>
                  </div>
                  {/* Investment selector */}
                  <div className="flex items-center gap-1.5 text-xs">
                    <span className="text-slate-500 whitespace-nowrap">Investment:</span>
                    <div className="flex rounded-md border border-slate-200 overflow-hidden font-medium">
                      {INVEST_PRESETS.map(p => (
                        <button
                          key={p}
                          onClick={() => setInvestPreset(p as any)}
                          className={`px-2 py-1.5 transition-colors border-r border-slate-200 last:border-r-0 ${investPreset === p
                            ? "bg-blue-600 text-white"
                            : "bg-white text-slate-600 hover:bg-slate-50"
                            }`}
                        >
                          {p === "None" ? "None" : `$${p}`}
                        </button>
                      ))}
                      <button
                        onClick={() => setInvestPreset("custom")}
                        className={`px-2 py-1.5 transition-colors ${investPreset === "custom"
                          ? "bg-blue-600 text-white"
                          : "bg-white text-slate-600 hover:bg-slate-50"
                          }`}
                      >
                        Custom
                      </button>
                    </div>
                    {investPreset === "custom" && (
                      <input
                        type="number"
                        value={customInvest}
                        min={0}
                        step={10}
                        onChange={e => setCustomInvest(Math.max(0, Number(e.target.value)))}
                        placeholder="Amount"
                        className="w-20 px-2 py-1 border border-slate-200 rounded-md text-xs"
                      />
                    )}
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[120px]">Type</TableHead>
                    <TableHead>Strategy</TableHead>
                    {activeTab === "1h" && <TableHead>Kalshi Strike</TableHead>}
                    <TableHead>Cost Analysis</TableHead>
                    <TableHead className="text-right">Total Cost</TableHead>
                    <TableHead className="text-right">Overlap</TableHead>
                    <TableHead className="text-right">Result</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.checks
                    .filter(check =>
                      (viewMode === "overlap" ? check.is_valid : !check.is_valid) &&
                      check.total_cost * 100 <= maxCostPct &&
                      check.poly_cost * 100 >= minLegPct && check.poly_cost * 100 <= maxLegPct &&
                      check.kalshi_cost * 100 >= minLegPct && check.kalshi_cost * 100 <= maxLegPct
                    )
                    .map((check, i) => {
                      const isProfitable = check.is_arbitrage
                      const isCheapButInvalid = !check.is_valid && check.total_cost < 1.00
                      const rowClass = isProfitable ? "bg-green-50/50" : isCheapButInvalid ? "bg-amber-50/60" : ""
                      const overlapDisplay = check.overlap_size !== undefined
                        ? check.overlap_size >= 0
                          ? `$${check.overlap_size.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                          : `GAP $${Math.abs(check.overlap_size).toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                        : "—"
                      return (
                        <TableRow key={i} className={rowClass}>
                          <TableCell>
                            <Badge variant="outline" className={`whitespace-nowrap ${!check.is_valid ? "border-amber-400 text-amber-700 bg-amber-50" : ""}`}>
                              {check.type}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-xs">
                            <div className="flex flex-col">
                              <span>Buy Poly-{check.poly_leg}</span>
                              <span>Buy Kalshi-{check.kalshi_leg}</span>
                            </div>
                          </TableCell>
                          {activeTab === "1h" && (
                            <TableCell className="font-mono text-xs">
                              {check.kalshi_strike ? `$${check.kalshi_strike.toLocaleString()}` : "—"}
                            </TableCell>
                          )}
                          <TableCell className="w-[30%]">
                            <div className="space-y-1">
                              <div className="flex justify-between text-xs text-muted-foreground">
                                <span>${check.poly_cost.toFixed(3)} + ${check.kalshi_cost.toFixed(3)}</span>
                                <span>{Math.round(check.total_cost * 100)}%</span>
                              </div>
                              <Progress
                                value={Math.min(check.total_cost * 100, 100)}
                                className="h-2"
                                indicatorClassName={isProfitable ? "bg-green-500" : isCheapButInvalid ? "bg-amber-400" : "bg-slate-400"}
                              />
                            </div>
                          </TableCell>
                          <TableCell className="text-right font-mono font-bold">${check.total_cost.toFixed(3)}</TableCell>
                          <TableCell className="text-right">
                            <span className={`text-xs font-mono ${check.overlap_size !== undefined && check.overlap_size < 0 ? "text-red-600 font-semibold" : "text-slate-500"}`}>
                              {overlapDisplay}
                            </span>
                          </TableCell>
                          <TableCell className="text-right">
                            {isProfitable ? (
                              <div className="flex flex-col items-end">
                                <Badge className="bg-green-600 hover:bg-green-700 whitespace-nowrap">+${check.margin.toFixed(3)}</Badge>
                                {showCalculator && betAmount > 0 && (
                                  <span className="text-xs text-green-600 font-medium mt-1">${getRealizedProfit(check)?.toFixed(2)} profit</span>
                                )}
                              </div>
                            ) : isCheapButInvalid ? (
                              <Badge variant="outline" className="border-amber-400 text-amber-700 bg-amber-50 text-xs whitespace-nowrap">⚠ Gap Risk</Badge>
                            ) : (
                              <span className="text-muted-foreground text-xs">—</span>
                            )}
                          </TableCell>
                        </TableRow>
                      )
                    })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* ── History ── */}
          {historyForTab.length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Clock className="h-5 w-5" />
                      Arbitrage History — {MARKET_LABELS(selectedAsset, activeTab)}
                    </CardTitle>
                    <CardDescription>
                      {historyForTab.length} total across {groupedHistoryArray.length} markets
                    </CardDescription>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => {
                    setHistory(selectedAsset, activeTab, () => []);
                    localStorage.removeItem(HISTORY_KEY(selectedAsset, activeTab));
                  }} className="text-xs text-slate-500">
                    Clear History
                  </Button>
                </div>
                {/* All / Dry Run tabs */}
                <div className="flex border-b border-slate-200 mt-2">
                  <button
                    onClick={() => setHistoryView("all")}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${historyView === "all"
                      ? "border-blue-600 text-blue-700"
                      : "border-transparent text-slate-500 hover:text-slate-700"
                      }`}
                  >
                    All
                    <span className="ml-1.5 px-1.5 py-0.5 text-[10px] bg-slate-100 text-slate-600 rounded-full">
                      {historyForTab.length}
                    </span>
                  </button>
                  <button
                    onClick={() => setHistoryView("dryrun")}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${historyView === "dryrun"
                      ? "border-blue-600 text-blue-700"
                      : "border-transparent text-slate-500 hover:text-slate-700"
                      }`}
                  >
                    Dry Run
                    {(() => {
                      const validCount = historyForTab.filter(h => h.is_valid !== false && h.total_cost * 100 <= maxCostPct).length
                      return validCount > 0 ? (
                        <span className="ml-1.5 px-1.5 py-0.5 text-[10px] bg-green-100 text-green-700 rounded-full font-semibold">
                          {validCount}
                        </span>
                      ) : null
                    })()}
                  </button>
                </div>
              </CardHeader>
              {historyView === "all" ? (
                /* ── ALL view: grouped by market slug ── */
                <CardContent className="space-y-4">
                  {groupedHistoryArray.map(group => {
                    const groupExpanded = expandedHistory.has(group.slug)
                    return (
                      <div key={group.slug} className="border rounded-lg overflow-hidden bg-slate-50">
                        <div
                          className="flex items-center justify-between p-3 cursor-pointer hover:bg-slate-100 bg-slate-100"
                          onClick={() => toggleHistoryExpand(group.slug)}
                        >
                          <div className="flex items-center gap-3">
                            {groupExpanded ? <ChevronDown className="h-5 w-5 text-slate-600" /> : <ChevronRight className="h-5 w-5 text-slate-600" />}
                            <Badge variant="outline" className="bg-blue-50">Market</Badge>
                            <span className="font-medium text-sm">{group.slug}</span>
                          </div>
                          <div className="flex items-center gap-3">
                            <Badge className={group.activeCount > 0 ? "bg-green-600" : "bg-slate-400"}>
                              {group.activeCount} active
                            </Badge>
                            <span className="text-sm text-slate-500">{group.opportunities.length} opportunities</span>
                          </div>
                        </div>

                        {groupExpanded && (
                          <div className="space-y-2 p-3">
                            {group.opportunities.map(item => {
                              const isExpanded = expandedHistory.has(item.id)
                              const currentDuration = item.isActive
                                ? Math.floor((new Date().getTime() - item.firstSeen.getTime()) / 1000)
                                : item.duration
                              return (
                                <div key={item.id} className={`border rounded-lg overflow-hidden ${item.isActive ? "border-green-300 bg-green-50" : "border-slate-200 bg-white"}`}>
                                  <div className="flex items-center justify-between p-2 cursor-pointer hover:bg-slate-50" onClick={() => toggleHistoryExpand(item.id)}>
                                    <div className="flex items-center gap-2">
                                      {isExpanded ? <ChevronDown className="h-4 w-4 text-slate-500" /> : <ChevronRight className="h-4 w-4 text-slate-500" />}
                                      <span className="text-xs text-slate-400 font-mono">{item.firstSeen.toLocaleTimeString()}</span>
                                      <Badge variant="outline" className="whitespace-nowrap text-xs">{item.type}</Badge>
                                      <Badge
                                        variant="outline"
                                        className={`text-[10px] px-1.5 py-0 ${item.is_valid !== false
                                          ? "border-green-400 text-green-700 bg-green-50"
                                          : "border-amber-400 text-amber-700 bg-amber-50"
                                          }`}
                                      >
                                        {item.is_valid !== false ? "Overlap" : "Gap"}
                                      </Badge>
                                      {item.kalshi_strike && (
                                        <span className="font-mono text-xs text-slate-600">${item.kalshi_strike.toLocaleString()}</span>
                                      )}
                                      <span className="text-xs text-slate-500">Poly-{item.poly_leg} + Kalshi-{item.kalshi_leg}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                      <span className="text-xs text-slate-500">{formatDuration(currentDuration)}</span>
                                      <Badge className={`${item.isActive ? "bg-green-600" : "bg-slate-400"} text-xs`}>
                                        {item.isActive ? "Active" : "Ended"}
                                      </Badge>
                                      <span className="font-bold text-green-700 text-sm">+${item.margin.toFixed(3)}</span>
                                    </div>
                                  </div>

                                  {isExpanded && (
                                    <div className="px-3 pb-3 border-t border-slate-200 pt-3 space-y-3">

                                      {/* Timing & market */}
                                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                                        {([
                                          ["First Seen", item.firstSeen.toLocaleTimeString()],
                                          ["Last Updated", item.lastSeen.toLocaleTimeString()],
                                          ["Duration", formatDuration(currentDuration)],
                                          ["Market", (item.marketSlug || "").slice(0, 24) + ((item.marketSlug || "").length > 24 ? "…" : "")],
                                        ] as [string, string][]).map(([label, val]) => (
                                          <div key={label}>
                                            <div className="text-slate-400 uppercase tracking-wide text-[10px]">{label}</div>
                                            <div className="font-mono text-slate-700">{val}</div>
                                          </div>
                                        ))}
                                      </div>

                                      {/* Strategy, price-to-beat, overlap */}
                                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                                        <div className="bg-slate-50 p-2 rounded border">
                                          <div className="text-slate-400 uppercase tracking-wide text-[10px] mb-1">Strategy</div>
                                          <div className="font-medium">Poly <span className="font-mono">{item.poly_leg}</span> + Kalshi <span className="font-mono">{item.kalshi_leg}</span></div>
                                          {item.kalshi_strike && <div className="text-slate-500 mt-0.5">Kalshi @ <span className="font-mono">${item.kalshi_strike.toLocaleString()}</span></div>}
                                        </div>
                                        {item.poly_price_to_beat != null && (
                                          <div className="bg-slate-50 p-2 rounded border">
                                            <div className="text-slate-400 uppercase tracking-wide text-[10px] mb-1">Poly Price To Beat</div>
                                            <div className="font-mono font-medium">${item.poly_price_to_beat.toLocaleString(undefined, { maximumFractionDigits: 5 })}</div>
                                            <div className="text-slate-400 text-[10px] mt-0.5">Polymarket open</div>
                                          </div>
                                        )}
                                        {formatStrikeLabel(item) ? (
                                          <div className="bg-slate-50 p-2 rounded border">
                                            <div className="text-slate-400 uppercase tracking-wide text-[10px] mb-1">Kalshi Price Goal</div>
                                            <div className="font-mono font-medium">{formatStrikeLabel(item)}</div>
                                            <div className="text-slate-400 text-[10px] mt-0.5">Kalshi strike</div>
                                          </div>
                                        ) : item.kalshi_floor_strike != null && (
                                          <div className="bg-slate-50 p-2 rounded border">
                                            <div className="text-slate-400 uppercase tracking-wide text-[10px] mb-1">Kalshi Price To Beat</div>
                                            <div className="font-mono font-medium">${item.kalshi_floor_strike.toLocaleString(undefined, { maximumFractionDigits: 5 })}</div>
                                            <div className="text-slate-400 text-[10px] mt-0.5">Kalshi floor strike</div>
                                          </div>
                                        )}
                                        {item.overlap_size != null && (
                                          <div className={`p-2 rounded border ${item.overlap_size >= 0 ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"}`}>
                                            <div className="text-slate-400 uppercase tracking-wide text-[10px] mb-1">Overlap</div>
                                            <div className={`font-mono font-medium ${item.overlap_size >= 0 ? "text-green-700" : "text-red-600"}`}>
                                              {item.overlap_size >= 0
                                                ? `$${item.overlap_size.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                                                : `GAP $${Math.abs(item.overlap_size).toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
                                            </div>
                                            <div className="text-slate-400 text-[10px] mt-0.5">safety zone</div>
                                          </div>
                                        )}
                                      </div>

                                      {/* Resolution & Realized Returns */}
                                      {(item.poly_outcome || item.kalshi_outcome || (item.kalshi_market_ticker && !item.isActive)) && (
                                        <div className="bg-blue-50 border border-blue-200 p-3 rounded-lg flex flex-col md:flex-row justify-between items-center gap-4">
                                          <div className="flex gap-4">
                                            <div className="text-center">
                                              <div className="text-[10px] text-blue-600 uppercase font-bold mb-1">Polymarket Result</div>
                                              <Badge variant="outline" className={item.poly_outcome ? (item.poly_outcome.toLowerCase() === item.poly_leg.toLowerCase() ? "bg-green-100 text-green-800 border-green-200" : "bg-red-100 text-red-800 border-red-200") : ""}>
                                                {item.poly_outcome ? item.poly_outcome.toUpperCase() : "SYNCING..."}
                                              </Badge>
                                            </div>
                                            <div className="text-center border-l border-blue-200 pl-4">
                                              <div className="text-[10px] text-blue-600 uppercase font-bold mb-1">Kalshi Result</div>
                                              <Badge variant="outline" className={item.kalshi_outcome ? (item.kalshi_outcome.toLowerCase() === item.kalshi_leg.toLowerCase() ? "bg-green-100 text-green-800 border-green-200" : "bg-red-100 text-red-800 border-red-200") : ""}>
                                                {item.kalshi_outcome ? item.kalshi_outcome.toUpperCase() : "SYNCING..."}
                                              </Badge>
                                            </div>
                                          </div>

                                          {item.realized_return !== undefined && (
                                            <div className="text-right">
                                              <div className="text-[10px] text-blue-600 uppercase font-bold mb-0.5">Realized Return</div>
                                              <div className={`text-lg font-bold ${item.realized_return > betAmount ? "text-green-600" : item.realized_return > 0 ? "text-amber-600" : "text-red-600"}`}>
                                                ${item.realized_return.toFixed(2)}
                                                <span className="text-xs ml-1 opacity-70">
                                                  ({item.realized_return >= betAmount ? "+" : ""}{(item.realized_return - betAmount).toFixed(2)} profit)
                                                </span>
                                              </div>
                                            </div>
                                          )}
                                        </div>
                                      )}

                                      {/* Cost breakdown */}
                                      <div className="grid grid-cols-3 gap-2 text-xs">
                                        <div className="bg-white p-2 rounded border">
                                          <div className="text-slate-400 uppercase tracking-wide text-[10px] mb-1">Poly {item.poly_leg}</div>
                                          <div className="font-mono text-slate-700">${item.poly_cost.toFixed(4)}</div>
                                          <div className="text-slate-400 text-[10px]">{(item.poly_cost * 100).toFixed(1)}¢</div>
                                        </div>
                                        <div className="bg-white p-2 rounded border">
                                          <div className="text-slate-400 uppercase tracking-wide text-[10px] mb-1">Kalshi {item.kalshi_leg}</div>
                                          <div className="font-mono text-slate-700">${item.kalshi_cost.toFixed(4)}</div>
                                          <div className="text-slate-400 text-[10px]">{(item.kalshi_cost * 100).toFixed(1)}¢</div>
                                        </div>
                                        <div className="bg-green-50 p-2 rounded border border-green-200">
                                          <div className="text-green-600 uppercase tracking-wide text-[10px] mb-1">Margin</div>
                                          <div className="font-mono font-bold text-green-700">+${item.margin.toFixed(4)}</div>
                                          <div className="text-green-600 text-[10px]">{(item.margin * 100).toFixed(2)}% on ${item.total_cost.toFixed(3)}</div>
                                        </div>
                                      </div>

                                      {/* Profit calculator */}
                                      {showCalculator && betAmount > 0 && getContractDetails(item) && (
                                        <div className="bg-blue-50 p-2 rounded border border-blue-200 text-xs space-y-1">
                                          <div className="font-medium text-blue-700 mb-1">Profit on ${betAmount.toLocaleString()} investment</div>
                                          <div className="flex justify-between">
                                            <span className="text-slate-600">Polymarket {item.poly_leg}:</span>
                                            <span className="font-mono">${getContractDetails(item)!.polyAllocation.toFixed(2)} → {getContractDetails(item)!.polyContracts.toFixed(3)} contracts</span>
                                          </div>
                                          <div className="flex justify-between">
                                            <span className="text-slate-600">Kalshi {item.kalshi_leg}:</span>
                                            <span className="font-mono">${getContractDetails(item)!.kalshiAllocation.toFixed(2)} → {getContractDetails(item)!.kalshiContracts.toFixed(3)} contracts</span>
                                          </div>
                                          <div className="flex justify-between font-semibold pt-1 border-t border-blue-200">
                                            <span>Net profit:</span>
                                            <span className="font-mono text-green-700">+${getRealizedProfit(item)?.toFixed(2)}</span>
                                          </div>
                                        </div>
                                      )}
                                    </div>
                                  )}
                                </div>
                              )
                            })}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </CardContent>
              ) : (() => {
                /* ── DRY RUN view: flat profit-focused table with grand total ── */
                const dryItems = historyForTab
                  .filter(h => h.is_valid !== false && h.total_cost * 100 <= maxCostPct)
                  .sort((a, b) => b.firstSeen.getTime() - a.firstSeen.getTime())
                const totalProfit = betAmount > 0
                  ? dryItems.reduce((sum, h) => sum + (getRealizedProfit(h) ?? 0), 0)
                  : null
                const avgMarginPct = dryItems.length > 0
                  ? dryItems.reduce((sum, h) => sum + h.margin, 0) / dryItems.length * 100
                  : 0
                return dryItems.length === 0 ? (
                  <div className="text-center py-10 text-slate-500 text-sm px-6">
                    <div className="text-2xl mb-2">📋</div>
                    <div className="font-medium">No valid arbitrage history yet</div>
                    <div className="text-xs mt-1 text-slate-400">Valid opportunities will appear here as they are detected</div>
                  </div>
                ) : (
                  <CardContent className="space-y-4 p-4">
                    {/* Summary banner */}
                    <div className="grid grid-cols-3 gap-3">
                      <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center">
                        <div className="text-green-600 text-[10px] uppercase tracking-wide font-medium mb-1">Opportunities</div>
                        <div className="text-2xl font-bold text-green-700">{dryItems.length}</div>
                      </div>
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-center">
                        <div className="text-blue-600 text-[10px] uppercase tracking-wide font-medium mb-1">Avg Margin</div>
                        <div className="text-2xl font-bold text-blue-700">{avgMarginPct.toFixed(2)}%</div>
                      </div>
                      {betAmount > 0 && totalProfit !== null ? (
                        <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-center">
                          <div className="text-emerald-600 text-[10px] uppercase tracking-wide font-medium mb-1">Total Profit</div>
                          <div className="text-2xl font-bold text-emerald-700">+${totalProfit.toFixed(2)}</div>
                          <div className="text-[10px] text-emerald-600">${betAmount} per trade</div>
                        </div>
                      ) : (
                        <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-center">
                          <div className="text-slate-500 text-[10px] uppercase tracking-wide font-medium mb-1">Total Profit</div>
                          <div className="text-sm text-slate-400 mt-2">Set investment ↑</div>
                        </div>
                      )}
                    </div>

                    {/* Per-item table */}
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Time</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead>Strategy</TableHead>
                          <TableHead className="text-right">Margin</TableHead>
                          {betAmount > 0 && <TableHead className="text-right">Profit (${betAmount})</TableHead>}
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {dryItems.map((item) => {
                          const profit = betAmount > 0 ? getRealizedProfit(item) : null
                          const isExpanded = expandedHistory.has(item.id)
                          const details = betAmount > 0 ? getContractDetails(item) : null
                          const now = new Date()
                          const currentDuration = item.isActive
                            ? Math.floor((now.getTime() - item.firstSeen.getTime()) / 1000)
                            : item.duration
                          return (
                            <React.Fragment key={item.id}>
                              <TableRow
                                key={item.id}
                                className={`cursor-pointer hover:bg-slate-50 ${item.isActive ? "bg-green-50/40" : ""}`}
                                onClick={() => toggleHistoryExpand(item.id)}
                              >
                                <TableCell className="font-mono text-xs text-slate-500">
                                  {item.firstSeen.toLocaleTimeString()}
                                  {item.isActive && <Badge className="ml-1.5 bg-green-600 text-[9px] px-1 py-0">Live</Badge>}
                                </TableCell>
                                <TableCell>
                                  <Badge variant="outline" className="whitespace-nowrap text-xs">{item.type}</Badge>
                                </TableCell>
                                <TableCell className="text-xs">
                                  <div className="flex flex-col">
                                    <span>Poly {item.poly_leg} @ ${item.poly_cost.toFixed(3)}</span>
                                    <span>Kalshi {item.kalshi_leg} {formatStrikeLabel(item) ? `@ ${formatStrikeLabel(item)}` : `@ $${item.kalshi_cost.toFixed(3)}`}</span>
                                  </div>
                                </TableCell>
                                <TableCell className="text-right">
                                  <div className="flex flex-col items-end">
                                    <span className="font-bold text-green-700">+${item.margin.toFixed(4)}</span>
                                    <span className="text-[10px] text-green-600">{(item.margin * 100).toFixed(2)}%</span>
                                  </div>
                                </TableCell>
                                {betAmount > 0 && (
                                  <TableCell className="text-right font-bold text-blue-700">
                                    {profit != null ? `+$${profit.toFixed(2)}` : "—"}
                                  </TableCell>
                                )}
                              </TableRow>
                              {isExpanded && (
                                <TableRow key={`${item.id}-detail`}>
                                  <TableCell colSpan={betAmount > 0 ? 5 : 4} className="p-0">
                                    <div className="px-3 pb-3 border-t border-slate-200 pt-3 space-y-3 bg-white">
                                      {/* Timing & market */}
                                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                                        {([
                                          ["First Seen", item.firstSeen.toLocaleTimeString()],
                                          ["Last Updated", item.lastSeen.toLocaleTimeString()],
                                          ["Duration", formatDuration(currentDuration)],
                                          ["Market", (item.marketSlug || "").slice(0, 24) + ((item.marketSlug || "").length > 24 ? "…" : "")],
                                        ] as [string, string][]).map(([label, val]) => (
                                          <div key={label}>
                                            <div className="text-slate-400 uppercase tracking-wide text-[10px]">{label}</div>
                                            <div className="font-mono text-slate-700">{val}</div>
                                          </div>
                                        ))}
                                      </div>
                                      {/* Strategy, price-to-beat, overlap */}
                                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                                        <div className="bg-slate-50 p-2 rounded border">
                                          <div className="text-slate-400 uppercase tracking-wide text-[10px] mb-1">Strategy</div>
                                          <div className="font-medium">Poly <span className="font-mono">{item.poly_leg}</span> + Kalshi <span className="font-mono">{item.kalshi_leg}</span></div>
                                          {item.kalshi_strike && <div className="text-slate-500 mt-0.5">Kalshi @ <span className="font-mono">${item.kalshi_strike.toLocaleString()}</span></div>}
                                        </div>
                                        {item.poly_price_to_beat != null && (
                                          <div className="bg-slate-50 p-2 rounded border">
                                            <div className="text-slate-400 uppercase tracking-wide text-[10px] mb-1">Poly Price To Beat</div>
                                            <div className="font-mono font-medium">${item.poly_price_to_beat.toLocaleString(undefined, { maximumFractionDigits: 5 })}</div>
                                          </div>
                                        )}
                                        {formatStrikeLabel(item) ? (
                                          <div className="bg-slate-50 p-2 rounded border">
                                            <div className="text-slate-400 uppercase tracking-wide text-[10px] mb-1">Kalshi Price Goal</div>
                                            <div className="font-mono font-medium">{formatStrikeLabel(item)}</div>
                                          </div>
                                        ) : item.kalshi_floor_strike != null && (
                                          <div className="bg-slate-50 p-2 rounded border">
                                            <div className="text-slate-400 uppercase tracking-wide text-[10px] mb-1">Kalshi Floor Strike</div>
                                            <div className="font-mono font-medium">${item.kalshi_floor_strike.toLocaleString(undefined, { maximumFractionDigits: 5 })}</div>
                                          </div>
                                        )}
                                        {item.overlap_size != null && (
                                          <div className={`p-2 rounded border ${item.overlap_size >= 0 ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"}`}>
                                            <div className="text-slate-400 uppercase tracking-wide text-[10px] mb-1">Overlap</div>
                                            <div className={`font-mono font-medium ${item.overlap_size >= 0 ? "text-green-700" : "text-red-600"}`}>
                                              {item.overlap_size >= 0
                                                ? `$${item.overlap_size.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                                                : `GAP $${Math.abs(item.overlap_size).toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
                                            </div>
                                          </div>
                                        )}
                                      </div>

                                      {/* Resolution & Realized Returns */}
                                      {(item.poly_outcome || item.kalshi_outcome || (item.kalshi_market_ticker && !item.isActive)) && (
                                        <div className="bg-blue-50 border border-blue-200 p-3 rounded-lg flex flex-col md:flex-row justify-between items-center gap-4">
                                          <div className="flex gap-4">
                                            <div className="text-center">
                                              <div className="text-[10px] text-blue-600 uppercase font-bold mb-1">Polymarket Result</div>
                                              <Badge variant="outline" className={item.poly_outcome ? (item.poly_outcome.toLowerCase() === item.poly_leg.toLowerCase() ? "bg-green-100 text-green-800 border-green-200" : "bg-red-100 text-red-800 border-red-200") : ""}>
                                                {item.poly_outcome ? item.poly_outcome.toUpperCase() : "SYNCING..."}
                                              </Badge>
                                            </div>
                                            <div className="text-center border-l border-blue-200 pl-4">
                                              <div className="text-[10px] text-blue-600 uppercase font-bold mb-1">Kalshi Result</div>
                                              <Badge variant="outline" className={item.kalshi_outcome ? (item.kalshi_outcome.toLowerCase() === item.kalshi_leg.toLowerCase() ? "bg-green-100 text-green-800 border-green-200" : "bg-red-100 text-red-800 border-red-200") : ""}>
                                                {item.kalshi_outcome ? item.kalshi_outcome.toUpperCase() : "SYNCING..."}
                                              </Badge>
                                            </div>
                                          </div>

                                          {item.realized_return !== undefined && (
                                            <div className="text-right">
                                              <div className="text-[10px] text-blue-600 uppercase font-bold mb-0.5">Realized Return</div>
                                              <div className={`text-lg font-bold ${item.realized_return > betAmount ? "text-green-600" : item.realized_return > 0 ? "text-amber-600" : "text-red-600"}`}>
                                                ${item.realized_return.toFixed(2)}
                                                <span className="text-xs ml-1 opacity-70">
                                                  ({item.realized_return >= betAmount ? "+" : ""}{(item.realized_return - betAmount).toFixed(2)} profit)
                                                </span>
                                              </div>
                                            </div>
                                          )}
                                        </div>
                                      )}

                                      {/* Cost breakdown */}
                                      <div className="grid grid-cols-3 gap-2 text-xs">
                                        <div className="bg-white p-2 rounded border">
                                          <div className="text-slate-400 uppercase tracking-wide text-[10px] mb-1">Poly {item.poly_leg}</div>
                                          <div className="font-mono text-slate-700">${item.poly_cost.toFixed(4)}</div>
                                          <div className="text-slate-400 text-[10px]">{(item.poly_cost * 100).toFixed(1)}¢</div>
                                        </div>
                                        <div className="bg-white p-2 rounded border">
                                          <div className="text-slate-400 uppercase tracking-wide text-[10px] mb-1">Kalshi {item.kalshi_leg}</div>
                                          <div className="font-mono text-slate-700">${item.kalshi_cost.toFixed(4)}</div>
                                          <div className="text-slate-400 text-[10px]">{(item.kalshi_cost * 100).toFixed(1)}¢</div>
                                        </div>
                                        <div className="bg-green-50 p-2 rounded border border-green-200">
                                          <div className="text-green-600 uppercase tracking-wide text-[10px] mb-1">Margin</div>
                                          <div className="font-mono font-bold text-green-700">+${item.margin.toFixed(4)}</div>
                                          <div className="text-green-500 text-[10px]">{(item.margin / item.total_cost * 100).toFixed(2)}% on total</div>
                                        </div>
                                      </div>
                                      {/* Profit calculator */}
                                      {showCalculator && betAmount > 0 && details && (
                                        <div className="bg-blue-50 p-2 rounded border border-blue-200 text-xs space-y-1">
                                          <div className="flex justify-between">
                                            <span className="text-blue-600">Poly contracts:</span>
                                            <span className="font-mono">{details.polyContracts.toFixed(2)} × ${item.poly_cost.toFixed(3)} = ${(details.polyContracts * item.poly_cost).toFixed(2)}</span>
                                          </div>
                                          <div className="flex justify-between">
                                            <span className="text-blue-600">Kalshi contracts:</span>
                                            <span className="font-mono">{details.kalshiContracts.toFixed(2)} × ${item.kalshi_cost.toFixed(3)} = ${(details.kalshiContracts * item.kalshi_cost).toFixed(2)}</span>
                                          </div>
                                          <div className="flex justify-between font-semibold pt-1 border-t border-blue-200">
                                            <span>Net profit:</span>
                                            <span className="font-mono text-green-700">+${getRealizedProfit(item)?.toFixed(2)}</span>
                                          </div>
                                        </div>
                                      )}
                                    </div>
                                  </TableCell>
                                </TableRow>
                              )}
                            </React.Fragment>
                          )
                        })}
                        {/* Grand total row */}
                        {betAmount > 0 && totalProfit !== null && (
                          <TableRow className="border-t-2 border-slate-300 bg-slate-50 font-semibold">
                            <TableCell colSpan={4} className="text-right text-sm">
                              Total from {dryItems.length} trades at ${betAmount} each:
                            </TableCell>
                            <TableCell className="text-right font-bold text-emerald-700 text-base">
                              +${totalProfit.toFixed(2)}
                            </TableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </CardContent>
                )
              })()}
            </Card>
          )}

        </>
      )}
    </div>
  )
}
