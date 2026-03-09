from tradingview_ta import TA_Handler, Interval
from screener_fetcher import ScreenerFetcher

screener = ScreenerFetcher()
tickers = screener.get_small_mid_caps(['Electronic Technology'])

if tickers:
    test_ticker = tickers[0]
    print(f"Testing raw ticker from screener: {test_ticker}")
    
    # Test 1: Raw ticker
    try:
        handler = TA_Handler(
            symbol=test_ticker,
            exchange="NSE",
            screener="india",
            interval=Interval.INTERVAL_1_DAY
        )
        analysis = handler.get_analysis()
        print(f"Test 1 (Raw '{test_ticker}'): SUCCESS. Rating: {analysis.summary.get('RECOMMENDATION')}")
    except Exception as e:
        print(f"Test 1 (Raw '{test_ticker}'): FAILED. Error: {e}")

    # Test 2: Stripped ticker
    stripped_ticker = test_ticker.split(':')[-1] if ':' in test_ticker else test_ticker
    try:
        handler = TA_Handler(
            symbol=stripped_ticker,
            exchange="NSE",
            screener="india",
            interval=Interval.INTERVAL_1_DAY
        )
        analysis = handler.get_analysis()
        print(f"Test 2 (Stripped '{stripped_ticker}'): SUCCESS. Rating: {analysis.summary.get('RECOMMENDATION')}")
    except Exception as e:
        print(f"Test 2 (Stripped '{stripped_ticker}'): FAILED. Error: {e}")
        
    # Test 3: BSE fallback
    try:
        handler = TA_Handler(
            symbol=stripped_ticker,
            exchange="BSE",
            screener="india",
            interval=Interval.INTERVAL_1_DAY
        )
        analysis = handler.get_analysis()
        print(f"Test 3 (BSE Fallback '{stripped_ticker}'): SUCCESS. Rating: {analysis.summary.get('RECOMMENDATION')}")
    except Exception as e:
        print(f"Test 3 (BSE Fallback '{stripped_ticker}'): FAILED. Error: {e}")
