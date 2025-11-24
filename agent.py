from tools import get_stock_price, get_stock_history, analyze_sentiment
from logger_config import setup_logger

logger = setup_logger('agent')

class StockAgent:
    def __init__(self):
        self.context = []
        self.last_ticker = None
        logger.info("StockAgent initialized")

    def extract_ticker(self, query):
        """Extracts a likely stock ticker or company name from the query."""
        words = query.split()
        common_words = {"I", "A", "AM", "PM", "IS", "ARE", "WAS", "WERE", "BE", "BEEN", "BEING", "HAVE", "HAS", "HAD", "DO", "DOES", "DID", "WILL", "WOULD", "SHALL", "SHOULD", "MAY", "MIGHT", "MUST", "CAN", "COULD", "OF", "IN", "ON", "AT", "TO", "FOR", "FROM", "WITH", "BY", "ABOUT", "AGAINST", "BETWEEN", "INTO", "THROUGH", "DURING", "BEFORE", "AFTER", "ABOVE", "BELOW", "FROM", "UP", "DOWN", "IN", "OUT", "ON", "OFF", "OVER", "UNDER", "AGAIN", "FURTHER", "THEN", "ONCE", "HERE", "THERE", "WHEN", "WHERE", "WHY", "HOW", "ALL", "ANY", "BOTH", "EACH", "FEW", "MORE", "MOST", "OTHER", "SOME", "SUCH", "NO", "NOR", "NOT", "ONLY", "OWN", "SAME", "SO", "THAN", "TOO", "VERY", "S", "T", "CAN", "WILL", "JUST", "DON", "SHOULD", "NOW", "BUY", "SELL", "PRICE", "SENTIMENT", "RECOMMEND", "TELL", "ME", "WHAT", "WHICH", "WHO", "WHOM", "WHOSE", "IF", "IT", "COOL", "THANKS", "THANK", "YOU", "OKAY", "OK", "GOOD", "GREAT", "BYE", "HELLO", "HI", "HEY", "NICE", "AWESOME"}
        
        # 1. Look for explicit uppercase words that are not stopwords
        candidates = [word.strip("?!.,") for word in words if word.strip("?!.,").isupper() and word.strip("?!.,") not in common_words and len(word.strip("?!.,")) <= 10] # Increased length for company names
        if candidates:
            return candidates[0]
        
        # 1.5 Handle single word queries that might be lowercase company names
        if len(words) == 1:
            clean_word = words[0].strip("?!.,").upper()
            if clean_word not in common_words:
                return clean_word

        # 2. Look for words after context keywords
        lower_query = query.lower()
        keywords = ["about", "for", "buy", "sell", "price", "of", "ticker", "stock"]
        words_lower = lower_query.split()
        
        for i, word in enumerate(words_lower):
            clean_word = word.strip("?!.,")
            if clean_word in keywords and i + 1 < len(words):
                # Capture up to 3 subsequent words as a potential company name
                potential_name_parts = []
                for j in range(i + 1, min(i + 4, len(words))):
                    part = words[j].strip("?!.,")
                    if part.upper() in common_words and part.lower() not in ["motors", "steel", "power", "consultancy", "services", "technologies", "enterprises", "ltd", "limited", "inc", "corp"]:
                         break # Stop if we hit a common word that isn't part of a company name
                    potential_name_parts.append(part)
                
                if potential_name_parts:
                    candidate = " ".join(potential_name_parts)
                    return candidate # Return the multi-word string
        
        return None

    def process_query(self, query):
        """Process user query and return response."""
        logger.info(f"Processing query: {query}")
        self.context.append({"role": "user", "content": query})
        
        response = ""
        q_lower = query.lower().strip("?!., ")
        
        # Handle small talk / conversational inputs first
        small_talk = {
            "cool": "Glad you think so! Let me know if you need more stock info.",
            "thanks": "You're welcome! Happy to help.",
            "thank you": "You're welcome!",
            "ok": "Okay! What's next?",
            "okay": "Okay! Ready for your next question.",
            "good": "Great! Anything else?",
            "great": "Awesome! Let me know if you have more questions.",
            "bye": "Goodbye! Happy trading!",
            "hello": "Hello! I can help you with stock prices, sentiment, and recommendations.",
            "hi": "Hi there! Ask me about any stock.",
            "hey": "Hey! How can I help you with the market today?",
            "nice": "Thanks!",
            "awesome": "I try my best! :)"
        }
        
        if q_lower in small_talk:
            response = small_talk[q_lower]
            self.context.append({"role": "agent", "content": response})
            return response
            
        # Also check for partial matches for thanks/hello if not exact
        if "thank" in q_lower:
             response = "You're welcome!"
             self.context.append({"role": "agent", "content": response})
             return response
        
        ticker_candidate = self.extract_ticker(query)
        ticker = None

        # Try to resolve a new ticker from the query
        if ticker_candidate:
            price = get_stock_price(ticker_candidate)
            if price:
                ticker = ticker_candidate
            else:
                from tools import lookup_ticker
                found_ticker = lookup_ticker(ticker_candidate)
                if found_ticker:
                    ticker = found_ticker
                    response += f"*(Found ticker {ticker} for '{ticker_candidate}')*\n\n"
        
        # If no new ticker found, check if we have context
        if not ticker and self.last_ticker:
            # Check if the query implies a follow-up (contains keywords or is short)
            # For now, we assume if no other ticker is mentioned, it refers to the last one
            ticker = self.last_ticker
            # response += f"*(Continuing with {ticker})*\n\n" # Optional: explicit confirmation

        if ticker:
            self.last_ticker = ticker # Update context

            # Determine intent
            q_lower = query.lower()
            
            if "price" in q_lower:
                price = get_stock_price(ticker)
                if price:
                    response += f"The current price of {ticker} is ${price:.2f}."
                else:
                    response += f"Could not fetch price for {ticker}. Please check if the ticker is correct."
            
            elif "sentiment" in q_lower:
                from tools import get_stock_news
                news_items = get_stock_news(ticker)
                if news_items:
                    sentiments = []
                    response_parts = [f"**News Sentiment for {ticker}:**\n"]
                    for item in news_items[:3]:
                        title = item.get('title', '')
                        link = item.get('link', '')
                        sentiment, score = analyze_sentiment(title)
                        sentiments.append(score)
                        response_parts.append(f"- [{title}]({link}) - *{sentiment}* ({score:.2f})")
                    
                    avg_score = sum(sentiments) / len(sentiments) if sentiments else 0
                    overall_sentiment = "Positive" if avg_score > 0.1 else "Negative" if avg_score < -0.1 else "Neutral"
                    response_parts.insert(1, f"**Overall Sentiment:** {overall_sentiment} (Score: {avg_score:.2f})\n")
                    response += "\n".join(response_parts)
                else:
                    response += f"No recent news found for {ticker}."
            
            elif "recommend" in q_lower or "buy" in q_lower or "sell" in q_lower:
                from tools import calculate_recommendation
                rec, reason = calculate_recommendation(ticker)
                
                # Handle specific "what if I sell/buy" questions
                if "what if" in q_lower:
                    price = get_stock_price(ticker)
                    if "sell" in q_lower:
                        response += f"If you sell {ticker} now at ${price:.2f}, you would be realizing the current value. "
                        if rec == "Sell":
                            response += "Given the 'Sell' recommendation, this aligns with the analysis."
                        elif rec == "Buy":
                            response += "However, the recommendation is to 'Buy', so you might miss out on potential gains."
                        else:
                            response += "The recommendation is 'Hold', suggesting stability or uncertainty."
                    elif "buy" in q_lower:
                        response += f"If you buy {ticker} now at ${price:.2f}, you are entering at this price point. "
                        if rec == "Buy":
                            response += "This aligns with the 'Buy' recommendation."
                        elif rec == "Sell":
                            response += "However, the recommendation is to 'Sell', suggesting potential downside."
                        else:
                            response += "The recommendation is 'Hold', so proceed with caution."
                    response += f"\n\n**Standard Recommendation:** {rec}\n{reason}"
                else:
                    response += f"**Recommendation for {ticker}:** {rec}\n{reason}"
            
            elif "tell me about" in q_lower or "info" in q_lower or "summary" in q_lower:
                 # General summary
                price = get_stock_price(ticker)
                from tools import calculate_recommendation
                rec, reason = calculate_recommendation(ticker)
                
                response += f"**Summary for {ticker}:**\n"
                if price:
                    response += f"- **Current Price:** ${price:.2f}\n"
                response += f"\n{reason}"

            else:
                # Default to price if ticker is found but no specific intent
                # If it's a follow-up without specific keywords (e.g. "is it good?"), default to recommendation
                if "good" in q_lower or "bad" in q_lower:
                     from tools import calculate_recommendation
                     rec, reason = calculate_recommendation(ticker)
                     response += f"**Recommendation for {ticker}:** {rec}\n{reason}"
                else:
                    price = get_stock_price(ticker)
                    if price:
                        response += f"The current price of {ticker} is ${price:.2f}."
                    else:
                        response += f"I found ticker {ticker}, but couldn't fetch data."

        elif "hello" in query.lower() or "hi" in query.lower():
             response = "Hello! I can help you with stock prices, sentiment, and recommendations. Try asking 'What is the price of AAPL?'"
        
        else:
            if ticker_candidate:
                 response = f"I couldn't find a valid ticker for '{ticker_candidate}'. Please try specifying the exact ticker (e.g., TATAMOTORS.NS)."
            else:
                response = "I didn't catch the stock ticker. Please specify one (e.g., AAPL, TSLA)."

        self.context.append({"role": "agent", "content": response})
        return response

    def get_context(self):
        return self.context
