"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { AlertCircle, TrendingUp } from "lucide-react"

interface OutcomePrices {
  bid: number
  ask: number
}

interface KalshiOutcomePrices {
  yes_ask: number
  no_ask: number
  yes_bid: number
  no_bid: number
}

interface ArbitrageCheck {
  outcome: string
  direction: string
  poly_cost: number
  kalshi_cost: number
  total_cost: number
  is_arbitrage: boolean
  margin: number
}

interface MatchData {
  home_team: string
  away_team: string
  league: string
  league_name: string
  poly_slug: string
  kalshi_ticker: string
  polymarket_outcomes: Record<string, OutcomePrices>
  kalshi_outcomes: Record<string, KalshiOutcomePrices>
  checks: ArbitrageCheck[]
  opportunities: ArbitrageCheck[]
}

interface ApiResponse {
  timestamp: string
  total_matches: number
  total_poly_events: number
  total_kalshi_events: number
  matches: MatchData[]
  opportunities: ArbitrageCheck[]
  errors: string[]
  leagues: Record<string, string>
}

export default function Dashboard() {
  const [data, setData] = useState<ApiResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())
  const [selectedLeague, setSelectedLeague] = useState<string>("all")

  const fetchData = async () => {
    try {
      const params = selectedLeague !== "all" ? `?league=${selectedLeague}` : ""
      const res = await fetch(`http://localhost:8000/arbitrage${params}`)
      const json = await res.json()
      setData(json)
      setLastUpdated(new Date())
      setLoading(false)
    } catch (err) {
      console.error("Failed to fetch data", err)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [selectedLeague])

  if (loading) return <div className="flex items-center justify-center h-screen">Loading...</div>

  if (!data) return <div className="p-8">No data available</div>

  const bestOpp = data.opportunities.length > 0 ? data.opportunities[0] : null

  return (
    <div className="p-8 space-y-8 bg-slate-50 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold tracking-tight">Soccer Arbitrage Scanner</h1>
          <Badge variant="outline" className="animate-pulse bg-green-100 text-green-800 border-green-200">
            <span className="w-2 h-2 rounded-full bg-green-500 mr-2"></span>
            Live
          </Badge>
        </div>
        <div className="flex items-center gap-4">
          <select
            value={selectedLeague}
            onChange={(e) => setSelectedLeague(e.target.value)}
            className="border rounded-md px-3 py-1.5 text-sm bg-white"
          >
            <option value="all">All Leagues</option>
            {data.leagues && Object.entries(data.leagues).map(([key, name]) => (
              <option key={key} value={key}>{name}</option>
            ))}
          </select>
          <div className="text-sm text-muted-foreground">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* Errors */}
      {data.errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md flex items-start gap-2">
          <AlertCircle className="h-5 w-5 mt-0.5 shrink-0" />
          <div>
            <strong className="font-bold block mb-1">Errors Detected:</strong>
            <ul className="list-disc ml-5 text-sm">
              {data.errors.map((err, i) => (
                <li key={i}>{err}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-xs text-muted-foreground uppercase font-bold">Matched Pairs</div>
            <div className="text-3xl font-bold">{data.total_matches}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-xs text-muted-foreground uppercase font-bold">Polymarket Events</div>
            <div className="text-3xl font-bold">{data.total_poly_events}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-xs text-muted-foreground uppercase font-bold">Kalshi Events</div>
            <div className="text-3xl font-bold">{data.total_kalshi_events}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-xs text-muted-foreground uppercase font-bold">Opportunities</div>
            <div className="text-3xl font-bold text-green-600">{data.opportunities.length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Best Opportunity */}
      {bestOpp && (
        <Card className="bg-gradient-to-r from-green-50 to-emerald-50 border-green-200 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2 text-green-700">
              <TrendingUp className="h-5 w-5" />
              <CardTitle>Best Opportunity Found</CardTitle>
            </div>
            <CardDescription>Highest margin arbitrage across all matches</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
              <div className="text-center md:text-left">
                <div className="text-sm text-muted-foreground">Profit Margin</div>
                <div className="text-4xl font-bold text-green-700">${bestOpp.margin.toFixed(3)}</div>
                <div className="text-xs text-green-600 font-medium">per contract</div>
              </div>
              <div className="flex-1 bg-white p-4 rounded-lg border border-green-100 w-full">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-semibold text-slate-700">{bestOpp.outcome}</span>
                  <Badge className="bg-green-600">{bestOpp.direction}</Badge>
                </div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Poly Leg</span>
                  <span className="font-mono">${bestOpp.poly_cost.toFixed(3)}</span>
                </div>
                <div className="flex justify-between text-sm mb-3">
                  <span>Kalshi Leg</span>
                  <span className="font-mono">${bestOpp.kalshi_cost.toFixed(3)}</span>
                </div>
                <div className="pt-2 border-t border-dashed border-slate-200 flex justify-between font-bold">
                  <span>Total Cost</span>
                  <span>${bestOpp.total_cost.toFixed(3)}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Match Cards */}
      {data.matches.map((match, matchIdx) => (
        <Card key={matchIdx} className={match.opportunities.length > 0 ? "border-green-200" : ""}>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle className="text-lg">
                  {match.home_team} vs {match.away_team}
                </CardTitle>
                <CardDescription>
                  <Badge variant="outline" className="mr-2">{match.league_name}</Badge>
                  {match.opportunities.length > 0 && (
                    <Badge className="bg-green-600">{match.opportunities.length} opportunities</Badge>
                  )}
                </CardDescription>
              </div>
              <div className="text-xs text-muted-foreground text-right">
                <div>Poly: {match.poly_slug}</div>
                <div>Kalshi: {match.kalshi_ticker}</div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {/* Side-by-side prices */}
            <div className="grid grid-cols-2 gap-6 mb-6">
              <div>
                <h4 className="font-semibold text-sm mb-3 text-slate-600">Polymarket</h4>
                <div className="space-y-2">
                  {Object.entries(match.polymarket_outcomes).map(([name, prices]) => (
                    <div key={name} className="flex justify-between items-center text-sm">
                      <span>{name}</span>
                      <div className="font-mono">
                        <span className="text-muted-foreground mr-2">bid {prices.bid.toFixed(3)}</span>
                        <span className="font-medium">ask {prices.ask.toFixed(3)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <h4 className="font-semibold text-sm mb-3 text-slate-600">Kalshi</h4>
                <div className="space-y-2">
                  {Object.entries(match.kalshi_outcomes).map(([name, prices]) => (
                    <div key={name} className="flex justify-between items-center text-sm">
                      <span className="truncate mr-2">{name}</span>
                      <div className="font-mono">
                        <span className="text-green-600 mr-2">Y {prices.yes_ask.toFixed(3)}</span>
                        <span className="text-red-600">N {prices.no_ask.toFixed(3)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Arbitrage checks for this match */}
            {match.checks.length > 0 && (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Outcome</TableHead>
                    <TableHead>Direction</TableHead>
                    <TableHead>Poly Cost</TableHead>
                    <TableHead>Kalshi Cost</TableHead>
                    <TableHead>Total</TableHead>
                    <TableHead className="text-right">Result</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {match.checks.map((check, i) => {
                    const isProfitable = check.total_cost < 1.00
                    const percentCost = Math.min(check.total_cost * 100, 100)

                    return (
                      <TableRow key={i} className={isProfitable ? "bg-green-50/50" : ""}>
                        <TableCell className="font-medium">{check.outcome}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="text-xs whitespace-nowrap">
                            {check.direction}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono text-sm">${check.poly_cost.toFixed(3)}</TableCell>
                        <TableCell className="font-mono text-sm">${check.kalshi_cost.toFixed(3)}</TableCell>
                        <TableCell>
                          <div className="space-y-1 min-w-[120px]">
                            <div className="flex justify-between text-xs">
                              <span className="font-mono font-bold">${check.total_cost.toFixed(3)}</span>
                              <span>{Math.round(percentCost)}%</span>
                            </div>
                            <Progress
                              value={percentCost}
                              className="h-2"
                              indicatorClassName={isProfitable ? "bg-green-500" : "bg-slate-400"}
                            />
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          {isProfitable ? (
                            <Badge className="bg-green-600 hover:bg-green-700">
                              +${check.margin.toFixed(3)}
                            </Badge>
                          ) : (
                            <span className="text-muted-foreground text-xs">-</span>
                          )}
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      ))}

      {/* No matches state */}
      {data.matches.length === 0 && (
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground">
            <p className="text-lg">No matched markets found</p>
            <p className="text-sm mt-1">Waiting for matching soccer events across both platforms...</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
