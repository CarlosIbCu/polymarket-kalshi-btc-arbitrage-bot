# Soccer Arbitrage Bot - Implementation Plan

## Overview
Convert the BTC hourly price arbitrage bot into a soccer match 3-way moneyline (Home/Draw/Away) arbitrage scanner across Polymarket and Kalshi. Support all major leagues globally.

## Arbitrage Logic (Soccer 3-Way Moneyline)

A soccer match has 3 outcomes: **Home Win**, **Draw**, **Away Win**.

On **Polymarket**, each match is an event with markets for each outcome, priced via the CLOB order book.

On **Kalshi**, each outcome is a separate binary YES/NO market (e.g., "Will Liverpool beat Arsenal?" YES/NO).

**Arbitrage exists when:** you can buy one outcome on Polymarket and buy the opposite (NO) on Kalshi for the same outcome, totaling < $1.00. For example:
- Polymarket "Home Win" ask = $0.45
- Kalshi "Home Win" NO ask = $0.50
- Total = $0.95 → $0.05 profit guaranteed

We check all 3 outcomes in both directions (buy on Poly + sell on Kalshi, and vice versa) = 6 checks per match.

---

## Leagues to Support

### Europe
- EPL (English Premier League)
- La Liga
- Bundesliga
- Serie A
- Ligue 1
- Champions League (UCL)
- Europa League (UEL)
- Eredivisie
- Primeira Liga (Portugal)
- EFL Championship

### Americas
- MLS (Major League Soccer)

### International
- World Cup (when active)

### Central/South America
- Copa Libertadores
- Copa Sudamericana
- Liga MX (Mexico)
- Brasileirao (Brazil)
- Primera Division (Argentina)

---

## Backend Changes

### Step 1: New file `backend/leagues.py`
League configuration with Polymarket slug prefixes and Kalshi series tickers.

```
LEAGUES = {
    'epl': {
        'name': 'English Premier League',
        'polymarket_prefix': 'epl',    # slug prefix on Polymarket
        'kalshi_series': 'KXEPL',      # Kalshi series ticker
    },
    'laliga': { ... },
    ...
}
```

### Step 2: Replace `backend/fetch_current_polymarket.py` → `backend/fetch_polymarket.py`
- Remove all BTC/Binance logic
- Fetch active soccer events from Polymarket gamma API using `tag=sports` or slug-based discovery
- For each match event, fetch CLOB prices for all outcomes (Home/Draw/Away)
- Return structured match data:
  ```python
  {
      'slug': 'epl-liv-ars-2026-02-15',
      'home_team': 'Liverpool',
      'away_team': 'Arsenal',
      'league': 'epl',
      'start_time': '2026-02-15T15:00:00Z',
      'outcomes': {
          'Home': {'ask': 0.45, 'bid': 0.43},
          'Draw': {'ask': 0.30, 'bid': 0.28},
          'Away': {'ask': 0.28, 'bid': 0.26},
      }
  }
  ```

### Step 3: Replace `backend/fetch_current_kalshi.py` → `backend/fetch_kalshi.py`
- Remove all BTC/Binance logic
- Query Kalshi markets by series ticker for each league
- For each match, extract yes_ask/no_ask prices
- Return structured match data:
  ```python
  {
      'ticker': 'KXEPLGAME-26FEB15LIVARS',
      'home_team': 'Liverpool',
      'away_team': 'Arsenal',
      'league': 'epl',
      'outcomes': {
          'Home': {'yes_ask': 0.47, 'no_ask': 0.55},
          'Draw': {'yes_ask': 0.28, 'no_ask': 0.74},
          'Away': {'yes_ask': 0.27, 'no_ask': 0.75},
      }
  }
  ```

### Step 4: New file `backend/match_markets.py`
Match the same game across platforms using team name fuzzy matching + date.
- Normalize team names (e.g., "Liverpool FC" ↔ "Liverpool", "Man United" ↔ "Manchester United")
- Match by date + team names
- Return paired matches ready for arbitrage comparison

### Step 5: Replace `backend/api.py` arbitrage logic
New endpoint structure:
- `GET /matches` — list all currently matched pairs across platforms
- `GET /arbitrage` — run arbitrage checks on all matched pairs

For each matched pair, check all 6 combinations:
| # | Buy on Poly | Buy on Kalshi | Condition |
|---|-------------|---------------|-----------|
| 1 | Home (ask)  | Home NO (ask) | sum < 1   |
| 2 | Draw (ask)  | Draw NO (ask) | sum < 1   |
| 3 | Away (ask)  | Away NO (ask) | sum < 1   |
| 4 | Home NO equivalent (1-bid) | Home YES (ask) | sum < 1 |
| 5 | Draw NO equivalent (1-bid) | Draw YES (ask) | sum < 1 |
| 6 | Away NO equivalent (1-bid) | Away YES (ask) | sum < 1 |

### Step 6: Delete obsolete files
- `backend/find_new_market.py` (BTC Polymarket slug generator)
- `backend/find_new_kalshi_market.py` (BTC Kalshi slug generator)
- `backend/get_current_markets.py` (BTC hour-based market picker)
- `backend/arbitrage_bot.py` (BTC CLI scanner)
- `backend/explore_kalshi_api.py` (exploration script)

---

## Frontend Changes

### Step 7: Rewrite `frontend/app/page.tsx`
Replace the BTC dashboard with a soccer arbitrage dashboard:

- **Header**: "Soccer Arbitrage Scanner" + Live badge + league filter dropdown
- **Best Opportunity Hero Card**: Show best margin found across all matches
- **Match Cards Grid**: Each matched pair shows:
  - Team names, league badge, kickoff time
  - Side-by-side Polymarket vs Kalshi prices for Home/Draw/Away
  - Arbitrage checks with margins highlighted
- **Opportunities Table**: All profitable opportunities sorted by margin
- **League filter**: Filter by league or show all

### Step 8: Update TypeScript interfaces
New `MatchData`, `ArbitrageCheck`, etc. interfaces matching the new API response shape.

---

## Files Created/Modified Summary

| Action | File | Description |
|--------|------|-------------|
| CREATE | `backend/leagues.py` | League config (names, API identifiers) |
| CREATE | `backend/fetch_polymarket.py` | Soccer Polymarket data fetcher |
| CREATE | `backend/fetch_kalshi.py` | Soccer Kalshi data fetcher |
| CREATE | `backend/match_markets.py` | Cross-platform match pairing |
| REWRITE | `backend/api.py` | New soccer arbitrage API |
| DELETE | `backend/find_new_market.py` | No longer needed |
| DELETE | `backend/find_new_kalshi_market.py` | No longer needed |
| DELETE | `backend/get_current_markets.py` | No longer needed |
| DELETE | `backend/arbitrage_bot.py` | No longer needed |
| DELETE | `backend/explore_kalshi_api.py` | No longer needed |
| REWRITE | `frontend/app/page.tsx` | Soccer dashboard |
| KEEP | `backend/test_polymarket_sports_api.py` | Reference/test script |
| KEEP | `backend/requirements.txt` | May add `fuzzywuzzy` or similar |
| KEEP | All `frontend/components/ui/*` | shadcn components reused |

---

## Implementation Order

1. `backend/leagues.py` (config, no dependencies)
2. `backend/fetch_polymarket.py` (Polymarket soccer fetcher)
3. `backend/fetch_kalshi.py` (Kalshi soccer fetcher)
4. `backend/match_markets.py` (pairing logic)
5. `backend/api.py` (tie it all together)
6. Delete obsolete backend files
7. `frontend/app/page.tsx` (new dashboard)
8. Test end-to-end
