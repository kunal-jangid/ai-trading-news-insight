import streamlit as st
import os
import json
from dotenv import load_dotenv

# Import components
from polymarket_fetcher import PolymarketFetcher
from analyzer import TradeAnalyzer
from screener_fetcher import ScreenerFetcher
from technical_filter import TechnicalFilter
from news_fetcher import NewsFetcher
from main import get_news_summary

load_dotenv()

st.set_page_config(page_title="Quantitative Trading Dashboard", layout="wide", page_icon="📈")

# Helper function to embed TradingView Widget
def render_tradingview_widget(tv_symbol):
    # tv_symbol is already in the format "EXCHANGE:TICKER" (e.g., "NSE:HAL")
    html = f"""
    <!-- TradingView Widget BEGIN -->
    <div class="tradingview-widget-container" style="height:500px;width:100%">
      <div id="tradingview_{tv_symbol.replace(':', '_')}" style="height:calc(100% - 32px);width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
      "autosize": true,
      "symbol": "{tv_symbol}",
      "interval": "D",
      "timezone": "Asia/Kolkata",
      "theme": "dark",
      "style": "1",
      "locale": "en",
      "enable_publishing": false,
      "hide_top_toolbar": false,
      "hide_legend": false,
      "save_image": false,
      "container_id": "tradingview_{tv_symbol.replace(':', '_')}"
    }});
      </script>
    </div>
    <!-- TradingView Widget END -->
    """
    st.components.v1.html(html, height=500)

st.title("📈 AI Quantitative Trading Dashboard")
st.markdown("Macro geopolitical event-driven sectoral screener powered by **Polymarket, Ollama, and TradingView**.")

if st.button("Run Quantitative Pipeline", type="primary"):
    # Initialize components
    poly = PolymarketFetcher()
    analyzer = TradeAnalyzer(model_name="gemma2")
    screener = ScreenerFetcher()
    tech_filter = TechnicalFilter()
    
    EVENT_REGISTRY_KEY = os.getenv("EVENT_REGISTRY_API_KEY")
    news = NewsFetcher(api_key=EVENT_REGISTRY_KEY)
    
    # Setup progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.text("Step 1: Fetching Polymarket Odds...")
    indian_keywords = ["india", "modi", "war", "china", "defense", "military", "rbi", "election"]
    df_odds = poly.get_live_odds(keywords=indian_keywords, limit=150)
    
    poly_summary = "No relevant Polymarket events found."
    if not df_odds.empty:
        top_events = df_odds.head(5)
        summary_lines = [f"- {row['Market Question']} | Odds: {row['Current Odds']}" for _, row in top_events.iterrows()]
        poly_summary = "\n".join(summary_lines)
        
    progress_bar.progress(20)
    
    status_text.text("Step 2: Asking Ollama to map geopolitical odds to core Indian Sectors...")
    target_sectors = analyzer.identify_affected_sectors(poly_summary)
    st.info(f"**Identified Affected Sectors:** {', '.join(target_sectors)}")
    
    progress_bar.progress(40)
    
    if not target_sectors:
        st.error("No valid sectors returned by Ollama. Aborting.")
        st.stop()
        
    status_text.text("Step 3: Screening for Mid/Small Cap stocks in those sectors...")
    screened_df = screener.get_small_mid_caps(target_sectors)
    
    if screened_df is None or screened_df.empty:
        st.warning("No related small/mid cap stocks found in those sectors.")
        st.stop()
        
    st.write(f"Screener found **{len(screened_df)}** stocks. Filtering for extremely Bullish OR Bearish technical ratings...")
    progress_bar.progress(60)
    
    status_text.text("Step 4: Executing TradingView Technical Analysis Filter...")
    survivors_data = tech_filter.filter_strong_signals(screened_df)
    
    if not survivors_data:
        st.warning("Condition failed: No stocks generated a meaningful technical signal (Buy or Sell).")
        st.stop()
        
    bulls = [item['ticker'] for item in survivors_data if item.get('signal_type') == 'BULLISH']
    bears = [item['ticker'] for item in survivors_data if item.get('signal_type') == 'BEARISH']
    
    st.success(f"**Surviving Tickers ({len(survivors_data)}):**")
    if bulls:
        st.write(f"🟢 **Bullish:** {', '.join(bulls)}")
    if bears:
        st.write(f"🔴 **Bearish:** {', '.join(bears)}")
    
    progress_bar.progress(80)
    status_text.text("Step 5: Fetching News & Generating Investment Thesis...")
    
    # We will loop through max 3 survivors to avoid immense waiting times
    for survivor in survivors_data[:3]:
        # 'survivor['ticker']' contains exchange like NSE:HAL. We strip it for the news query to just search the name.
        full_ticker = survivor['ticker']
        clean_name = full_ticker.split(':')[-1] if ':' in full_ticker else full_ticker
        news_file = f"news_{clean_name}.jsonl"
        
        # Download recent business news
        news.fetch_historical_news(
            keywords=[clean_name, "India", "business", "market"],
            start_date="2026-02-01", 
            end_date="2026-03-06",
            output_file=news_file,
            max_articles=15
        )
        news_summary = get_news_summary(news_file, max_articles=8)
        
        # Ask Ollama for the final report
        report = analyzer.generate_report(
            ticker=full_ticker,
            polymarket_data=poly_summary,
            news_summary=news_summary,
            ta_data=survivor
        )
        
        # Display the result
        st.markdown(f"---")
        st.subheader(f"Investment Thesis: {full_ticker}")
        
        # Two columns layout
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown(report)
            
        with col2:
            st.markdown("### TradingView Chart")
            render_tradingview_widget(full_ticker)

    progress_bar.progress(100)
    status_text.text("Pipeline Execution Completed.")
    
    st.balloons()
