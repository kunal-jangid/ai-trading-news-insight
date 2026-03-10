# 📈 AI Quantitative Trading Dashboard

## Overview
Macro geopolitical event-driven sectoral screener powered by **Polymarket, Ollama, and TradingView**. 
This tool acts as an autonomous quantitative analyst. It ingests live betting odds from prediction markets to gauge geopolitical and macroeconomic sentiment, identifies sectors poised to be affected, screens for fundamentally strong Small and Mid-cap Indian stocks in those sectors, filters them by TradingView's daily technical ratings, and finally generates a comprehensive investment thesis using a local Large Language Model (LLM) fed with the latest financial news.

---

## Installation & Setup
Follow these steps to get the environment running from scratch, assuming no prior setup.

### 1. Prerequisites
- **Python 3.10+**: Ensure Python is installed on your system.
- **Ollama**: This project requires `ollama` for local, private AI analysis so no OpenAI/Anthropic API costs are incurred.
  - Download and install Ollama from [ollama.com](https://ollama.com/).
  - Once installed, open your terminal and pull the required model (we use `gemma2` by default):
    ```bash
    ollama run gemma2
    ```
    *Note: Keep the Ollama service running in the background for the application to communicate with it.*

### 2. Clone the Repository
```bash
git clone https://github.com/kunal-jangid/ai-trading-news-insight.git
cd trading-news-insight
```

### 3. Install Dependencies
Install the required Python packages (create a virtual environment first if preferred):
```bash
pip install streamlit pandas requests python-dotenv ollama yfinance tradingview-screener
```
*(Tip: Make sure to freeze these into a `requirements.txt` if you haven't already).*

### 4. Setting up Environment Variables (`.env`)
You need an API key from EventRegistry to fetch the latest business news.
1. Sign up at [EventRegistry.org](https://eventregistry.org/) or [NewsAPI.ai](https://newsapi.ai/) to get a free API key.
2. In the root directory of the project, create a new file named exactly `.env`.
3. Add the following line to your `.env` file, replacing the placeholder with your actual key:
   ```env
   EVENT_REGISTRY_API_KEY=your_copied_api_key_here
   ```

### 5. Running the Application
You can run the dashboard via Streamlit for an interactive UI:
```bash
streamlit run app.py
```
Alternatively, for a terminal-based sequential run that outputs to a markdown file (`result.md`):
```bash
python main.py
```

---

## Technical Walkthrough

The quantitative pipeline executes in 5 sequential steps, orchestrated in `app.py` (for the Streamlit UI) and `main.py` (for the CLI):

### Step 1: Geopolitical Sentiment Extraction (`polymarket_fetcher.py`)
- Connects to the Polymarket Gamma API to gather active prediction markets.
- Filters these live markets using keywords (e.g., "india", "modi", "war", "rbi", "china") and parses the probability odds and liquidity.
- Consolidates the most heavily traded macroeconomic events into a summary text block.

### Step 2: Sector Identification (`analyzer.py` & **Ollama**)
- Sends the Polymarket geopolitical summary to the local Ollama LLM (`gemma2`).
- Prompts the LLM to act as a financial analyst and strictly map those geopolitical events to exactly 3 highly impacted Indian industrial sectors from a predefined list.
- Forces the LLM to return these target sectors in a strict JSON format for programmatic use.

### Step 3: Fundamental Screening (`screener_fetcher.py`)
- Utilizes the `tradingview-screener` library to query the Indian stock market.
- Given the target sectors identified in Step 2, it screens for companies with a basic market capitalization between ₹500 Cr and ₹50,000 Cr (Small to Mid-cap).
- This intentionally filters out massive blue chips where alpha is harder to generate, focusing instead on agile companies with higher growth elasticity.

### Step 4: Technical Filtering (`technical_filter.py`)
- Reads the fundamentally screened Pandas DataFrame, extracting the natively calculated `Recommend.All` numeric ratings sourced directly from the TradingView screener payload.
- Consolidating the technical metadata natively from the screener array completely circumvents standard 429 HTTP API rate limits or Cloudflare blocks caused by iterative API loops.
- Ruthlessly filters out any stock that does not map to a `BUY`/`STRONG_BUY` OR `SELL`/`STRONG_SELL` summary rating. It guarantees we only consider equities with active, established momentum in either direction (bullish breakouts or bearish breakdowns).

### Step 5: News Gathering & AI Investment Thesis (`news_fetcher.py`, `main.py`, & `analyzer.py`)
- For the surviving fundamentally strong and technically bullish tickers, `news_fetcher.py` pulls the latest business news articles (capped at ~15-25) using the Event Registry API.
- The `TradeAnalyzer` aggregates all context: Polymarket macro odds, recent specific news headlines, and the exact granular technical indicators retrieved from TradingView (RSI, MAs, MACD, Bollinger Bands).
- Prompts the local LLM to generate a highly critical, holistic trading report. The prompt explicitly asks the LLM to weigh the news risk against the technical price action and give a final verdict (STRONG BUY, BUY ON DIP, HOLD, SELL, SHORT, or AVOID). 
- Finally, the Streamlit interface (`app.py`) dynamically displays this resulting thesis alongside an interactive TradingView chart widget.

---

## Limitations

1. **API Rate Limits:** The free tier of Event Registry (News API) heavily restricts the number of articles you can fetch. Running the pipeline excessively will exhaust your daily quota, stalling the final analysis step.
2. **LLM Formatting Hallucinations:** While we use strict system prompts, local models like `gemma2` can sometimes struggle with structural compliance (e.g., failing to return valid JSON in the sector identification step), which requires robust string-parsing fallbacks.
3. **Data Freshness / Relevance (Polymarket):** The Polymarket API focuses primarily on US/Global events. If there are no high-liquidity Indian or Asian macroeconomic markets currently active, the primary trigger for the sectoral screener may lack relevant signal.
4. **Execution Speed:** Running LLM inference locally blocks the application. Processing multiple target sectors and analyzing several surviving stocks sequentially can take several minutes depending on the host machine's GPU/CPU capabilities.

---

## 📈 Future Development Ideas (Financial Analyst Perspective)

To evolve this tool from a hobbyist dashboard into an institutional-grade alpha generation engine, consider the following expansions:

1. **Options Flow & Volatility Integration** 
   While technicals show price momentum, options data reveals *institutional conviction*. Integrate NSE option chain data to filter survivors by Put-Call Ratio (PCR), Open Interest (OI) buildup, and Implied Volatility (IV) percentile. A stock breaking out technically combined with aggressive, out-of-the-money call buying is a significantly stronger signal.
   
2. **Automated Forward Walk & Backtesting Engine** 
   Currently, the LLM provides an opinion, but we don't know its analytical hit rate. Build a background cron job that logs every "STRONG BUY" verdict generated by the model into a SQLite/PostgreSQL database along with the Entry Price, a predefined Target, and a Stop-Loss. Track the T+5, T+20, and T+60 returns to statistically evaluate and tune the LLM's predictive efficacy.

3. **Quantitative News Sentiment Scoring**
   Instead of just asking the LLM to contextually read the news, run a lightweight NLP sentiment analyzer (like FinBERT) across real-time headlines continuously. Trigger the pipeline *only* when the z-score of the sentiment for a specific sector deviates drastically from its 30-day moving average, signaling an actionable supply/demand shock.

4. **Risk Parity & Correlation Matrix**
   If the pipeline returns 3 valid stocks, they might all be heavily correlated (e.g., all Defense stocks reacting to the same border news). Introduce a correlation matrix using the standard deviations of daily historical returns. The dashboard should suggest optimal position sizing based on maintaining a Beta-neutral portfolio or maximizing the Sharpe ratio, rather than naive equal-weighting.

5. **Alternative Data Sources for Supply Chain Vectors**
   Move beyond just prediction markets. Integrate leading economic indicators such as global shipping freight rates (Baltic Dry Index), local domestic auto sales, GST collection data trends, or even tracking APIs for port congestion. This allows the model to preempt material supply chain shifts before they explicitly hit the financial news cycle.

----
*I used gemini to generate this Readme file and further development ideas to benefit from finance related knowledge it has. Let's have fingers crossed that I do not eventually forget about this and keep working on.*
