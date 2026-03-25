"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { AlertCircle, TrendingUp } from "lucide-react"

interface MarketData {
  timestamp: string
  polymarket: {
    price_to_beat: number
    current_price: number
    prices: {
      Up: number
      Down: number
    }
    slug: string
  }
  kalshi: {
    event_ticker: string
    current_price: number
    markets: Array<{
      strike: number
      yes_ask: number
      no_ask: number
      subtitle: string
    }>
  }
  checks: Array<{
    kalshi_strike: number
    type: string
    poly_leg: string
    kalshi_leg: string
    poly_cost: number
    kalshi_cost: number
    total_cost: number
    is_arbitrage: boolean
    margin: number
  }>
  opportunities: Array<{
    kalshi_strike: number
    type: string
    poly_leg: string
    kalshi_leg: string
    poly_cost: number
    kalshi_cost: number
    total_cost: number
    is_arbitrage: boolean
    margin: number
  }>
  errors: string[]
}

export default function Dashboard() {
  const [data, setData] = useState<MarketData | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())

  const fetchData = async () => {
    try {
      const res = await fetch("http://localhost:8000/arbitrage")
      const json = await res.json()
      setData(json)
      setLastUpdated(new Date())
      setLoading(false)
    } catch (err) {
      console.error("Failed to fetch data", err)
      // On failure, we should probably set loading to false to show the dashboard
      // with whatever data we currently have, or an empty state
      setLoading(false)
    }
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    // Initial fetch
    fetchData()

    // Setup polling
    const interval = setInterval(() => {
      fetchData()
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  if (loading) return <div className="flex items-center justify-center h-screen">Loading...</div>

  if (!data) return <div className="p-8">No data available</div>

  const bestOpp = data.opportunities.length > 0
    ? data.opportunities.reduce((prev, current) => (prev.margin > current.margin) ? prev : current)
    : null

  return (
    <div className="p-8 space-y-8 bg-slate-50 min-h-screen">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold tracking-tight">Arbitrage Bot Dashboard</h1>
          <Badge variant="outline" className="animate-pulse bg-green-100 text-green-800 border-green-200">
            <span className="w-2 h-2 rounded-full bg-green-500 mr-2"></span>
            Live
          </Badge>
        </div>
        <div className="text-sm text-muted-foreground">
          Last updated: {lastUpdated.toLocaleTimeString()}
        </div>
      </div>

      {data.errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md flex items-start gap-2">
          <AlertCircle className="h-5 w-5 mt-0.5" />
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

      {/* Best Opportunity Hero Card */}
      {bestOpp && (
        <Card className="bg-gradient-to-r from-green-50 to-emerald-50 border-green-200 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2 text-green-700">
              <TrendingUp className="h-5 w-5" />
              <CardTitle>Best Opportunity Found</CardTitle>
            </div>
            <CardDescription>Risk-free arbitrage detected with highest margin</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
              <div className="text-center md:text-left">
                <div className="text-sm text-muted-foreground">Profit Margin</div>
                <div className="text-4xl font-bold text-green-700">${bestOpp.margin.toFixed(3)}</div>
                <div className="text-xs text-green-600 font-medium">per unit</div>
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
                  <span>Kalshi {bestOpp.kalshi_leg} (${bestOpp.kalshi_strike.toLocaleString()})</span>
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

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Polymarket Card */}
        <Card>
          <CardHeader>
            <CardTitle>Polymarket</CardTitle>
            <CardDescription>Target: {data.polymarket?.slug || "Unavailable"}</CardDescription>
          </CardHeader>
          <CardContent>
            {data.polymarket ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-100 p-3 rounded-md">
                    <div className="text-xs text-muted-foreground uppercase font-bold">Price to Beat</div>
                    <div className="text-xl font-mono font-semibold">${data.polymarket.price_to_beat?.toLocaleString() || "N/A"}</div>
                  </div>
                  <div className="bg-slate-100 p-3 rounded-md">
                    <div className="text-xs text-muted-foreground uppercase font-bold">Current Price</div>
                    <div className="text-xl font-mono font-semibold">${data.polymarket.current_price?.toLocaleString() || "N/A"}</div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between items-center text-sm">
                    <span>UP Contract</span>
                    <span className="font-mono font-medium">${data.polymarket.prices?.Up?.toFixed(3) || "0.000"}</span>
                  </div>
                  <Progress value={(data.polymarket.prices?.Up || 0) * 100} className="h-2 bg-slate-100" indicatorClassName="bg-green-500" />

                  <div className="flex justify-between items-center text-sm mt-2">
                    <span>DOWN Contract</span>
                    <span className="font-mono font-medium">${data.polymarket.prices?.Down?.toFixed(3) || "0.000"}</span>
                  </div>
                  <Progress value={(data.polymarket.prices?.Down || 0) * 100} className="h-2 bg-slate-100" indicatorClassName="bg-red-500" />
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center p-8 text-muted-foreground bg-slate-50 rounded-md border border-dashed">
                Polymarket data is currently unavailable
              </div>
            )}
          </CardContent>
        </Card>

        {/* Kalshi Card */}
        <Card>
          <CardHeader>
            <CardTitle>Kalshi</CardTitle>
            <CardDescription>Ticker: {data.kalshi?.event_ticker || "Unavailable"}</CardDescription>
          </CardHeader>
          <CardContent>
            {data.kalshi ? (
              <div className="space-y-4">
                <div className="bg-slate-100 p-3 rounded-md mb-4">
                  <div className="text-xs text-muted-foreground uppercase font-bold">Current Price</div>
                  <div className="text-xl font-mono font-semibold">${data.kalshi.current_price?.toLocaleString() || "N/A"}</div>
                </div>

                <div className="space-y-3 max-h-[200px] overflow-y-auto pr-2">
                  {data.kalshi.markets
                    ?.filter(m => !data.polymarket || Math.abs(m.strike - (data.polymarket.price_to_beat || 0)) < 2500)
                    .map((m, i) => (
                      <div key={i} className="text-sm border-b pb-2 last:border-0">
                        <div className="flex justify-between font-medium mb-1">
                          <span>{m.subtitle}</span>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                          <div className="flex justify-between text-xs text-muted-foreground">
                            <span>Yes: {m.yes_ask}¢</span>
                            <span>No: {m.no_ask}¢</span>
                          </div>
                          <div className="flex h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                            <div className="bg-green-500 h-full" style={{ width: `${m.yes_ask}%` }}></div>
                            <div className="bg-red-500 h-full" style={{ width: `${m.no_ask}%` }}></div>
                          </div>
                        </div>
                      </div>
                    ))}
                  {(!data.kalshi.markets || data.kalshi.markets.length === 0) && (
                    <div className="text-center text-sm text-muted-foreground p-2">No markets available</div>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center p-8 text-muted-foreground bg-slate-50 rounded-md border border-dashed">
                Kalshi data is currently unavailable
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Arbitrage Checks Table */}
      <Card>
        <CardHeader>
          <CardTitle>Arbitrage Analysis</CardTitle>
          <CardDescription>Real-time comparison of all potential strategies</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[100px]">Type</TableHead>
                <TableHead>Kalshi Strike</TableHead>
                <TableHead>Strategy</TableHead>
                <TableHead>Cost Analysis</TableHead>
                <TableHead className="text-right">Total Cost</TableHead>
                <TableHead className="text-right">Result</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.checks.map((check, i) => {
                const isProfitable = check.total_cost < 1.00
                const percentCost = Math.min(check.total_cost * 100, 100)

                return (
                  <TableRow key={i} className={isProfitable ? "bg-green-50/50" : ""}>
                    <TableCell>
                      <Badge variant="outline" className="whitespace-nowrap">
                        {check.type.replace("Poly", "P").replace("Kalshi", "K")}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      ${check.kalshi_strike.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-xs">
                      <div className="flex flex-col">
                        <span>Buy P-{check.poly_leg}</span>
                        <span>Buy K-{check.kalshi_leg}</span>
                      </div>
                    </TableCell>
                    <TableCell className="w-[30%]">
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>${check.poly_cost.toFixed(3)} + ${check.kalshi_cost.toFixed(3)}</span>
                          <span>{Math.round(check.total_cost * 100)}%</span>
                        </div>
                        <Progress
                          value={percentCost}
                          className="h-2"
                          indicatorClassName={isProfitable ? "bg-green-500" : "bg-slate-400"}
                        />
                      </div>
                    </TableCell>
                    <TableCell className="text-right font-mono font-bold">
                      ${check.total_cost.toFixed(3)}
                    </TableCell>
                    <TableCell className="text-right">
                      {isProfitable ? (
                        <Badge className="bg-green-600 hover:bg-green-700 whitespace-nowrap">
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
        </CardContent>
      </Card>
    </div>
  )
}
