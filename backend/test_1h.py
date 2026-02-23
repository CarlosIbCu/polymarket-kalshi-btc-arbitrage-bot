import requests

r = requests.get("http://localhost:8000/arbitrage/1h", timeout=30)
d = r.json()
print(f"Polymarket slug: {d.get('polymarket', {}).get('slug', 'N/A')}")
print(f"Kalshi ticker:   {d.get('kalshi', {}).get('event_ticker', 'N/A')}")
print(f"Poly ptb:        ${d.get('polymarket', {}).get('price_to_beat', 0):,.2f}")
print()
for c in d.get("checks", []):
    valid = c.get("is_valid", "?")
    overlap = c.get("overlap_size", 0)
    arb = c.get("is_arbitrage", False)
    marker = "*** ARB ***" if arb else ("INVALID" if not valid else "no arb")
    print(
        f"  {c['type']:10} | Poly {c['poly_leg']:4} + Kalshi {c['kalshi_leg']:3}"
        f" @ ${c.get('kalshi_strike', 0):>9,.0f}"
        f" | valid={str(valid):5} overlap=${overlap:>7,.0f}"
        f" | total={c['total_cost']:.3f} | {marker}"
    )

opps = d.get("opportunities", [])
print(f"\n=== {len(opps)} OPPORTUNITIES ===")
for o in opps:
    print(f"  {o['type']}: margin={o['margin']:.4f} ({o['margin']*100:.2f}%) | overlap=${o.get('overlap_size',0):,.0f}")
