from tradingview_screener import Query, Column

class ScreenerFetcher:
    def __init__(self, min_market_cap: float = 500_0000000, max_market_cap: float = 50_000000000):
        # 500 Cr = 5,000,000,000 INR
        # 5,000 Cr = 50,000,000,000 INR
        self.min_market_cap = min_market_cap
        self.max_market_cap = max_market_cap

    def get_small_mid_caps(self, sectors: list[str]):
        """
        Fetches small and mid cap Indian stocks belonging to the given sectors.
        Returns a pandas DataFrame containing tickers and technical indicators.
        """
        print(f"Screening for small/mid caps in sectors: {sectors}")
        
        q = (Query()
             .set_markets('india')
             .select(
                 'name', 'sector', 'market_cap_basic',
                 'Recommend.All', 'RSI', 'MACD.macd', 'SMA20', 'BB.lower', 'BB.upper', 'close'
             )
             .where(
                 Column('market_cap_basic').between(self.min_market_cap, self.max_market_cap),
                 Column('sector').isin(sectors)
             )
        )
        
        try:
            _, df = q.get_scanner_data()
            if df.empty:
                print("No stocks found matching the criteria.")
                return None
            
            print(f"Screener found {len(df)} stocks.")
            return df
        except Exception as e:
            print(f"Error fetching from Screener: {e}")
            return None
