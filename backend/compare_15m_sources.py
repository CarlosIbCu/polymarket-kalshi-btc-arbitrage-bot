import requests
import datetime
import pytz
from fetch_current_polymarket import get_chainlink_btc_usd_price, get_window_open_price as get_binance_open, get_binance_current_price
from get_current_markets import get_current_market_urls

def compare_sources():
    market_info = get_current_market_urls()
    target_time = market_info["target_time_utc"]
    
    # Binance
    binance_ptb, _ = get_binance_open(target_time)
    binance_curr, _ = get_binance_current_price()
    
    # Chainlink Ethereum
    cl_curr, _ = get_chainlink_btc_usd_price()
    
    print(f"Target Time (UTC): {target_time}")
    print(f"--- Binance ---")
    print(f"  PTB (Open):    ${binance_ptb}")
    print(f"  Current:       ${binance_curr}")
    print(f"--- Chainlink (Eth) ---")
    print(f"  Current:       ${cl_curr}")
    
    print(f"\nUser Reported Polymarket:")
    print(f"  PTB:           $66,785.86")
    print(f"  Current:       $66,879.0")

if __name__ == "__main__":
    compare_sources()
