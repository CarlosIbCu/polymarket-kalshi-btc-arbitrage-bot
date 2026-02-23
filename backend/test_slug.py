import datetime
import pytz
from find_new_market import generate_slug, get_current_15min_window

def test():
    now = datetime.datetime.now(pytz.utc)
    print(f"Current UTC: {now}")
    
    window = get_current_15min_window(now)
    print(f"Window Start: {window}")
    
    slug = generate_slug(window)
    print(f"Slug:         {slug}")
    
    ts = int(window.timestamp())
    print(f"Timestamp:    {ts}")
    # 1771595400 ?
    target = 1771595400
    if ts == target:
        print("MATCHES output from earlier!")
    else:
        print(f"Difference: {ts - target} seconds")

if __name__ == "__main__":
    test()
