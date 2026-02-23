import re
import json

def extract_ptb(market_data):
    """
    Extract Price to Beat from yes_sub_title or no_sub_title if available.
    Example: 'Price to beat: $67,948.02' -> 67948.02
    """
    for field in ['yes_sub_title', 'no_sub_title']:
        sub = market_data.get(field, "")
        if "Price to beat: $" in sub:
            try:
                # Remove 'Price to beat: $', then remove commas
                price_str = sub.split('$')[-1].replace(',', '')
                return float(price_str)
            except (ValueError, IndexError):
                continue
    return None

# Test with our debug data
with open("kalshi_debug_raw.json", "r") as f:
    sample_data = json.load(f)

extracted = extract_ptb(sample_data)
floor = sample_data.get('floor_strike')

print(f"Extracted PTB: {extracted}")
print(f"Floor Strike:  {floor}")
print(f"Diff:          {extracted - floor if extracted and floor else 'N/A'}")
