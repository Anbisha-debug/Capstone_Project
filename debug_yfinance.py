import yfinance as yf

def test_ticker(ticker):
    print(f"Testing {ticker}...")
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        if hist.empty:
            print(f"No history for {ticker}")
        else:
            print(f"Success! Got {len(hist)} rows for {ticker}")
            print(hist.head())
    except Exception as e:
        print(f"Error: {e}")

test_ticker("TCS.NS")
test_ticker("TATAMOTORS.NS")
test_ticker("AAPL")
