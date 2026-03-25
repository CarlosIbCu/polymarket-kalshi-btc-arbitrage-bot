import datetime

def get_current_market_urls():
    """
    Automatically generates market configuration for TODAY (Dec 30).
    """
    # 1. Get Today's Date (UTC)
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # 2. Format for Polymarket (e.g., "december-30")
    month_str = now.strftime("%B").lower() 
    day_str = now.strftime("%d").lstrip("0") 
    
    # Slug: "bitcoin-up-or-down-on-december-30"
    poly_slug = f"bitcoin-up-or-down-on-{month_str}-{day_str}"
    
    # Query fallback
    poly_query = f"Bitcoin Up or Down on {now.strftime('%B')} {day_str}"

    # 3. Format for Kalshi (YYMMMDD -> 25DEC30)
    kalshi_date_str = now.strftime("%y%b%d").upper()

    # 4. Target Time (Yesterday Noon ET = Open Price)
    # We use a rough estimate for the candle lookup; the bot will refine this.
    target_time = now.replace(hour=17, minute=0, second=0, microsecond=0) - datetime.timedelta(days=1)

    return {
        "polymarket_slug": poly_slug,
        "polymarket_query": poly_query,
        "target_time_utc": target_time,
        "kalshi_date_string": kalshi_date_str
    }