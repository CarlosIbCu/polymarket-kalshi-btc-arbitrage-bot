import requests
import time
import datetime
import json
import pytz
from get_current_markets import get_current_market_urls
from web3 import Web3
import concurrent.futures

# Configuration
POLYMARKET_API_URL = "https://gamma-api.polymarket.com/events"
BINANCE_PRICE_URL = "https://api.binance.com/api/v3/ticker/price"
BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
COINBASE_TICKER_URL = "https://api.exchange.coinbase.com/products/BTC-USD/ticker"
# Chainlink Price Feeds on Ethereum Mainnet
CHAINLINK_BTC_USD_PROXY = "0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c"
CHAINLINK_ETH_USD_PROXY = "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419"
CHAINLINK_SOL_USD_PROXY = "0x4ffc43a60ed71866380a96f13b6329c488ce9f01507"
# XRP lacks a standard Chainlink proxy on Ethereum Mainnet; will fall back to exchange APIs.

# Chainlink AggregatorV3Interface ABI (only the function we need)
CHAINLINK_ABI = [
    {
        "inputs": [],
        "name": "latestRoundData",
        "outputs": [
            {"internalType": "uint80", "name": "roundId", "type": "uint80"},
            {"internalType": "int256", "name": "answer", "type": "int256"},
            {"internalType": "uint256", "name": "startedAt", "type": "uint256"},
            {"internalType": "uint256", "name": "updatedAt", "type": "uint256"},
            {"internalType": "uint80", "name": "answeredInRound", "type": "uint80"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# The 15m Polymarket market resolves via Chainlink BTC/USD.
# Now we fetch the actual Chainlink price instead of using Binance as a proxy.
# Note: We use the 15m kline interval for the opening price.

# Retry settings
MAX_RETRIES = 3
TIMEOUT = 5  # seconds

def fetch_with_retry(url, params=None, max_retries=MAX_RETRIES, timeout=TIMEOUT):
    """Make a request with retries and timeout."""
    last_error = None
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json(), None
        except requests.exceptions.Timeout:
            last_error = f"Timeout (attempt {attempt + 1}/{max_retries})"
        except requests.exceptions.RequestException as e:
            last_error = str(e)

        if attempt < max_retries - 1:
            time.sleep(0.5 * (attempt + 1))

    return None, last_error

CLOB_API_URL = "https://clob.polymarket.com"

# ── Token ID cache ────────────────────────────────────────────────────────────
# The gamma API CDN caches bestBid/bestAsk for 30+ seconds — useless for live
# data. Instead, we fetch clobTokenIds from gamma once per slug, then hit the
# CLOB /book endpoint directly every call for real-time orderbook prices.
_token_id_cache: dict[str, list[str]] = {}


def _get_clob_token_ids(slug: str) -> list[str]:
    """
    Return [up_token_id, down_token_id] for a slug, with in-process caching.
    Token IDs are stable per market, so we only need to fetch from gamma once.
    """
    if slug in _token_id_cache:
        return _token_id_cache[slug]

    data, err = fetch_with_retry(POLYMARKET_API_URL, params={"slug": slug})
    if err or not data:
        return []

    markets = data[0].get("markets", [])
    if not markets:
        return []

    raw = markets[0].get("clobTokenIds", "[]")
    token_ids = json.loads(raw) if isinstance(raw, str) else (raw or [])
    _token_id_cache[slug] = token_ids
    return token_ids


def _get_clob_midpoint(token_id: str) -> float | None:
    """
    Fetch the current mid-price for one token from the CLOB /midpoint endpoint.
    Mid = (bestBid + bestAsk) / 2 — the fairest single price for the outcome.
    Returns None on failure.
    """
    data, err = fetch_with_retry(
        f"{CLOB_API_URL}/midpoint",
        params={"token_id": token_id},
    )
    if err or not data:
        return None
    mid = data.get("mid")
    return float(mid) if mid is not None else None


def get_polymarket_data(slug):
    """
    Fetch the Up/Down BUY prices for a 15m Polymarket BTC market by slug.

    Two-tier approach for real-time accuracy:
      1. gamma API    → clobTokenIds (cached once per slug)
      2. CLOB /midpoint → live mid-price for each token (updates every call)

    Up price   = midpoint of Up token
    Down price = midpoint of Down token

    Falls back to gamma outcomePrices (mid-market, CDN-cached) if CLOB unavailable.
    """
    token_ids     = _get_clob_token_ids(slug)
    up_token_id   = token_ids[0] if len(token_ids) > 0 else None
    down_token_id = token_ids[1] if len(token_ids) > 1 else None

    up_buy_price: float = 0.0
    down_buy_price: float = 0.0
    used_clob = False

    up_mid   = _get_clob_midpoint(up_token_id)   if up_token_id   else None
    down_mid = _get_clob_midpoint(down_token_id) if down_token_id else None

    if up_mid is not None or down_mid is not None:
        up_buy_price   = up_mid   if up_mid   is not None else 0.0
        down_buy_price = down_mid if down_mid is not None else 0.0
        used_clob = True

    # Fallback: gamma outcomePrices (mid-market, CDN-cached ~30s)
    if not used_clob:
        data, err = fetch_with_retry(POLYMARKET_API_URL, params={"slug": slug})
        if err or not data:
            return None, f"Polymarket API error: {err or 'no data'}"

        markets = data[0].get("markets", [])
        if not markets:
            return None, "Markets not found in event"

        market = markets[0]
        outcome_prices_raw = market.get("outcomePrices", "[]")
        outcome_prices = json.loads(outcome_prices_raw) if isinstance(outcome_prices_raw, str) else outcome_prices_raw
        outcomes_raw = market.get("outcomes", "[]")
        outcomes = json.loads(outcomes_raw) if isinstance(outcomes_raw, str) else outcomes_raw

        for outcome, price_str in zip(outcomes, outcome_prices):
            try:
                price = float(price_str)
            except (ValueError, TypeError):
                price = 0.0
            ol = (outcome or "").lower()
            if ol in ("up", "yes", "over"):
                up_buy_price = price
            elif ol in ("down", "no", "under"):
                down_buy_price = price

    return {
        "Up": round(up_buy_price, 4),
        "Down": round(down_buy_price, 4),
    }, None



def get_binance_current_price(asset="btc"):
    """Get the current spot price from Binance as a fallback."""
    asset_map = {"btc": "BTCUSDT", "eth": "ETHUSDT", "sol": "SOLUSDT", "xrp": "XRPUSDT"}
    symbol = asset_map.get(asset.lower(), "BTCUSDT")
    data, err = fetch_with_retry(BINANCE_PRICE_URL, params={"symbol": symbol})
    if err:
        return None, f"Binance price error: {err}"
    try:
        return float(data["price"]), None
    except (KeyError, TypeError) as e:
        return None, f"Parse error: {e}"


def get_coinbase_current_price(asset="btc"):
    """Get the current spot price from Coinbase."""
    asset_map = {"btc": "BTC-USD", "eth": "ETH-USD", "sol": "SOL-USD", "xrp": "XRP-USD"}
    product_id = asset_map.get(asset.lower(), "BTC-USD")
    url = f"https://api.exchange.coinbase.com/products/{product_id}/ticker"
    data, err = fetch_with_retry(url)
    if err:
        return None, f"Coinbase price error: {err}"
    try:
        return float(data["price"]), None
    except (KeyError, TypeError) as e:
        return None, f"Parse error: {e}"


def get_clob_current_price(token_id: str):
    """
    Get the current mid-price for the Up outcome from the Polymarket CLOB API.
    Returns (price, None) on success or (None, error) on failure.
    """
    try:
        buy_r, _ = fetch_with_retry(
            "https://clob.polymarket.com/price",
            params={"token_id": token_id, "side": "BUY"},
        )
        sell_r, _ = fetch_with_retry(
            "https://clob.polymarket.com/price",
            params={"token_id": token_id, "side": "SELL"},
        )
        if buy_r and sell_r and "price" in buy_r and "price" in sell_r:
            mid = (float(buy_r["price"]) + float(sell_r["price"])) / 2
            return round(mid, 4), None
        return None, "CLOB price unavailable"
    except Exception as e:
        return None, str(e)


# Web3 connection cache for reuse
_web3_instance = None

# Cache for Chainlink price at window start
_chainlink_price_cache = {
    "window_start": None,
    "price": None,
}


def _get_chainlink_price_at_window_start(target_time_utc, asset="btc"):
    """
    Get the Chainlink price at the start of the window.
    Uses caching to avoid making too many requests.
    """
    global _chainlink_price_cache
    
    cache_key = f"{asset}_{target_time_utc}"
    # Check if we have a cached price for this window
    if (_chainlink_price_cache.get("window_key") == cache_key and 
        _chainlink_price_cache.get("price") is not None):
        return _chainlink_price_cache["price"], None
    
    # Get fresh Chainlink price and cache it
    price, err = get_chainlink_price(asset=asset)
    if err is None and price is not None:
        _chainlink_price_cache["window_key"] = cache_key
        _chainlink_price_cache["price"] = price
    
    return price, err


def _get_web3():
    """
    Get or create a Web3 instance connected to Ethereum mainnet via Infura.
    Cached for reuse to avoid creating new connections for each call.
    """
    global _web3_instance
    if _web3_instance is None:
        _web3_instance = Web3(Web3.HTTPProvider(INFURA_URL))
    return _web3_instance


def get_chainlink_price(asset="btc"):
    """
    Get the current price from Chainlink price feed.
    """
    try:
        w3 = _get_web3()
        
        if not w3.is_connected():
            return None, "Failed to connect to Ethereum via Infura"
        
        proxy_map = {
            "btc": CHAINLINK_BTC_USD_PROXY,
            "eth": CHAINLINK_ETH_USD_PROXY,
            "sol": CHAINLINK_SOL_USD_PROXY
        }
        proxy_address = proxy_map.get(asset.lower())
        if not proxy_address:
            return None, f"No Chainlink proxy configured for {asset}"
        
        # Create contract instance
        contract = w3.eth.contract(
            address=proxy_address,
            abi=CHAINLINK_ABI
        )
        
        # Get latest round data
        round_data = contract.functions.latestRoundData().call()
        answer = round_data[1]
        decimals = contract.functions.decimals().call()
        price = float(answer) / (10 ** decimals)
        
        return round(price, 2), None
        
    except Exception as e:
        return None, f"Chainlink price fetch error: {str(e)}"


# Cache for window open price (PTB) fallback
_window_open_price_cache = {
    "target_time": None,
    "price": None
}

# Cache for Gamma PTB
_gamma_ptb_cache = {
    "slug": None,
    "price": None
}

def get_polymarket_ptb(slug):
    """
    Fetch the exact priceToBeat from Polymarket Gamma API eventMetadata.
    This is the definitive 'Price to Beat' shown on the website.
    """
    global _gamma_ptb_cache
    
    # Check cache first
    if _gamma_ptb_cache["slug"] == slug and _gamma_ptb_cache["price"] is not None:
        return _gamma_ptb_cache["price"], None

    # Fetch from Gamma API
    data, err = fetch_with_retry("https://gamma-api.polymarket.com/events", params={"slug": slug})
    if err or not data:
        return None, f"Polymarket PTB error: {err or 'no data'}"
    
    try:
        event = data[0]
        metadata = event.get("eventMetadata", {})
        ptb = metadata.get("priceToBeat")
        if ptb is not None:
            price = round(float(ptb), 2)
            # Update cache
            _gamma_ptb_cache["slug"] = slug
            _gamma_ptb_cache["price"] = price
            return price, None
        return None, f"priceToBeat not found in metadata for {slug}"
    except (IndexError, KeyError, ValueError, TypeError) as e:
        return None, f"Metadata parse error: {e}"


def get_window_open_price(current_window_utc, asset="btc"):
    """
    Get the OPEN price of the current 15m Binance candle.
    """
    global _window_open_price_cache
    
    asset_map = {"btc": "BTCUSDT", "eth": "ETHUSDT", "sol": "SOLUSDT", "xrp": "XRPUSDT"}
    symbol = asset_map.get(asset.lower(), "BTCUSDT")
    cache_key = f"{symbol}_{current_window_utc}"
    
    # Check cache first
    if (_window_open_price_cache.get("window_key") == cache_key and 
        _window_open_price_cache.get("price") is not None):
        return _window_open_price_cache["price"], None

    try:
        # Get the timestamp of the current window start
        timestamp_ms = int(current_window_utc.timestamp() * 1000)

        params = {
            "symbol": symbol,
            "interval": "15m",
            "startTime": timestamp_ms,
            "limit": 1,
        }
        data, err = fetch_with_retry(BINANCE_KLINES_URL, params=params)
        if err:
            return None, f"Binance kline error: {err}"
        if not data:
            return None, "Current candle not found"

        # Kline format: [open_time, OPEN, high, low, close, volume, close_time, ...]
        # Index 1 is the OPEN price
        open_price = float(data[0][1])
        
        # Update cache
        _window_open_price_cache["window_key"] = cache_key
        _window_open_price_cache["price"] = round(open_price, 2)
        
        return _window_open_price_cache["price"], None
    except Exception as e:
        return None, str(e)


def get_coinbase_historical_price(target_time_utc, asset="btc"):
    """
    Get the price from Coinbase at a specific historical timestamp.
    """
    try:
        asset_map = {"btc": "BTC-USD", "eth": "ETH-USD", "sol": "SOL-USD", "xrp": "XRP-USD"}
        product_id = asset_map.get(asset.lower(), "BTC-USD")
        # Granularity 60 = 1 minute
        start_iso = target_time_utc.isoformat()
        end_iso = (target_time_utc + datetime.timedelta(minutes=1)).isoformat()
        
        params = {
            "start": start_iso,
            "end": end_iso,
            "granularity": 60
        }
        data, err = fetch_with_retry(f"https://api.exchange.coinbase.com/products/{product_id}/candles", params=params)
        if err or not data:
            return None, f"Coinbase historical error: {err or 'no data'}"
        
        # Format: [time, low, high, open, close, volume]
        # data[0] is the most recent (which should be our minute)
        # Index 3 is OPEN price
        return float(data[0][3]), None
    except Exception as e:
        return None, str(e)


def fetch_polymarket_data_struct(asset="btc"):
    """
    Fetches current 15m Polymarket market data and returns a structured dictionary.
    """
    try:
        market_info = get_current_market_urls(asset=asset)
        polymarket_slug = market_info["polymarket_slug"]
        target_time_utc = market_info["target_time_utc"]  # current window start

        # Parallelize independent network requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            poly_future = executor.submit(get_polymarket_data, polymarket_slug)
            ptb_future = executor.submit(get_polymarket_ptb, polymarket_slug)
            current_future = executor.submit(get_coinbase_current_price, asset=asset)
            
            poly_prices, poly_err = poly_future.result()
            if poly_err:
                return None, f"Polymarket Error: {poly_err}"

            price_to_beat, ptb_err = ptb_future.result()
            if ptb_err:
                # Fallback: Get historical Coinbase price at window start
                price_to_beat, ptb_err = get_coinbase_historical_price(target_time_utc, asset=asset)
                if ptb_err:
                    # Final fallback to Binance open price
                    price_to_beat, ptb_err = get_window_open_price(target_time_utc, asset=asset)
                    if ptb_err:
                        return None, f"Price to Beat Error (Polymarket & Binance): {ptb_err}"

            current_price, current_err = current_future.result()
            if current_err:
                # Fallback to Binance
                current_price, current_err = get_binance_current_price(asset=asset)
                if current_err:
                    return None, f"Current Price Error (Coinbase & Binance): {current_err}"

        return {
            "price_to_beat": price_to_beat,
            "current_price": current_price,
            "prices": poly_prices,
            "slug": polymarket_slug,
            "target_time_utc": target_time_utc,
            "asset": asset.upper()
        }, None

    except Exception as e:
        return None, str(e)

    except Exception as e:
        return None, str(e)


def main():
    while True:
        data, err = fetch_polymarket_data_struct()
        if err:
            print(f"Error: {err}")
        else:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}]")
            print(f"  Slug: {data['slug']}")
            print(f"  Price to Beat: ${data['price_to_beat']:,.2f}" if data['price_to_beat'] else "  Price to Beat: N/A")
            print(f"  Current Price: ${data['current_price']:,.2f}" if data.get('current_price') else "  Current Price: N/A")
            print(f"  Up: {data['prices'].get('Up', 0):.3f} / Down: {data['prices'].get('Down', 0):.3f}")
        time.sleep(2)

if __name__ == "__main__":
    main()
