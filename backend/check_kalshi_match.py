import requests
import datetime

def check_candles():
    start_ts = int(datetime.datetime(2026, 2, 20, 14, 10, tzinfo=datetime.timezone.utc).timestamp() * 1000)
    params = {
        'symbol': 'BTCUSDT',
        'interval': '1m',
        'startTime': start_ts,
        'limit': 30
    }
    r = requests.get('https://api.binance.com/api/v3/klines', params=params)
    data = r.json()
    
    target_kalshi = 66895.28
    print(f"Target PTB from Kalshi: ${target_kalshi}")
    print("-" * 30)
    for k in data:
        ts = datetime.datetime.fromtimestamp(k[0]/1000, datetime.timezone.utc).strftime("%H:%M")
        o = float(k[1])
        c = float(k[4])
        print(f"{ts} | Open: {o} | Close: {c}")
        if abs(o - target_kalshi) < 2 or abs(c - target_kalshi) < 2:
            print(f"  *** POTENTIAL MATCH at {ts} ***")

if __name__ == "__main__":
    check_candles()
