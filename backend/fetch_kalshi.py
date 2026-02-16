"""
Fetch soccer match data from Kalshi.
Uses the public trade API to discover markets by series ticker.

Kalshi soccer structure:
- Each match has an event_ticker (e.g., KXEPLGAME-26MAR03WOLLFC)
- Each event has 3 markets with tickers ending in team abbreviation or TIE:
  - KXEPLGAME-26MAR03WOLLFC-WOL (Wolverhampton win)
  - KXEPLGAME-26MAR03WOLLFC-TIE (Draw)
  - KXEPLGAME-26MAR03WOLLFC-LFC (Liverpool win)
- Prices are in cents (0-99), need to convert to dollars (0.00-0.99)
"""
import re
import requests
from leagues import LEAGUES

KALSHI_API_URL = "https://api.elections.kalshi.com/trade-api/v2/markets"


def fetch_kalshi_markets_for_series(series_ticker):
    """Fetch all open markets for a Kalshi series ticker with pagination."""
    all_markets = []
    cursor = None

    while True:
        params = {
            "series_ticker": series_ticker,
            "status": "open",
            "limit": 200,
        }
        if cursor:
            params["cursor"] = cursor

        try:
            response = requests.get(KALSHI_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            markets = data.get("markets", [])
            all_markets.extend(markets)

            cursor = data.get("cursor")
            if not cursor or not markets:
                break

        except Exception:
            break

    return all_markets


def _parse_kalshi_match_title(title):
    """
    Parse 'Team A vs Team B Winner?' into (team_a, team_b).
    """
    match = re.match(r"(.+?)\s+vs\s+(.+?)\s+Winner\??", title, re.IGNORECASE)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, None


def parse_kalshi_soccer_markets(raw_markets):
    """
    Group raw Kalshi markets by event_ticker and structure them.
    Each event becomes a match with 3 outcomes identified by ticker suffix.
    """
    events = {}

    for market in raw_markets:
        event_ticker = market.get("event_ticker", "")
        ticker = market.get("ticker", "")
        title = market.get("title", "")

        # Price conversion: cents to dollars
        yes_ask = market.get("yes_ask", 0) / 100.0
        no_ask = market.get("no_ask", 0) / 100.0
        yes_bid = market.get("yes_bid", 0) / 100.0
        no_bid = market.get("no_bid", 0) / 100.0

        if event_ticker not in events:
            home, away = _parse_kalshi_match_title(title)
            events[event_ticker] = {
                "event_ticker": event_ticker,
                "title": title,
                "home_team": home or "",
                "away_team": away or "",
                "outcomes": {},
            }

        # Determine outcome from ticker suffix
        # Ticker format: KXEPLGAME-26MAR03WOLLFC-WOL
        # Suffix is everything after the last hyphen
        suffix = ticker.rsplit("-", 1)[-1] if "-" in ticker else ""

        if suffix == "TIE":
            outcome_name = "Draw"
        else:
            # Suffix is a team abbreviation — figure out if it's home or away
            # We'll store it with the abbreviation for now and resolve in matching
            outcome_name = suffix

        events[event_ticker]["outcomes"][outcome_name] = {
            "ticker": ticker,
            "yes_ask": yes_ask,
            "no_ask": no_ask,
            "yes_bid": yes_bid,
            "no_bid": no_bid,
        }

    # Convert to list and ensure each event has 3 outcomes
    result = []
    for event in events.values():
        if len(event["outcomes"]) == 3:
            result.append(event)

    return result


def fetch_kalshi_soccer_events(league_key=None):
    """
    Fetch all active soccer match events from Kalshi.
    If league_key is provided, only fetch for that league.
    """
    leagues_to_fetch = {}
    if league_key:
        if league_key in LEAGUES:
            leagues_to_fetch[league_key] = LEAGUES[league_key]
    else:
        leagues_to_fetch = LEAGUES

    all_matches = []
    errors = []

    for key, league in leagues_to_fetch.items():
        series = league["kalshi_series"]
        try:
            raw_markets = fetch_kalshi_markets_for_series(series)

            if not raw_markets:
                continue

            parsed_events = parse_kalshi_soccer_markets(raw_markets)

            for event in parsed_events:
                event["league"] = key
                event["league_name"] = league["name"]
                event["source"] = "kalshi"
                all_matches.append(event)

        except Exception as e:
            errors.append(f"Kalshi {league['name']}: {e}")

    return all_matches, errors


if __name__ == "__main__":
    print("Fetching Kalshi soccer events (EPL)...")
    matches, errs = fetch_kalshi_soccer_events("epl")

    if errs:
        for e in errs:
            print(f"ERROR: {e}")

    print(f"\nFound {len(matches)} match events")
    for m in matches[:5]:
        print(f"\n{m['event_ticker']}: {m['title']}")
        print(f"  Home: {m['home_team']}, Away: {m['away_team']}")
        print(f"  League: {m['league_name']}")
        for name, prices in m["outcomes"].items():
            print(f"  {name}: yes_ask={prices['yes_ask']:.2f} no_ask={prices['no_ask']:.2f}")
