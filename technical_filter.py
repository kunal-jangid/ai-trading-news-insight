import pandas as pd

class TechnicalFilter:
    def __init__(self, exchange: str = "NSE", screener: str = "india"):
        self.exchange = exchange
        self.screener = screener

    def filter_strong_signals(self, df: pd.DataFrame) -> list[dict]:
        """
        Takes a DataFrame from tradingview-screener containing Recommend.All columns.
        Returns a list of dictionaries containing info for those with Strong Buy or Strong Sell ratings.
        Recommend.All roughly maps: [-1 to -0.5: Strong Sell, -0.5 to 0: Sell, 0: Neutral, 0 to +0.5: Buy, +0.5 to +1: Strong Buy]
        """
        if df is None or df.empty:
            return []
            
        print(f"Filtering {len(df)} stocks for Strong Buy/Sell daily ratings natively...")
        survivors = []
        
        for _, row in df.iterrows():
            ticker = row['ticker']
            rating_val = row.get('Recommend.All', 0)
            
            # Determine strict signal bounds
            if rating_val >= 0.1:  # Buy or Strong Buy threshold
                signal_type = 'BULLISH'
                rec_text = 'BUY' if rating_val < 0.5 else 'STRONG_BUY'
            elif rating_val <= -0.1: # Sell or Strong Sell threshold
                signal_type = 'BEARISH'
                rec_text = 'SELL' if rating_val > -0.5 else 'STRONG_SELL'
            else:
                continue # Skip neutral
                
            # Reconstruct the expected dictionary for analyzer.py compatibility
            survivors.append({
                'ticker': ticker,
                'signal_type': signal_type,
                'indicators': {
                    'close': row.get('close', 'N/A'),
                    'RSI': row.get('RSI', 'N/A'),
                    'MACD.macd': row.get('MACD.macd', 'N/A'),
                    'SMA20': row.get('SMA20', 'N/A'),
                    'BBUpper': row.get('BB.upper', 'N/A'),
                    'BBLower': row.get('BB.lower', 'N/A')
                },
                'summary': {
                    'RECOMMENDATION': rec_text
                }
            })
            
        print(f"Surviving bullish/bearish stocks: {len(survivors)}")
        return survivors
                
                
        print(f"Surviving bullish/bearish stocks: {len(survivors)}")
        return survivors
