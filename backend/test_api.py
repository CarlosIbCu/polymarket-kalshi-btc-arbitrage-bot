import requests
import json
import time

time.sleep(4)  # wait for server to start

try:
    r = requests.get("http://localhost:8000/arbitrage", timeout=15)
    d = r.json()
    print("=== ARBITRAGE API TEST ===")
    print(f"Errors: {d.get('errors', [])}")
    print()

    poly = d.get("polymarket", {})
    kalshi = d.get("kalshi", {})

    if poly:
        print(f"Polymarket Slug: {poly.get('slug', 'N/A')}")
        prices = poly.get("prices", {})
        print(f"  Up:   ${prices.get('Up', 0):.3f}")
        print(f"  Down: ${prices.get('Down', 0):.3f}")
        ptb = poly.get("price_to_beat")
        if ptb:
            print(f"  Price to Beat: ${ptb:,.2f}")
    print()
    if kalshi:
        print(f"Kalshi Event: {kalshi.get('event_ticker', 'N/A')}")
        print(f"  Kalshi Yes (Up): ${kalshi.get('yes_ask', 0):.3f}")
        print(f"  Kalshi No (Down): ${kalshi.get('no_ask', 0):.3f}")
        fs = kalshi.get("floor_strike")
        if fs:
            print(f"  Floor Strike: ${fs:,.2f}")
    print()
    print("=== CHECKS ===")
    for c in d.get("checks", []):
        arb_flag = "*** ARBITRAGE ***" if c["is_arbitrage"] else ""
        print(f"  {c['type']}: Poly {c['poly_leg']}={c['poly_cost']:.3f} + Kalshi {c['kalshi_leg']}={c['kalshi_cost']:.3f} = {c['total_cost']:.3f} {arb_flag}")
    print()
    opps = d.get("opportunities", [])
    if opps:
        print(f"=== OPPORTUNITIES FOUND: {len(opps)} ===")
        for o in opps:
            print(f"  {o['type']}: Margin = {o['margin']:.4f} ({o['margin']*100:.2f}%)")
    else:
        print("No arbitrage opportunities found (normal)")
except Exception as e:
    print(f"Error: {e}")
