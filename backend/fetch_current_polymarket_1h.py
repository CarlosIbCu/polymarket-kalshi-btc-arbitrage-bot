import requests
import time
import datetime
import json
import pytz
from get_current_markets_1h import get_current_market_urls
from web3 import Web3
import concurrent.futures

POLYMARKET_API_URL = "https://gamma-api.polymarket.com/events"
BINANCE_PRICE_URL = "https://api.binance.com/api/v3/ticker/price"
BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
# Chainlink Price Feeds on Ethereum Mainnet
CHAINLINK_BTC_USD_PROXY = "0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c"
CHAINLINK_ETH_USD_PROXY = "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419"

# Chainlink AggregatorV3Interface ABI
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

MAX_RETRIES = 3
TIMEOUT = 5

def fetch_with_retry(url, params=None, max_retries=MAX_RETRIES, timeout=TIMEOUT):
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

_token_id_cache: dict[str, list[str]] = {}


def _get_clob_token_ids(slug: str) -> list[str]:
    """Return [up_token_id, ...] for a slug, cached per slug."""
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
    """Fetch the current mid-price for one token from the CLOB /midpoint endpoint."""
    data, err = fetch_with_retry(f"{CLOB_API_URL}/midpoint", params={"token_id": token_id})
    if err or not data:
        return None
    mid = data.get("mid")
    return float(mid) if mid is not None else None


def get_polymarket_data(slug):
    """
    Fetch the Up/Down BUY prices for a 1h Polymarket BTC market by slug.

    Two-tier approach:
      1. gamma API      → clobTokenIds (cached per slug)
      2. CLOB /midpoint → live mid-price for each token

    Up price   = midpoint of Up token
    Down price = midpoint of Down token
    Falls back to gamma outcomePrices if CLOB unavailable.
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

    return {"Up": round(up_buy_price, 4), "Down": round(down_buy_price, 4)}, None







def get_binance_current_price(asset="btc"):
    asset_map = {"btc": "BTCUSDT", "eth": "ETHUSDT", "sol": "SOLUSDT", "xrp": "XRPUSDT"}
    symbol = asset_map.get(asset.lower(), "BTCUSDT")
    data, err = fetch_with_retry(BINANCE_PRICE_URL, params={"symbol": symbol})
    if err:
        return None, f"Binance price error: {err}"
    try:
        return float(data["price"]), None
    except (KeyError, TypeError) as e:
        return None, f"Parse error: {e}"

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
            "sol": "0x4ffc43a60ed71866380a96f13b6329c488ce9f01507" # SOL/USD Proxy
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


# Cache for window open price (PTB)
_window_open_price_cache = {
    "target_time": None,
    "price": None
}

def get_window_open_price(current_window_utc, asset="btc"):
    """
    Get the OPEN price of the current 1h Binance candle.
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
            "interval": "1h",
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


def fetch_polymarket_data_struct(asset="btc"):
    """
    Fetches current 1h Polymarket market data.
    """
    try:
        market_info = get_current_market_urls(asset=asset)
        polymarket_slug = market_info["polymarket_slug"]
        target_time_utc = market_info["target_time_utc"]

        # Parallelize independent network requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            poly_future = executor.submit(get_polymarket_data, polymarket_slug)
            ptb_future = executor.submit(get_window_open_price, target_time_utc, asset=asset)
            current_future = executor.submit(get_binance_current_price, asset=asset)
            
            poly_prices, poly_err = poly_future.result()
            if poly_err:
                return None, f"Polymarket Error: {poly_err}"

            price_to_beat, ptb_err = ptb_future.result()
            if ptb_err:
                return None, f"Price to Beat Error: {ptb_err}"

            current_price, current_err = current_future.result()
            if current_err:
                return None, f"Binance Current Price Error: {current_err}"

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


if __name__ == "__main__":
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
