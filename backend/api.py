from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fetch_polymarket import fetch_polymarket_soccer_events
from fetch_kalshi import fetch_kalshi_soccer_events
from match_markets import match_markets
from leagues import LEAGUES
import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def check_arbitrage_for_pair(pair):
    """
    Run arbitrage checks on a matched pair of markets.
    For each outcome (Home/Draw/Away), check both directions:
      1. Buy outcome on Poly (ask) + Buy NO on Kalshi (no_ask) < $1.00
      2. Buy outcome on Kalshi (yes_ask) + Sell on Poly (1 - bid) < $1.00
    """
    poly = pair["polymarket"]
    kalshi = pair["kalshi"]
    poly_outcomes = poly.get("outcomes", {})
    kalshi_outcomes = kalshi.get("outcomes", {})

    checks = []

    # Map Polymarket outcomes to Kalshi outcomes
    # Polymarket: "Home Team", "Draw", "Away Team" (or similar)
    # Kalshi: separate markets per outcome
    #
    # We need to align them. Both platforms should have ~3 outcomes for a match.
    # We'll try to match by outcome name similarity.
    outcome_pairs = _align_outcomes(poly_outcomes, kalshi_outcomes)

    for outcome_name, poly_prices, kalshi_prices in outcome_pairs:
        poly_ask = poly_prices.get("ask", 0)
        poly_bid = poly_prices.get("bid", 0)
        kalshi_yes_ask = kalshi_prices.get("yes_ask", 0)
        kalshi_no_ask = kalshi_prices.get("no_ask", 0)

        # Direction 1: Buy on Polymarket + Buy NO on Kalshi
        if poly_ask > 0 and kalshi_no_ask > 0:
            total = poly_ask + kalshi_no_ask
            check = {
                "outcome": outcome_name,
                "direction": "Poly YES + Kalshi NO",
                "poly_cost": poly_ask,
                "kalshi_cost": kalshi_no_ask,
                "total_cost": total,
                "is_arbitrage": total < 1.00,
                "margin": max(0, 1.00 - total),
            }
            checks.append(check)

        # Direction 2: Buy on Kalshi + Sell on Polymarket
        if kalshi_yes_ask > 0 and poly_bid > 0:
            poly_sell_cost = 1.0 - poly_bid  # cost to be short on Poly
            total = kalshi_yes_ask + poly_sell_cost
            check = {
                "outcome": outcome_name,
                "direction": "Kalshi YES + Poly NO",
                "poly_cost": poly_sell_cost,
                "kalshi_cost": kalshi_yes_ask,
                "total_cost": total,
                "is_arbitrage": total < 1.00,
                "margin": max(0, 1.00 - total),
            }
            checks.append(check)

    return checks


def _align_outcomes(poly_outcomes, kalshi_outcomes):
    """
    Align Polymarket and Kalshi outcomes by name.
    Returns list of (outcome_name, poly_prices, kalshi_prices) tuples.
    """
    from match_markets import similarity

    aligned = []
    used_kalshi = set()

    for poly_name, poly_prices in poly_outcomes.items():
        best_match = None
        best_score = 0

        for kalshi_name, kalshi_prices in kalshi_outcomes.items():
            if kalshi_name in used_kalshi:
                continue

            # Check name similarity
            score = similarity(poly_name.lower(), kalshi_name.lower())

            # Boost score for exact keyword matches
            if "draw" in poly_name.lower() and "draw" in kalshi_name.lower():
                score = max(score, 0.95)

            if score > best_score:
                best_score = score
                best_match = (kalshi_name, kalshi_prices)

        if best_match and best_score > 0.4:
            used_kalshi.add(best_match[0])
            aligned.append((poly_name, poly_prices, best_match[1]))

    return aligned


@app.get("/arbitrage")
def get_arbitrage_data(league: str = Query(default=None)):
    """
    Fetch all soccer markets, match them, and run arbitrage checks.
    Optional league filter (e.g., ?league=epl).
    """
    poly_matches, poly_errors = fetch_polymarket_soccer_events(league)
    kalshi_matches, kalshi_errors = fetch_kalshi_soccer_events(league)

    paired = match_markets(poly_matches, kalshi_matches)

    all_checks = []
    all_opportunities = []

    for pair in paired:
        checks = check_arbitrage_for_pair(pair)
        match_info = {
            "home_team": pair["home_team"],
            "away_team": pair["away_team"],
            "league": pair["league"],
            "league_name": pair["league_name"],
            "poly_slug": pair["polymarket"].get("slug", ""),
            "kalshi_ticker": pair["kalshi"].get("event_ticker", ""),
            "polymarket_outcomes": pair["polymarket"].get("outcomes", {}),
            "kalshi_outcomes": {
                k: {
                    "yes_ask": v.get("yes_ask", 0),
                    "no_ask": v.get("no_ask", 0),
                    "yes_bid": v.get("yes_bid", 0),
                    "no_bid": v.get("no_bid", 0),
                }
                for k, v in pair["kalshi"].get("outcomes", {}).items()
            },
            "checks": checks,
            "opportunities": [c for c in checks if c["is_arbitrage"]],
        }
        all_checks.append(match_info)
        all_opportunities.extend(match_info["opportunities"])

    # Sort opportunities by margin descending
    all_opportunities.sort(key=lambda x: x["margin"], reverse=True)

    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "total_matches": len(paired),
        "total_poly_events": len(poly_matches),
        "total_kalshi_events": len(kalshi_matches),
        "matches": all_checks,
        "opportunities": all_opportunities,
        "errors": poly_errors + kalshi_errors,
        "leagues": {k: v["name"] for k, v in LEAGUES.items()},
    }


@app.get("/leagues")
def get_leagues():
    """Return list of supported leagues."""
    return {k: v["name"] for k, v in LEAGUES.items()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
