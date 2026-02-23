import requests
import datetime
import pytz

def check_range():
    base = int(datetime.datetime(2026, 2, 20, 14, 0, tzinfo=datetime.timezone.utc).timestamp())
    # Check every 5 minutes from 13:30 to 14:45
    for offset in range(-30, 60, 5):
        ts = base + (offset * 60)
        slug = f"btc-updown-15m-{ts}"
        url = f"https://gamma-api.polymarket.com/events?slug={slug}"
        r = requests.get(url)
        data = r.json()
        if data:
            event = data[0]
            m = event.get('markets', [{}])[0]
            print(f"FOUND: {slug} | Active: {m.get('active')} | Ends: {m.get('end_date_iso')}")
        else:
            pass # print(f"NOT FOUND: {slug}")

if __name__ == "__main__":
    check_range()
