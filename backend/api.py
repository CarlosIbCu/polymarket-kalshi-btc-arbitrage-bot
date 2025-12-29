from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fetch_current_polymarket import fetch_polymarket_data_struct
from fetch_current_kalshi import fetch_kalshi_data_struct
from blockrun_analyzer import (
    analyze_arbitrage_opportunity,
    get_market_sentiment,
    list_available_models,
    is_blockrun_enabled,
)
import datetime

app = FastAPI(
    title="Polymarket-Kalshi Arbitrage API",
    description="Real-time arbitrage detection with optional AI analysis via BlockRun",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/arbitrage")
def get_arbitrage_data(
    include_ai: bool = Query(False, description="Include AI analysis via BlockRun"),
    model: str = Query("gpt-4o-mini", description="AI model to use for analysis"),
):
    # Fetch Data
    poly_data, poly_err = fetch_polymarket_data_struct()
    kalshi_data, kalshi_err = fetch_kalshi_data_struct()
    
    response = {
        "timestamp": datetime.datetime.now().isoformat(),
        "polymarket": poly_data,
        "kalshi": kalshi_data,
        "checks": [],
        "opportunities": [],
        "errors": [],
        "ai_analysis": None,
        "ai_enabled": is_blockrun_enabled(),
    }
    
    if poly_err:
        response["errors"].append(poly_err)
    if kalshi_err:
        response["errors"].append(kalshi_err)
        
    if not poly_data or not kalshi_data:
        return response

    # Logic
    poly_strike = poly_data['price_to_beat']
    poly_up_cost = poly_data['prices'].get('Up', 0.0)
    poly_down_cost = poly_data['prices'].get('Down', 0.0)
    
    if poly_strike is None:
        response["errors"].append("Polymarket Strike is None")
        return response

    kalshi_markets = kalshi_data.get('markets', [])
    
    # Ensure sorted by strike
    kalshi_markets.sort(key=lambda x: x['strike'])
    
    # Find index closest to poly_strike
    closest_idx = 0
    min_diff = float('inf')
    for i, m in enumerate(kalshi_markets):
        diff = abs(m['strike'] - poly_strike)
        if diff < min_diff:
            min_diff = diff
            closest_idx = i
            
    # Select 4 below and 4 above (approx 8-9 markets total)
    # If closest is at index C, we want [C-4, C+5] roughly
    start_idx = max(0, closest_idx - 4)
    end_idx = min(len(kalshi_markets), closest_idx + 5) # +5 to include the closest and 4 above
    
    selected_markets = kalshi_markets[start_idx:end_idx]
    
    for km in selected_markets:
        kalshi_strike = km['strike']
        kalshi_yes_cost = km['yes_ask'] / 100.0
        kalshi_no_cost = km['no_ask'] / 100.0
        
        # Only check markets within range (removed previous hardcoded range check)
            
        check_data = {
            "kalshi_strike": kalshi_strike,
            "kalshi_yes": kalshi_yes_cost,
            "kalshi_no": kalshi_no_cost,
            "type": "",
            "poly_leg": "",
            "kalshi_leg": "",
            "poly_cost": 0,
            "kalshi_cost": 0,
            "total_cost": 0,
            "is_arbitrage": False,
            "margin": 0
        }

        if poly_strike > kalshi_strike:
            check_data["type"] = "Poly > Kalshi"
            check_data["poly_leg"] = "Down"
            check_data["kalshi_leg"] = "Yes"
            check_data["poly_cost"] = poly_down_cost
            check_data["kalshi_cost"] = kalshi_yes_cost
            check_data["total_cost"] = poly_down_cost + kalshi_yes_cost
            
        elif poly_strike < kalshi_strike:
            check_data["type"] = "Poly < Kalshi"
            check_data["poly_leg"] = "Up"
            check_data["kalshi_leg"] = "No"
            check_data["poly_cost"] = poly_up_cost
            check_data["kalshi_cost"] = kalshi_no_cost
            check_data["total_cost"] = poly_up_cost + kalshi_no_cost
            
        elif poly_strike == kalshi_strike:
            # Check 1
            check1 = check_data.copy()
            check1["type"] = "Equal"
            check1["poly_leg"] = "Down"
            check1["kalshi_leg"] = "Yes"
            check1["poly_cost"] = poly_down_cost
            check1["kalshi_cost"] = kalshi_yes_cost
            check1["total_cost"] = poly_down_cost + kalshi_yes_cost
            
            if check1["total_cost"] < 1.00:
                check1["is_arbitrage"] = True
                check1["margin"] = 1.00 - check1["total_cost"]
                response["opportunities"].append(check1)
            response["checks"].append(check1)
            
            # Check 2
            check2 = check_data.copy()
            check2["type"] = "Equal"
            check2["poly_leg"] = "Up"
            check2["kalshi_leg"] = "No"
            check2["poly_cost"] = poly_up_cost
            check2["kalshi_cost"] = kalshi_no_cost
            check2["total_cost"] = poly_up_cost + kalshi_no_cost
            
            if check2["total_cost"] < 1.00:
                check2["is_arbitrage"] = True
                check2["margin"] = 1.00 - check2["total_cost"]
                response["opportunities"].append(check2)
            response["checks"].append(check2)
            continue # Skip adding the base check_data

        if check_data["total_cost"] < 1.00:
            check_data["is_arbitrage"] = True
            check_data["margin"] = 1.00 - check_data["total_cost"]
            response["opportunities"].append(check_data)
            
        response["checks"].append(check_data)

    # Add AI analysis if requested
    if include_ai and is_blockrun_enabled():
        response["ai_analysis"] = analyze_arbitrage_opportunity(
            poly_data, kalshi_data, response["opportunities"], model
        )

    return response


@app.get("/ai/analyze")
def analyze_current_opportunities(
    model: str = Query("gpt-4o-mini", description="AI model to use"),
):
    """
    Get AI analysis of current arbitrage opportunities using BlockRun.

    Requires BLOCKRUN_ENABLED=true in environment.
    Your wallet pays for LLM calls with USDC via x402 protocol.
    """
    if not is_blockrun_enabled():
        return {
            "status": "disabled",
            "message": "Set BLOCKRUN_ENABLED=true to enable AI analysis",
            "docs": "https://blockrun.ai",
        }

    # Fetch current data
    poly_data, _ = fetch_polymarket_data_struct()
    kalshi_data, _ = fetch_kalshi_data_struct()

    # Get opportunities (simplified check)
    opportunities = []
    if poly_data and kalshi_data:
        poly_strike = poly_data.get('price_to_beat', 0)
        poly_up = poly_data.get('prices', {}).get('Up', 0)
        poly_down = poly_data.get('prices', {}).get('Down', 0)

        for km in kalshi_data.get('markets', [])[:5]:
            kalshi_strike = km['strike']
            kalshi_yes = km['yes_ask'] / 100.0
            kalshi_no = km['no_ask'] / 100.0

            if poly_strike > kalshi_strike:
                total = poly_down + kalshi_yes
                if total < 1.0:
                    opportunities.append({
                        "type": "Poly > Kalshi",
                        "poly_leg": "Down", "kalshi_leg": "Yes",
                        "poly_cost": poly_down, "kalshi_cost": kalshi_yes,
                        "total_cost": total, "margin": 1.0 - total
                    })
            elif poly_strike < kalshi_strike:
                total = poly_up + kalshi_no
                if total < 1.0:
                    opportunities.append({
                        "type": "Poly < Kalshi",
                        "poly_leg": "Up", "kalshi_leg": "No",
                        "poly_cost": poly_up, "kalshi_cost": kalshi_no,
                        "total_cost": total, "margin": 1.0 - total
                    })

    return analyze_arbitrage_opportunity(poly_data, kalshi_data, opportunities, model)


@app.get("/ai/sentiment")
def get_btc_sentiment(
    model: str = Query("gpt-4o-mini", description="AI model to use"),
):
    """Get AI-powered BTC market sentiment analysis."""
    if not is_blockrun_enabled():
        return {
            "status": "disabled",
            "message": "Set BLOCKRUN_ENABLED=true to enable AI analysis",
        }
    return get_market_sentiment(model)


@app.get("/ai/models")
def get_available_models():
    """List available AI models via BlockRun."""
    return {
        "enabled": is_blockrun_enabled(),
        "models": list_available_models(),
        "docs": "https://blockrun.ai",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
