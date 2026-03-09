import json
import os
import sys
import pandas as pd
from dotenv import load_dotenv
from polymarket_fetcher import PolymarketFetcher
from news_fetcher import NewsFetcher
from analyzer import TradeAnalyzer

# Force UTF-8 on Windows command lines to prevent crashes on ₹ or emojis
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

def get_news_summary(filepath: str, max_articles: int = 15) -> str:
    """Reads the JSONL file and extracts headlines for the AI context."""
    if not os.path.exists(filepath):
        return "No news archive found."
        
    summary_lines = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= max_articles:
                    break
                article = json.loads(line)
                title = article.get("title", "No Title")
                date = article.get("date", "Unknown Date")
                source = article.get("source", {}).get("title", "Unknown Source")
                summary_lines.append(f"- [{date}] {title} (Source: {source})")
                
        if not summary_lines:
            return "News archive was empty."
            
        return "\n".join(summary_lines)
    except Exception as e:
        return f"Error reading news: {e}"

def main():
    # 1. Configuration & Initialization
    # Ensure your Ollama model is running locally (e.g., 'ollama run gemma2')
    EVENT_REGISTRY_KEY = os.getenv("EVENT_REGISTRY_API_KEY")
    REPORT_FILE = "result.md"
    
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("# Quantitative Trading Reports\n\n")
    
    poly = PolymarketFetcher()
    news = NewsFetcher(api_key=EVENT_REGISTRY_KEY)
    analyzer = TradeAnalyzer(model_name="gemma2") 

    print("=== Starting Quantitative Pipeline ===\n")

    # 2. Fetch Polymarket Sentiment
    print("-> Pulling prediction market odds...")
    indian_keywords = ["india", "modi", "war", "china", "defense", "military"]
    df_odds = poly.get_live_odds(keywords=indian_keywords, limit=150)
    
    poly_summary = "No relevant Polymarket events found."
    if not df_odds.empty:
        # Convert the top 5 most liquid events into a string for the AI
        top_events = df_odds.head(5)
        summary_lines = []
        for _, row in top_events.iterrows():
            summary_lines.append(f"- {row['Market Question']} | Odds: {row['Current Odds']} | Vol: ${row['Liquidity (USD)']:,.0f}")
        poly_summary = "\n".join(summary_lines)

    # 3. Dynamic Sector Identification & Screening
    print("-> Determining affected sectors based on Polymarket data...\n")
    target_sectors = analyzer.identify_affected_sectors(poly_summary)
    
    if not target_sectors:
        print("No sectors identified. Exiting.")
        return
        
    print(f"-> Screening for small/mid caps in: {target_sectors}...\n")
    from screener_fetcher import ScreenerFetcher
    from technical_filter import TechnicalFilter
    
    screener = ScreenerFetcher()
    screened_df = screener.get_small_mid_caps(target_sectors)
    
    if screened_df is None or screened_df.empty:
        print("No tickers passed fundamental screening. Exiting.")
        return
        
    print("-> Filtering for strong buy and sell technical ratings...\n")
    tech_filter = TechnicalFilter()
    survivors_data = tech_filter.filter_strong_signals(screened_df)
    
    if not survivors_data:
        print("No tickers passed technical filtering. Exiting.")
        return

    # Cap at 3 purely for terminal convenience and API limits
    for survivor in survivors_data[:3]:
        full_ticker = survivor['ticker']
        clean_ticker = full_ticker.split(':')[-1] if ':' in full_ticker else full_ticker
        print(f"\n{'='*70}\n[RUNNING PIPELINE FOR {full_ticker}]\n{'='*70}")
        news_file = f"{clean_ticker}_news.jsonl"
        
        # 4. Fetch Recent News
        print("-> Pulling news archive...")
        # Clean ticker name for keywords (e.g., "HAL.NS" -> "HAL")
        news_search_ticker = clean_ticker.replace(".NS", "").replace(".BO", "")
        
        # Optional: You can comment this out if you already downloaded the news today to save API credits
        news.fetch_historical_news(
            keywords=[news_search_ticker, "India", "business", "market"],
            start_date="2026-02-01", 
            end_date="2026-03-06",
            output_file=news_file,
            max_articles=25
        )
        
        news_summary = get_news_summary(news_file, max_articles=10)

        # 5. Run Technical Analysis & AI Generation
        print(f"-> Crunching technicals and generating AI report for {full_ticker}...\n")
        report = analyzer.generate_report(
            ticker=full_ticker, 
            polymarket_data=poly_summary, 
            news_summary=news_summary,
            ta_data=survivor
        )
        
        # 6. Output the Final Result
        print("-" * 70)
        print(f" OLLAMA QUANTITATIVE REPORT: {full_ticker} ")
        print("-" * 70 + "\n")
        print(report)
        print("\n" + "-" * 70)
        
        with open(REPORT_FILE, "a", encoding="utf-8") as f:
            f.write(f"## OLLAMA QUANTITATIVE REPORT: {full_ticker}\n\n")
            f.write(report)
            f.write("\n\n---\n\n")
            
    print(f"\nAll reports have been sequentially saved to {REPORT_FILE}")

if __name__ == "__main__":
    main()