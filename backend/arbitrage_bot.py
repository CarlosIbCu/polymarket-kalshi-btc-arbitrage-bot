import time
import datetime
from fetch_current_polymarket import fetch_polymarket_data_struct
from fetch_current_kalshi import fetch_kalshi_data_struct
from executor import TradeExecutor

def check_arbitrage(executor):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Scanning for arbitrage...")
    
    # Fetch Data
    poly_data, poly_err = fetch_polymarket_data_struct()
    kalshi_data, kalshi_err = fetch_kalshi_data_struct()
    
    if poly_err:
        print(f"Polymarket Error: {poly_err}")
        return
    if kalshi_err:
        print(f"Kalshi Error: {kalshi_err}")
        return
        
    if not poly_data: # or not kalshi_data:
        print("Missing data.")
        return

    if not kalshi_data:
        print("Missing Kalshi data.")
        return

    # Polymarket Data
    poly_strike = poly_data['price_to_beat']
    
    # SAFETY CHECK
    if poly_strike is None or poly_strike <= 1000:
        print(f"⚠️  Polymarket Strike Invalid ({poly_strike}). Skipping Arb Check.")
        print(f"    (Market: {poly_data.get('question')})")
        return
        
    poly_up_cost = poly_data['prices'].get('Up', 0.0)
    poly_down_cost = poly_data['prices'].get('Down', 0.0)



    # We need the specific Asset IDs to trade
    poly_up_id = poly_data.get('up_token_id') 
    poly_down_id = poly_data.get('down_token_id')
    # ----------------------
    
    if poly_strike is None:
        print("Polymarket Strike is None")
        return

    print(f"POLYMARKET | Strike: ${poly_strike:,.2f} | Up: ${poly_up_cost:.3f} | Down: ${poly_down_cost:.3f}")

    # Kalshi Data
    kalshi_markets = kalshi_data['markets']
    if not kalshi_markets:
        print("No Kalshi markets found")
        return
        
    # Find relevant Kalshi markets (closest to Poly strike)
    # We can check ALL of them, but let's focus on the ones around the Poly strike
    # Actually, the user asked to compare Poly Strike vs Kalshi Strike 1, 2, 3.
    # But "1, 2, 3" depends on which ones we fetched. 
    # Let's iterate through ALL fetched Kalshi markets and check for arb.
    
    found_arb = False
    
    # Print header for Kalshi
    # print("KALSHI MARKETS:")
    
    for km in kalshi_markets:
        kalshi_strike = km['strike']
        # Kalshi prices are in cents (integer), convert to dollars
        kalshi_yes_cost = km['yes_ask'] / 100.0
        kalshi_no_cost = km['no_ask'] / 100.0
        
        # Only print markets close to Poly strike to avoid spamming?
        # Or print all? User said "show the data it is using".
        # Let's print the ones within a reasonable range (e.g. +/- $2500)
        if abs(kalshi_strike - poly_strike) < 2500:
             print(f"  KALSHI | Strike: ${kalshi_strike:,.2f} | Yes: ${kalshi_yes_cost:.2f} | No: ${kalshi_no_cost:.2f}")
        
        # Logic:
        
        # Logic:
        # Polymarket "Up" means Price >= Poly_Strike
        # Polymarket "Down" means Price < Poly_Strike
        
        # Kalshi "Yes" means Price >= Kalshi_Strike
        # Kalshi "No" means Price < Kalshi_Strike
        
        # Case 1: Poly_Strike > Kalshi_Strike
        # Range: [Kalshi_Strike, Poly_Strike)
        # If Price is in this range:
        #   - Poly is Down (Win)
        #   - Kalshi is Yes (Win)
        # Strategy: Buy Poly Down + Kalshi Yes
        # If Price < Kalshi_Strike: Poly Down (Win), Kalshi Yes (Lose) -> 1 Win
        # If Price >= Poly_Strike: Poly Down (Lose), Kalshi Yes (Win) -> 1 Win
        # If Kalshi_Strike <= Price < Poly_Strike: Both Win -> 2 Wins
        # So MINIMUM payout is $1.00.
        # Risk Free if Cost(Poly Down) + Cost(Kalshi Yes) < 1.00
        
        if poly_strike > kalshi_strike:
            total_cost = poly_down_cost + kalshi_yes_cost
            print(f"    [Poly > Kalshi] Checking: Poly Down (${poly_down_cost:.3f}) + Kalshi Yes (${kalshi_yes_cost:.3f}) = ${total_cost:.3f}")
            
            if total_cost < 1.00:
                margin = 1.00 - total_cost
                print(f"!!! ARBITRAGE FOUND !!!")
                print(f"Type: Poly Strike ({poly_strike}) > Kalshi Strike ({kalshi_strike})")
                print(f"Strategy: Buy Poly DOWN + Kalshi YES")
                print(f"Total Cost: ${total_cost:.3f}")
                print(f"Min Payout: $1.00")
                print(f"Risk-Free Profit: ${margin:.3f} per unit")

                # --- INSERT THIS ---
                print("⚡ Triggering Trade...")
                executor.execute_trade({
                    'poly_token_id': poly_down_id,
                    'poly_price': poly_down_cost,
                    'kalshi_ticker': km.get('ticker', km.get('market_ticker')),
                    'kalshi_price': kalshi_yes_cost,
                    'kalshi_side': 'yes'
                })
                # -------------------
                found_arb = True

        # Case 2: Poly_Strike < Kalshi_Strike
        elif poly_strike < kalshi_strike:
            total_cost = poly_up_cost + kalshi_no_cost
            print(f"    [Poly < Kalshi] Checking: Poly Up (${poly_up_cost:.3f}) + Kalshi No (${kalshi_no_cost:.3f}) = ${total_cost:.3f}")
            
            if total_cost < 1.00:
                margin = 1.00 - total_cost
                print(f"!!! ARBITRAGE FOUND !!!")
                print(f"Type: Poly Strike ({poly_strike}) < Kalshi Strike ({kalshi_strike})")
                print(f"Strategy: Buy Poly UP + Kalshi NO")
                print(f"Total Cost: ${total_cost:.3f}")
                print(f"Min Payout: $1.00")
                print(f"Risk-Free Profit: ${margin:.3f} per unit")

                # --- INSERT THIS ---
                print("⚡ Triggering Trade...")
                executor.execute_trade({
                    'poly_token_id': poly_up_id,
                    'poly_price': poly_up_cost,
                    'kalshi_ticker': km.get('ticker', km.get('market_ticker')),
                    'kalshi_price': kalshi_no_cost,
                    'kalshi_side': 'no'
                })
                # -------------------
                found_arb = True
                
        # Case 3: Poly_Strike == Kalshi_Strike
        elif poly_strike == kalshi_strike:
            # Check Pair 1: Poly Down + Kalshi Yes
            cost1 = poly_down_cost + kalshi_yes_cost
            print(f"    [Poly == Kalshi] Checking: Poly Down (${poly_down_cost:.3f}) + Kalshi Yes (${kalshi_yes_cost:.3f}) = ${cost1:.3f}")
            
            if cost1 < 1.00:
                margin = 1.00 - cost1
                print(f"!!! ARBITRAGE FOUND !!!")
                print(f"Type: Equal Strikes ({poly_strike})")
                print(f"Strategy: Buy Poly DOWN + Kalshi YES")
                print(f"Total Cost: ${cost1:.3f}")
                print(f"Risk-Free Profit: ${margin:.3f} per unit")
                 # --- INSERT THIS ---
                print("⚡ Triggering Trade...")
                executor.execute_trade({
                    'poly_token_id': poly_down_id,
                    'poly_price': poly_down_cost,
                    'kalshi_ticker': km.get('ticker', km.get('market_ticker')),
                    'kalshi_price': kalshi_yes_cost,
                    'kalshi_side': 'yes'
                })
                # -------------------
                found_arb = True
                
            # Check Pair 2: Poly Up + Kalshi No
            cost2 = poly_up_cost + kalshi_no_cost
            print(f"    [Poly == Kalshi] Checking: Poly Up (${poly_up_cost:.3f}) + Kalshi No (${kalshi_no_cost:.3f}) = ${cost2:.3f}")
            
            if cost2 < 1.00:
                margin = 1.00 - cost2
                print(f"!!! ARBITRAGE FOUND !!!")
                print(f"Type: Equal Strikes ({poly_strike})")
                print(f"Strategy: Buy Poly UP + Kalshi NO")
                print(f"Total Cost: ${cost2:.3f}")
                print(f"Risk-Free Profit: ${margin:.3f} per unit")
                # --- INSERT THIS ---
                print("⚡ Triggering Trade...")
                executor.execute_trade({
                    'poly_token_id': poly_up_id,
                    'poly_price': poly_up_cost,
                    'kalshi_ticker': km.get('ticker', km.get('market_ticker')),
                    'kalshi_price': kalshi_no_cost,
                    'kalshi_side': 'no'
                })
                # -------------------
                found_arb = True

    if not found_arb:
        print("No risk-free arbitrage found.")
    print("-" * 50)

def main():
    print("Starting Arbitrage Bot...")
    print("Press Ctrl+C to stop.")
    # 1. Initialize Executor
    print("\n--- 🔌 INITIALIZING TRADER ---")
    try:
        executor = TradeExecutor()
        executor.login_kalshi() 
    except Exception as e:
        print(f"❌ CRITICAL ERROR: Could not start executor: {e}")
        return

    # 2. STATUS CHECK (Diagnose the "Not Ready" error)
    print("\n--- 🔍 CONNECTION STATUS ---")
    
    # Check Polymarket
    if executor.is_ready_poly:
        print("✅ Polymarket: CONNECTED")
    else:
        print("❌ Polymarket: FAILED")
        print("   (Reason: Check the '⚠️ Executor Warning' logs above)")

    # Check Kalshi
    if executor.is_ready_kalshi:
        print("✅ Kalshi: CONNECTED")
    else:
        print("❌ Kalshi: FAILED")
        print("   (Reason: Check the 'Kalshi Key Error' logs above)")

    if not executor.is_ready:
        print("\n⚠️  WARNING: The bot will SCAN, but it CANNOT TRADE.")
        print("   Fix the failed connection in .env to enable trading.")
    else:
        print("\n🚀 SYSTEM READY: Auto-Trading is ACTIVE.")
    print("----------------------------\n")
    while True:
        try:
            check_arbitrage(executor)
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)



if __name__ == "__main__":
    main()