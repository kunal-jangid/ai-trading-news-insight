import requests
import pandas as pd
import json

class PolymarketFetcher:
    def __init__(self, base_url: str = "https://gamma-api.polymarket.com/events"):
        self.base_url = base_url

    def get_live_odds(self, keywords: list = None, limit: int = 100) -> pd.DataFrame:
        """
        Fetches active markets and returns a DataFrame filtered by keywords.
        """
        if keywords is None:
            keywords = ["india", "modi", "rbi", "war", "china", "oil", "rate"]
            
        params = {"limit": limit, "active": "true", "closed": "false"}
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            events = response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error fetching Polymarket data: {e}")
            return pd.DataFrame()

        data = []
        for event in events:
            title = event.get("title", "")
            
            if any(kw in title.lower() for kw in keywords):
                markets = event.get("markets", [])
                
                for market in markets:
                    question = market.get("question", "N/A")
                    volume = float(market.get("volume", 0))
                    
                    raw_outcomes = market.get("outcomes", "[]")
                    raw_prices = market.get("outcomePrices", "[]")
                    
                    try:
                        outcomes = json.loads(raw_outcomes) if isinstance(raw_outcomes, str) else raw_outcomes
                        prices = json.loads(raw_prices) if isinstance(raw_prices, str) else raw_prices
                    except json.JSONDecodeError:
                        continue
                    
                    if isinstance(outcomes, list) and isinstance(prices, list) and len(outcomes) == len(prices) and len(outcomes) > 0:
                        odds_summary = []
                        for i in range(len(outcomes)):
                            try:
                                prob = float(prices[i]) * 100 
                                odds_summary.append(f"{outcomes[i]}: {prob:.1f}%")
                            except (ValueError, TypeError):
                                odds_summary.append(f"{outcomes[i]}: N/A")
                                
                        formatted_odds = " | ".join(odds_summary)
                        
                        data.append({
                            "Market Question": question,
                            "Current Odds": formatted_odds,
                            "Liquidity (USD)": volume
                        })
                
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values(by="Liquidity (USD)", ascending=False).reset_index(drop=True)
            
        return df