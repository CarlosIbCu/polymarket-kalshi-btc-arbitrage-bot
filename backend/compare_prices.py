from fetch_current_polymarket import (
    get_chainlink_btc_usd_price, 
    get_coinbase_current_price, 
    get_binance_current_price,
    get_polymarket_ptb,
    get_window_open_price
)
from find_new_market import get_current_market_slug, get_current_15min_window
import datetime
import pytz

def compare_prices():
    slug = get_current_market_slug()
    now = datetime.datetime.now(pytz.utc)
    window_start = get_current_15min_window(now)
    
    print(f"Slug: {slug}")
    print(f"Window Start: {window_start}")
    
    print("\n--- Current Price ---")
    cl_price, cl_err = get_chainlink_btc_usd_price()
    cb_price, cb_err = get_coinbase_current_price()
    bn_price, bn_err = get_binance_current_price()
    
    print(f"Chainlink: {cl_price} (Err: {cl_err})")
    print(f"Coinbase:  {cb_price} (Err: {cb_err})")
    print(f"Binance:   {bn_price} (Err: {bn_err})")
    
    print("\n--- Price to Beat ---")
    gamma_ptb, gamma_err = get_polymarket_ptb(slug)
    binance_ptb, binance_err = get_window_open_price(window_start)
    
    print(f"Gamma PTB:   {gamma_ptb} (Err: {gamma_err})")
    print(f"Binance PTB: {binance_ptb} (Err: {binance_err})")

if __name__ == "__main__":
    compare_prices()
