import requests
import datetime

def get_historical_binance(timestamp_ms):
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "BTCUSDT",
        "interval": "1m",
        "startTime": timestamp_ms,
        "limit": 1
    }
    r = requests.get(url, params=params)
    if r.status_code == 200:
        data = r.json()
        if data:
            return float(data[0][1]) # Open price
    return None

def get_historical_coinbase(timestamp):
    # Coinbase API uses ISO strings or Unix timestamps
    # For historical candles: /products/{product_id}/candles
    url = f"https://api.exchange.coinbase.com/products/BTC-USD/candles"
    dt = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)
    params = {
        "start": dt.isoformat(),
        "end": (dt + datetime.timedelta(minutes=1)).isoformat(),
        "granularity": 60
    }
    r = requests.get(url, params=params)
    if r.status_code == 200:
        data = r.json()
        if data:
            # Format: [time, low, high, open, close, volume]
            return float(data[0][3]) # Open price
    return None

if __name__ == "__main__":
    ts = 1771640100 # Feb 21, 02:15 UTC
    ts_ms = ts * 1000
    
    bn_price = get_historical_binance(ts_ms)
    cb_price = get_historical_coinbase(ts)
    
    print(f"Timestamp: {ts} (Feb 21, 02:15 UTC)")
    print(f"Binance 1m Open:  {bn_price}")
    print(f"Coinbase 1m Open: {cb_price}")
    # User screenshot Web PTB: 67,984.45
    # App Screenshot PTB: 67,989.01
    print(f"Web Screenshot PTB: 67984.45")
