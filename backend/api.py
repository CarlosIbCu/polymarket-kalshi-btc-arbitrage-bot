from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import datetime
import traceback

# 15-minute market fetchers
from fetch_current_polymarket import fetch_polymarket_data_struct as fetch_poly_15m
from fetch_current_kalshi import fetch_kalshi_data_struct as fetch_kalshi_15m

# 1-hour market fetchers
from fetch_current_polymarket_1h import fetch_polymarket_data_struct as fetch_poly_1h
from fetch_current_kalshi_1h import fetch_kalshi_data_struct as fetch_kalshi_1h

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.datetime.now().isoformat()}


# ── Leg price bounds for true arbitrage ──────────────────────────────────────
MIN_LEG = 0.10   # legs below 10¢ signal markets are in agreement, not disagreement
MAX_LEG = 0.90   # legs above 90¢ signal the same (other side would be < 10¢)


def is_valid_arb(
    poly_direction: str, poly_threshold: float,
    kalshi_direction: str, kalshi_threshold: float,
    poly_cost: float = 0.0, kalshi_cost: float = 0.0,
) -> tuple[bool, float]:
    """
    Validate that the two contract legs form a genuine arbitrage.

    Three rules must ALL pass:
      Rule 1 – Minimum leg price (10¢): cheap legs mean platforms AGREE, not disagree.
      Rule 2 – Maximum leg price (90¢): expensive legs mean the same (flip side < 10¢).
      Rule 3 – Direction overlap: legs must point toward each other with no gap.

    Valid direction combinations:
      - Poly DOWN + Kalshi YES: valid when kalshi_threshold < poly_threshold
      - Poly UP   + Kalshi NO:  valid when poly_threshold  < kalshi_threshold

    Returns:
        (is_valid: bool, overlap_size: float)
        overlap_size > 0: genuine overlap zone
        overlap_size = 0: contracts just touch (borderline)
        overlap_size < 0: GAP – invalid regardless of cost
    """
    # Rule 1 & 2: Both legs must be priced within 10–90¢
    if poly_cost > 0 and (poly_cost < MIN_LEG or poly_cost > MAX_LEG):
        return False, 0.0
    if kalshi_cost > 0 and (kalshi_cost < MIN_LEG or kalshi_cost > MAX_LEG):
        return False, 0.0

    d = poly_direction.upper()
    k = kalshi_direction.upper()

    # Rule 3: Direction overlap
    if d == "DOWN" and k == "YES":
        overlap = poly_threshold - kalshi_threshold
        return overlap >= 0, overlap

    if d == "UP" and k == "NO":
        overlap = kalshi_threshold - poly_threshold
        return overlap >= 0, overlap

    # Same-direction pairings — always invalid
    return False, -(abs(poly_threshold - kalshi_threshold))


def _build_15m_arbitrage(poly_data, kalshi_data):
    """
    15-minute arbitrage: both markets are simple binary Up/Down (Yes/No).

    Polymarket and Kalshi each use the opening price of the 15-min candle as
    their threshold, but via different oracles (Chainlink vs CF Benchmarks BRTI).
    We validate threshold overlap before flagging any opportunity.

    Valid checks:
      - Poly UP   + Kalshi NO  (valid if poly_ptb <= kalshi_floor_strike)
      - Poly DOWN + Kalshi YES (valid if kalshi_floor_strike <= poly_ptb)
    """
    checks = []
    opportunities = []

    poly_up = poly_data['prices'].get('Up', 0.0)
    poly_down = poly_data['prices'].get('Down', 0.0)
    kalshi_yes = kalshi_data['yes_ask']   # Kalshi YES = price goes Up
    kalshi_no  = kalshi_data['no_ask']    # Kalshi NO  = price goes Down

    poly_ptb  = poly_data.get('price_to_beat') or 0.0
    kalshi_fs = kalshi_data.get('floor_strike') or 0.0
    current   = poly_data.get('current_price')

    for poly_leg, poly_cost, kalshi_leg, kalshi_cost, label in [
        ("Up",   poly_up,   "No",  kalshi_no,  "Up Arb"),
        ("Down", poly_down, "Yes", kalshi_yes, "Down Arb"),
    ]:
        valid, overlap = is_valid_arb(poly_leg, poly_ptb, kalshi_leg, kalshi_fs,
                                       poly_cost, kalshi_cost)
        total = poly_cost + kalshi_cost
        is_arb = valid and total < 1.00 and poly_cost > 0 and kalshi_cost > 0

        check = {
            "type": label,
            "poly_leg": poly_leg,
            "kalshi_leg": kalshi_leg,
            "poly_cost": poly_cost,
            "kalshi_cost": kalshi_cost,
            "total_cost": total,
            "is_valid": valid,
            "overlap_size": round(overlap, 2),
            "is_arbitrage": is_arb,
            "margin": round(1.00 - total, 6) if is_arb else 0,
            "poly_price_to_beat": poly_ptb,
            "kalshi_floor_strike": kalshi_fs,
            "kalshi_market_ticker": kalshi_data.get('market', {}).get('ticker'),
            "kalshi_strike_label": f"${kalshi_fs:,.4f} or {'above' if kalshi_leg == 'Yes' else 'below'}",
            "current_price": current,
        }
        checks.append(check)
        if is_arb:
            opportunities.append(check)

    return checks, opportunities


def _build_1h_arbitrage(poly_data, kalshi_data):
    """
    1-hour arbitrage: Polymarket is binary Up/Down; Kalshi has a multi-strike ladder.

    For each Kalshi strike near the Polymarket threshold, we pair it with the
    correct Polymarket leg and validate the overlap before flagging.

    Only valid pairings:
      - Kalshi strike BELOW poly threshold → Poly DOWN + Kalshi YES (overlap = poly_ptb - k_strike)
      - Kalshi strike ABOVE poly threshold → Poly UP   + Kalshi NO  (overlap = k_strike - poly_ptb)

    Equal strikes are borderline (overlap = 0) but not discarded — they still
    carry no gap risk.
    """
    checks = []
    opportunities = []

    poly_strike = poly_data.get('price_to_beat')
    poly_up     = poly_data['prices'].get('Up', 0.0)
    poly_down   = poly_data['prices'].get('Down', 0.0)
    current     = poly_data.get('current_price')

    if poly_strike is None:
        return checks, opportunities

    kalshi_markets = kalshi_data.get('markets', [])
    if not kalshi_markets:
        return checks, opportunities

    # Select 4 markets below + 4 above the poly opening price
    closest_idx = min(
        range(len(kalshi_markets)),
        key=lambda i: abs(kalshi_markets[i]['strike'] - poly_strike)
    )
    start    = max(0, closest_idx - 4)
    end      = min(len(kalshi_markets), closest_idx + 5)
    selected = kalshi_markets[start:end]

    for km in selected:
        k_strike   = km['strike']
        k_yes_dec  = km['yes_ask_dec']  # YES = price closes above k_strike
        k_no_dec   = km['no_ask_dec']   # NO  = price closes below k_strike

        if k_strike < poly_strike:
            # Kalshi YES (above k_strike) + Poly DOWN (below poly_strike)
            # Overlap zone: [k_strike, poly_strike] ✅
            poly_leg, poly_cost   = "Down", poly_down
            kalshi_leg, kalshi_cost = "Yes", k_yes_dec
            arb_type = "Down Arb"
        elif k_strike > poly_strike:
            # Poly UP (above poly_strike) + Kalshi NO (below k_strike)
            # Overlap zone: [poly_strike, k_strike] ✅
            poly_leg, poly_cost   = "Up", poly_up
            kalshi_leg, kalshi_cost = "No", k_no_dec
            arb_type = "Up Arb"
        else:
            # Equal strike — overlap = 0, check both alignments
            for pl, pc, kl, kc, lbl in [
                ("Down", poly_down, "Yes", k_yes_dec, "Down Arb"),
                ("Up",   poly_up,   "No",  k_no_dec,  "Up Arb"),
            ]:
                valid, overlap = is_valid_arb(pl, poly_strike, kl, k_strike, pc, kc)
                total  = pc + kc
                is_arb = valid and total < 1.00 and pc > 0 and kc > 0
                c = {
                    "type": lbl,
                    "poly_leg": pl, "kalshi_leg": kl,
                    "kalshi_strike": k_strike,
                    "poly_cost": pc, "kalshi_cost": kc,
                    "total_cost": total,
                    "is_valid": valid,
                    "overlap_size": round(overlap, 2),
                    "is_arbitrage": is_arb,
                    "margin": round(1.00 - total, 6) if is_arb else 0,
                    "poly_price_to_beat": poly_strike,
                    "kalshi_market_ticker": km.get('ticker'),
                    "kalshi_strike_label": f"${k_strike:,.4f} or {'above' if kl == 'Yes' else 'below'}",
                    "current_price": current,
                }
                checks.append(c)
                if is_arb:
                    opportunities.append(c)
            continue

        valid, overlap = is_valid_arb(poly_leg, poly_strike, kalshi_leg, k_strike,
                                       poly_cost, kalshi_cost)
        total  = poly_cost + kalshi_cost
        is_arb = valid and total < 1.00 and poly_cost > 0 and kalshi_cost > 0

        check = {
            "type": arb_type,
            "poly_leg": poly_leg, "kalshi_leg": kalshi_leg,
            "kalshi_strike": k_strike,
            "poly_cost": poly_cost, "kalshi_cost": kalshi_cost,
            "total_cost": total,
            "is_valid": valid,
            "overlap_size": round(overlap, 2),
            "is_arbitrage": is_arb,
            "margin": round(1.00 - total, 6) if is_arb else 0,
            "poly_price_to_beat": poly_strike,
            "kalshi_market_ticker": km.get('ticker'),
            "kalshi_strike_label": f"${k_strike:,.4f} or {'above' if kalshi_leg == 'Yes' else 'below'}",
            "current_price": current,
        }
        checks.append(check)
        if is_arb:
            opportunities.append(check)

    return checks, opportunities


@app.get("/arbitrage/{asset}/15m")
@app.get("/arbitrage/15m")
def get_arbitrage_15m(asset: str = "btc"):
    """
    15-minute arbitrage (Polymarket 15M ↔ Kalshi KX{ASSET}15M).
    Default asset is BTC for backward compatibility.
    """
    errors = []
    poly_data = kalshi_data = None

    try:
        poly_data, err = fetch_poly_15m(asset=asset)
        if err:
            errors.append(f"Polymarket: {err}")
    except Exception as e:
        errors.append(f"Polymarket exception: {str(e)}")

    try:
        kalshi_data, err = fetch_kalshi_15m(asset=asset)
        if err:
            errors.append(f"Kalshi: {err}")
    except Exception as e:
        errors.append(f"Kalshi exception: {str(e)}")

    checks, opportunities = [], []
    if poly_data and kalshi_data:
        try:
            checks, opportunities = _build_15m_arbitrage(poly_data, kalshi_data)
        except Exception as e:
            errors.append(f"Processing: {str(e)}")
            print(traceback.format_exc())

    slug = poly_data.get('slug') if poly_data else 'N/A'
    ptb = poly_data.get('price_to_beat') if poly_data else 'N/A'
    cur = poly_data.get('current_price') if poly_data else 'N/A'
    print(f"[API 15m] Asset: {asset.upper()} | Slug: {slug} | PTB: {ptb} | Current: {cur}")
    
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "market_type": "15m",
        "asset": asset.upper(),
        "polymarket": poly_data,
        "kalshi": kalshi_data,
        "checks": checks,
        "opportunities": opportunities,
        "errors": errors,
    }


@app.get("/arbitrage/{asset}/1h")
@app.get("/arbitrage/1h")
def get_arbitrage_1h(asset: str = "btc"):
    """
    1-hour arbitrage (Polymarket 1H ↔ Kalshi KX{ASSET}D multi-strike).
    Default asset is BTC for backward compatibility.
    """
    errors = []
    poly_data = kalshi_data = None

    try:
        poly_data, err = fetch_poly_1h(asset=asset)
        if err:
            errors.append(f"Polymarket: {err}")
    except Exception as e:
        errors.append(f"Polymarket exception: {str(e)}")

    try:
        kalshi_data, err = fetch_kalshi_1h(asset=asset)
        if err:
            errors.append(f"Kalshi: {err}")
    except Exception as e:
        errors.append(f"Kalshi exception: {str(e)}")

    checks, opportunities = [], []
    if poly_data and kalshi_data:
        try:
            checks, opportunities = _build_1h_arbitrage(poly_data, kalshi_data)
        except Exception as e:
            errors.append(f"Processing: {str(e)}")
            print(traceback.format_exc())

    slug = poly_data.get('slug') if poly_data else 'N/A'
    ptb = poly_data.get('price_to_beat') if poly_data else 'N/A'
    cur = poly_data.get('current_price') if poly_data else 'N/A'
    print(f"[API 1h] Asset: {asset.upper()} | Slug: {slug} | PTB: {ptb} | Current: {cur}")
    
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "market_type": "1h",
        "asset": asset.upper(),
        "polymarket": poly_data,
        "kalshi": kalshi_data,
        "checks": checks,
        "opportunities": opportunities,
        "errors": errors,
    }


# Backward compat — keep /arbitrage pointing to BTC 15m
@app.get("/arbitrage")
def get_arbitrage_data():
    return get_arbitrage_15m(asset="btc")


@app.get("/market-outcome")
def get_market_outcome(poly_slug: str, kalshi_ticker: str):
    """
    Checks resolution status and outcome for both Poly and Kalshi markets.
    """
    res = {
        "poly_status": "active",
        "poly_outcome": None,
        "kalshi_status": "active",
        "kalshi_outcome": None,
        "resolved": False
    }

    # 1. Check Polymarket
    try:
        url = f"https://gamma-api.polymarket.com/events?slug={poly_slug}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data and len(data) > 0:
                event = data[0]
                markets = event.get("markets", [])
                if markets:
                    m = markets[0]
                    res["poly_status"] = m.get("status", "active")
                    # Polymarket: outcome is "up" or "down" indices usually etc.
                    # We look for binary outcomes if possible.
                    if res["poly_status"] == "resolved":
                        # If poly_outcome is null, we can try to guess or use CLOB
                        # but gamma usually has 'outcome' or we can check prices
                        res["poly_outcome"] = m.get("outcome") 
    except:
        pass

    # 2. Check Kalshi
    try:
        url = f"https://api.elections.kalshi.com/trade-api/v2/markets/{kalshi_ticker}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            m = data.get("market", {})
            res["kalshi_status"] = m.get("status", "active")
            if res["kalshi_status"] in ["finalized", "settled"]:
                res["kalshi_outcome"] = m.get("result") # "yes" or "no"

    except:
        pass

    res["resolved"] = (res["poly_status"] == "resolved") and (res["kalshi_status"] in ["finalized", "settled"])
    return res

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
