import requests
import pandas as pd
from datetime import datetime

def get_data_direct(ticker, range="1mo", interval="1d"):
    print(f"Testing direct request for {ticker}...")
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?range={range}&interval={interval}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
            result = data['chart']['result'][0]
            meta = result['meta']
            print(f"Price: {meta['regularMarketPrice']}")
            
            timestamps = result['timestamp']
            quotes = result['indicators']['quote'][0]
            closes = quotes['close']
            
            df = pd.DataFrame({'Close': closes}, index=pd.to_datetime(timestamps, unit='s'))
            print(df.head())
            return True
        else:
            print(f"No data found in response: {data}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

get_data_direct("TCS.NS")
get_data_direct("TATAMOTORS.NS")
get_data_direct("AAPL")