"""
Fetch soccer match data from Polymarket.
Uses the gamma API with tag_slug to discover match events,
and the CLOB API for live order book prices.

Polymarket soccer structure:
- Each match is an event with exactly 3 markets (Home Win, Draw, Away Win)
- Each market is binary Yes/No with its own CLOB token pair
- The outcome name comes from groupItemTitle (e.g., "Liverpool FC", "Draw (...)")
"""
import requests
from leagues import LEAGUES

GAMMA_API_URL = "https://gamma-api.polymarket.com/events"
CLOB_API_URL = "https://clob.polymarket.com/book"


def get_clob_price(token_id):
    """Fetch best bid/ask from CLOB order book for a token."""
    try:
        response = requests.get(CLOB_API_URL, params={"token_id": token_id}, timeout=5)
        response.raise_for_status()
        data = response.json()

        bids = data.get("bids", [])
        asks = data.get("asks", [])

        best_bid = max(float(b["price"]) for b in bids) if bids else 0.0
        best_ask = min(float(a["price"]) for a in asks) if asks else 0.0

        return {"bid": best_bid, "ask": best_ask}
    except Exception:
        return {"bid": 0.0, "ask": 0.0}


def _parse_outcome_name(market):
    """
    Extract a clean outcome name from a Polymarket market.
    Uses groupItemTitle first, falls back to parsing the question.
    """
    group_title = market.get("groupItemTitle", "")
    if group_title:
        # Clean up "Draw (Team A vs. Team B)" -> "Draw"
        if group_title.lower().startswith("draw"):
            return "Draw"
        return group_title

    question = market.get("question", "")
    if "draw" in question.lower():
        return "Draw"
    # "Will Team X win on 2026-02-15?" -> "Team X"
    if question.startswith("Will ") and " win " in question:
        team = question[5:question.index(" win ")]
        return team

    return question


def fetch_polymarket_soccer_events(league_key=None):
    """
    Fetch active soccer match events from Polymarket.
    Filters to events with exactly 3 markets (Home/Draw/Away).
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
        tag_slug = league["polymarket_tag_slug"]
        try:
            offset = 0
            limit = 100
            while True:
                response = requests.get(
                    GAMMA_API_URL,
                    params={
                        "active": "true",
                        "closed": "false",
                        "tag_slug": tag_slug,
                        "limit": limit,
                        "offset": offset,
                    },
                    timeout=15,
                )
                response.raise_for_status()
                events = response.json()

                if not events:
                    break

                for event in events:
                    markets = event.get("markets", [])
                    # Match events have exactly 3 markets (home/draw/away)
                    if len(markets) != 3:
                        continue

                    outcomes = {}
                    for market in markets:
                        outcome_name = _parse_outcome_name(market)

                        raw_token_ids = market.get("clobTokenIds")
                        if isinstance(raw_token_ids, str):
                            raw_token_ids = eval(raw_token_ids)

                        if not raw_token_ids or len(raw_token_ids) < 1:
                            continue

                        # First token is YES, fetch its price
                        yes_token_id = raw_token_ids[0]
                        prices = get_clob_price(yes_token_id)
                        outcomes[outcome_name] = prices

                    if len(outcomes) == 3:
                        all_matches.append({
                            "slug": event.get("slug", ""),
                            "title": event.get("title", ""),
                            "start_time": event.get("startDate", ""),
                            "end_time": event.get("endDate", ""),
                            "league": key,
                            "league_name": league["name"],
                            "outcomes": outcomes,
                            "source": "polymarket",
                        })

                if len(events) < limit:
                    break
                offset += limit

        except Exception as e:
            errors.append(f"Polymarket {league['name']}: {e}")

    return all_matches, errors


if __name__ == "__main__":
    print("Fetching Polymarket soccer events (EPL)...")
    matches, errs = fetch_polymarket_soccer_events("epl")

    if errs:
        for e in errs:
            print(f"ERROR: {e}")

    print(f"\nFound {len(matches)} match events")
    for m in matches[:5]:
        print(f"\n{m['title']} ({m['slug']})")
        print(f"  League: {m['league_name']}")
        for outcome, prices in m["outcomes"].items():
            print(f"  {outcome}: bid={prices['bid']:.3f} ask={prices['ask']:.3f}")
