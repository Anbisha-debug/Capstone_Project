Features Implemented:
  
  Real-time Stock Data: Fetches current prices and history using direct Yahoo Finance API (more robust than yfinance).
  Smart Ticker Lookup: Automatically finds ticker symbols for company names (e.g., "TATA" -> "TATAMOTORS.NS"). Prioritizes Indian Equities (NSE/BSE).
  News Sentiment Analysis: Analyzes latest news headlines using TextBlob.
  Recommendation Engine: Provides Buy/Sell/Hold recommendations with detailed reasoning (price trends + news summary).
  Conversation Context: Remembers the last discussed stock, allowing follow-up questions like "What if I sell?" or "Is it good?".
  Conversational Small Talk: Handles greetings ("Hello"), gratitude ("Thanks"), and other small talk ("Cool") politely without confusing them for stock tickers.
  Logging: Tracks all agent activities in agent.log.
  
How to Run
  Activate Environment (if applicable).
  Run the App:
  python -m streamlit run main.py
  Open Browser: The app will open at http://localhost:8501.

Usage Guide
  Ask for Price: "What is the price of AAPL?"
  Ask for Sentiment: "Sentiment for TSLA"
  Ask for Recommendation: "Should I buy NVDA?"
  General Info: "Tell me about TATA" (will try to find ticker)
  General Chat: "Hello", "Help"

Verification Results
  Installation: Dependencies installed successfully 
  App Launch: Streamlit app launches correctly.

Logic:
  Price fetching works.
  Sentiment analysis works (tested with mock/real data flow).
  Recommendations are generated based on logic.
