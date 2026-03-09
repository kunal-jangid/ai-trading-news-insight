import yfinance as yf
import ollama
import pandas as pd
import json

class TradeAnalyzer:
    def __init__(self, model_name="gemma2"):
        self.model_name = model_name

    def get_stock_context(self, ticker: str) -> dict:
        # We no longer use yfinance for full contexts, but leaving it as backward compatible if ever needed.
        pass

    def identify_affected_sectors(self, polymarket_data: str) -> list[str]:
        """Prompts Ollama to identify Indian industrial sectors affected by Polymarket events."""
        print(f"Asking {self.model_name} to identify affected Indian sectors...")
        
        valid_sectors = [
            'Producer Manufacturing', 'Finance', 'Energy Minerals', 'Process Industries',
            'Communications', 'Electronic Technology', 'Miscellaneous',
            'Technology Services', 'Industrial Services', 'Non-Energy Minerals',
            'Consumer Non-Durables', 'Transportation', 'Consumer Durables',
            'Health Technology', 'Utilities'
        ]
        
        prompt = f"""
        You are a quantitative financial analyst specializing in the Indian stock market (NSE/BSE).
        
        Here is the current geopolitical sentiment and event probabilities from Polymarket:
        {polymarket_data}
        
        Based on these events, which 3 macro Indian industrial sectors will face massive supply chain disruptions, shifts, or demand surges?
        You MUST pick exactly 3 sectors from this exact list: {valid_sectors}.
        
        Return ONLY a raw JSON list of the 3 sector names (e.g., ["Technology Services", "Finance", "Utilities"]).
        Do not include any markdown formatting, explanations, or other text. Just the JSON list.
        """
        
        try:
            response = ollama.chat(model=self.model_name, messages=[
                {
                    'role': 'user',
                    'content': prompt
                }
            ])
            
            content = response['message']['content'].strip()
            
            # Clean up markdown if the model ignored instructions
            if "```json" in content:
                content = content.split("```json")[-1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[-1].split("```")[0].strip()
                
            sectors = json.loads(content)
            
            if isinstance(sectors, list) and len(sectors) > 0:
                print(f"Identified sectors: {sectors}")
                return sectors
            else:
                print(f"Warning: Unexpected format from Ollama: {content}")
                return ["Process Industries"] # Fallback
                
        except Exception as e:
            print(f"Failed to extract sectors from Ollama. Error: {e}")
            return ["Process Industries"] # Fallback

    def generate_report(self, ticker: str, polymarket_data: str, news_summary: str, ta_data: dict = None):
        """Passes all technical and fundamental data to Ollama to generate a trading report."""
        if ta_data is None:
            return "Error: No Technical Analysis data provided."

        print(f"Generating quantitative AI report using {self.model_name} for {ticker}...")
        
        indicators = ta_data.get('indicators', {})
        summary = ta_data.get('summary', {})
        
        # Extract some useful indicators, fallback to N/A
        current_price = indicators.get("close", "N/A")
        rsi_14 = indicators.get("RSI", "N/A")
        macd = indicators.get("MACD.macd", "N/A")
        sma_20 = indicators.get("SMA20", "N/A")
        ema_20 = indicators.get("EMA20", "N/A")
        bb_upper = indicators.get("BBUpper", "N/A")
        bb_lower = indicators.get("BBLower", "N/A")
        
        signal_type = ta_data.get('signal_type', 'UNKNOWN')
        
        # We explicitly instruct the model on how to interpret the technicals
        prompt = f"""
        You are a ruthless, quantitative financial analyst. 
        I am considering a trade on the Indian ticker {ticker}. 
        
        Here is the current technical context from TradingView for {ticker}:
        - Current Price: ₹{current_price}
        - Rating: {summary.get('RECOMMENDATION', 'N/A')}
        - OVERALL SIGNAL: {signal_type}
        - RSI (14-day): {rsi_14} (Note: >70 is overbought, <30 is oversold).
        - SMA (20-day): ₹{sma_20}
        - MACD: {macd}
        - Bollinger Bands: Upper limit is ₹{bb_upper}, Lower limit is ₹{bb_lower}.
        
        Here is the geopolitical sentiment from Polymarket:
        {polymarket_data}
        
        Here is the recent news context:
        {news_summary}
        
        Write a comprehensive, highly critical trading report. 
        1. Assess the geopolitical/news risk based on the Polymarket and news text. Are we reacting to noise or a structural shift?
        2. Evaluate the price action using the provided TradingView indicators. Even if the news is good or bad, is the broader signal ({signal_type}) valid?
        3. Give a final verdict: STRONG BUY, BUY ON DIP, HOLD, SELL, SHORT, or AVOID.
        """

        try:
            response = ollama.chat(model=self.model_name, messages=[
                {
                    'role': 'user',
                    'content': prompt
                }
            ])
            return response['message']['content']
        except Exception as e:
            return f"Failed to connect to Ollama. Ensure your local model is running. Error: {e}"

if __name__ == "__main__":
    analyzer = TradeAnalyzer(model_name="gemma2") 
    
    # Mock data for testing the prompt structure
    mock_poly = "Reserve Bank of India decision in March? Yes (Rate Cut): 15.0% | No: 85.0% with $130,000 volume."
    mock_news = "Inflation data comes in slightly higher than expected, reducing hopes for an immediate RBI rate cut."
    
    # Testing with a highly liquid Indian banking stock
    report = analyzer.generate_report("HDFCBANK.NS", mock_poly, mock_news)
    
    print("\n" + "="*60)
    print(f"🤖 QUANTITATIVE TRADING REPORT")
    print("="*60 + "\n")
    print(report)