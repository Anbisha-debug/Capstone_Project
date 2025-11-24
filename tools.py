import requests
import pandas as pd
from logger_config import setup_logger
from textblob import TextBlob
from datetime import datetime

logger = setup_logger('tools')

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

def get_stock_price(ticker):
    """Fetches current stock price for a given ticker."""
    try:
        logger.info(f"Fetching stock price for {ticker}")
        url = f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?range=1d&interval=1d"
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
            meta = data['chart']['result'][0]['meta']
            return meta.get('regularMarketPrice')
        return None
    except Exception as e:
        logger.error(f"Error fetching stock price for {ticker}: {e}")
        return None

def get_stock_history(ticker, period="1mo"):
    """Fetches historical stock data."""
    try:
        logger.info(f"Fetching stock history for {ticker} over {period}")
        # Map period to range
        range_map = {"1mo": "1mo", "1d": "1d", "1y": "1y"}
        range_val = range_map.get(period, "1mo")
        
        url = f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?range={range_val}&interval=1d"
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        
        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
            result = data['chart']['result'][0]
            timestamps = result['timestamp']
            quotes = result['indicators']['quote'][0]
            closes = quotes['close']
            
            df = pd.DataFrame({'Close': closes}, index=pd.to_datetime(timestamps, unit='s'))
            return df
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error fetching stock history for {ticker}: {e}")
        return pd.DataFrame()

def get_stock_news(ticker):
    """Fetches latest news for a given ticker."""
    try:
        logger.info(f"Fetching news for {ticker}")
        # Yahoo Finance news is a bit trickier via API, but we can try the search endpoint or a specific news endpoint
        # Using search endpoint which returns news
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={ticker}&newsCount=5"
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        
        if 'news' in data:
            return data['news']
        return []
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {e}")
        return []

def analyze_sentiment(text):
    """Analyzes sentiment of a given text."""
    try:
        if not text:
            return "Neutral", 0.0
        
        # logger.info(f"Analyzing sentiment for text length: {len(text)}") # Reduce log spam
        analysis = TextBlob(text)
        polarity = analysis.sentiment.polarity
        
        if polarity > 0.1:
            return "Positive", polarity
        elif polarity < -0.1:
            return "Negative", polarity
        else:
            return "Neutral", polarity
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        return "Error", 0.0

def calculate_recommendation(ticker):
    """Calculates a recommendation based on price trend and sentiment."""
    try:
        logger.info(f"Calculating recommendation for {ticker}")
        
        # Get Sentiment
        news = get_stock_news(ticker)
        sentiment_score = 0
        news_summary = []
        if news:
            scores = []
            for item in news[:5]:
                title = item.get('title', '')
                _, score = analyze_sentiment(title)
                scores.append(score)
                news_summary.append(f"- \"{title}\" (Sentiment: {score:.2f})")
            sentiment_score = sum(scores) / len(scores) if scores else 0
        
        # Get Price Trend (1mo)
        history = get_stock_history(ticker, period="1mo")
        if history.empty:
            return "Hold", f"Insufficient data found for ticker '{ticker}'. Please check if the ticker is correct (e.g., for Tata Motors, try 'TATAMOTORS.NS')."
            
        start_price = history['Close'].iloc[0]
        end_price = history['Close'].iloc[-1]
        price_change = (end_price - start_price) / start_price
        
        # Logic
        rec = "Hold"
        if sentiment_score > 0.1 and price_change > 0.05:
            rec = "Buy"
        elif sentiment_score < -0.1 and price_change < -0.05:
            rec = "Sell"
            
        # Detailed Reasoning
        reason = f"""
**Analysis for {ticker}:**
1.  **Price Trend (1 Month):**
    -   Start Price: ${start_price:.2f}
    -   Current Price: ${end_price:.2f}
    -   Change: {price_change:.2%} ({'Up' if price_change > 0 else 'Down'})
    
2.  **News Sentiment:**
    -   Average Score: {sentiment_score:.2f} ({'Positive' if sentiment_score > 0.1 else 'Negative' if sentiment_score < -0.1 else 'Neutral'})
    -   *Recent Headlines:*
{chr(10).join(news_summary[:3])}

**Conclusion:**
Based on the {('positive' if price_change > 0 else 'negative')} price trend and {('positive' if sentiment_score > 0.1 else 'negative' if sentiment_score < -0.1 else 'neutral')} sentiment, the recommendation is to **{rec}**.
"""
        return rec, reason

    except Exception as e:
        logger.error(f"Error calculating recommendation for {ticker}: {e}")
        return "Error", str(e)

def lookup_ticker(query):
    """Searches for a ticker symbol using Yahoo Finance API."""
    try:
        logger.info(f"Looking up ticker for query: {query}")
        # Add region=IN to prioritize Indian stocks if likely, or just general search
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=10&newsCount=0"
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        
        if 'quotes' in data and len(data['quotes']) > 0:
            quotes = data['quotes']
            best_match = None
            
            # Priority 1: Indian NSE/BSE equities if query sounds Indian (heuristic) or just generally preferred
            # Let's look for .NS or .BO suffixes first for Indian context
            for quote in quotes:
                symbol = quote.get('symbol', '')
                quote_type = quote.get('quoteType', '')
                if quote_type == 'EQUITY' and (symbol.endswith('.NS') or symbol.endswith('.BO')):
                    best_match = symbol
                    break
            
            # Priority 2: Any Equity
            if not best_match:
                for quote in quotes:
                    if quote.get('quoteType', '') == 'EQUITY':
                        best_match = quote.get('symbol')
                        break
            
            # Fallback: First result
            if not best_match:
                best_match = quotes[0]['symbol']
                
            logger.info(f"Found ticker {best_match} for query {query}")
            return best_match
        return None
    except Exception as e:
        logger.error(f"Error looking up ticker for {query}: {e}")
        return None
