"""News Search & Sentiment Tool — fetches financial news via Tavily AI search."""
import json
import logging
import sys
from datetime import datetime, timedelta
from langchain_core.tools import tool

logger = logging.getLogger("news_search")

_sentiment_pipeline = None


def _get_pipeline():
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        from transformers import pipeline
        _sentiment_pipeline = pipeline(
            "text-classification",
            model="mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis",
            truncation=True,
            max_length=512,
        )
        logger.info("DistilRoBERTa financial sentiment pipeline loaded.")
    return _sentiment_pipeline


def _classify_sentiment(title: str, description: str = "") -> dict:
    text = f"{title} {description}".strip()
    try:
        result = _get_pipeline()(text)[0]
        return {
            "label": result["label"].lower(),
            "score": round(result["score"], 4),
        }
    except Exception as e:
        logger.warning("Sentiment model inference failed, falling back to neutral: %s", e)
        return {"label": "neutral", "score": 0.5}


@tool
def search_financial_news(query: str) -> str:
    """Search for recent financial news articles about a company or topic.

    Use this tool when the user asks about:
    - Recent news for a company (e.g., "latest news about Reliance")
    - Market sentiment or what's happening with a stock
    - News-based risk assessment
    - Any current events affecting a company

    Args:
        query: Search query — company name, ticker, or topic
               (e.g., "Reliance Industries earnings", "HDFC Bank NIM", "TCS deal wins")

    Returns:
        JSON with news articles including title, source, URL, date, and sentiment.
    """
    from app.config import settings

    if not settings.TAVILY_API_KEY:
        return json.dumps({
            "error": "TAVILY_API_KEY not configured",
            "query": query,
            "articles": [],
        })

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=settings.TAVILY_API_KEY)

        search_query = f"{query} latest news India 2026"

        response = client.search(
            query=search_query,
            search_depth="advanced",
            max_results=8,
            include_answer=False,
            include_domains=["economictimes.com", "moneycontrol.com", "livemint.com",
                             "business-standard.com", "ndtvprofit.com", "financialexpress.com"],
        )

        articles = []
        for result in response.get("results", []):
            title = result.get("title", "")
            content = result.get("content", "")
            sentiment = _classify_sentiment(title, content)
            articles.append({
                "title": title,
                "description": content[:300] if content else "",
                "source_name": result.get("url", "").split("/")[2].replace("www.", ""),
                "url": result.get("url"),
                "published_at": result.get("published_date") or datetime.now().isoformat(),
                "sentiment": sentiment,
            })

        sentiments = [a["sentiment"]["label"] for a in articles]
        pos = sentiments.count("positive")
        neg = sentiments.count("negative")
        overall = {
            "positive": pos,
            "negative": neg,
            "neutral": sentiments.count("neutral"),
            "total": len(sentiments),
            "overall_sentiment": "positive" if pos > neg else ("negative" if neg > pos else "neutral"),
        }

        return json.dumps({
            "query": query,
            "article_count": len(articles),
            "articles": articles,
            "sentiment_summary": overall,
            "source": "Tavily",
            "fetched_at": datetime.now().isoformat(),
        })

    except Exception as e:
        return json.dumps({
            "error": f"News search failed: {str(e)}",
            "query": query,
            "articles": [],
            "source": "Tavily",
        })


# =============================================================================
# HOW TO TEST THIS FILE
# =============================================================================
# Make sure you are inside the backend folder first:
#   cd D:\investment-research-dashboard-day2\investment-research-dashboard\backend
#
# Test 1 — Sentiment model only (no API key needed, downloads model ~80MB first run):
#   python -m app.ai.tools.news_search
#
# Test 2 — Full news search (needs TAVILY_API_KEY set in your .env file):
#   python -m app.ai.tools.news_search --news "Reliance Industries"
#   python -m app.ai.tools.news_search --news "TCS earnings"
#   python -m app.ai.tools.news_search --news "HDFC Bank"
#
# Expected output for Test 1:
#   === Sentiment Model Test ===
#   [PASS] 'Reliance Industries reports record profit, shares surge 5%...'
#          Expected: positive | Got: positive (confidence: 0.98)
#   [PASS] 'TCS misses earnings estimates, stock falls sharply...'
#          Expected: negative | Got: negative (confidence: 0.91)
#   [PASS] 'HDFC Bank announces quarterly results in line with expectations...'
#          Expected: neutral  | Got: neutral  (confidence: 0.85)
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # --- Test 1: Sentiment model directly ---
    print("\n=== Sentiment Model Test ===")
    test_sentences = [
        ("Reliance Industries reports record profit, shares surge 5%", "positive"),
        ("TCS misses earnings estimates, stock falls sharply", "negative"),
        ("HDFC Bank announces quarterly results in line with expectations", "neutral"),
    ]
    for text, expected in test_sentences:
        result = _classify_sentiment(text)
        status = "PASS" if result["label"] == expected else "FAIL"
        print(f"[{status}] '{text[:60]}...'")
        print(f"       Expected: {expected} | Got: {result['label']} (confidence: {result['score']})")

    # --- Test 2: Full news search (requires TAVILY_API_KEY in .env) ---
    if "--news" in sys.argv:
        query = sys.argv[sys.argv.index("--news") + 1] if len(sys.argv) > sys.argv.index("--news") + 1 else "Reliance Industries"
        print(f"\n=== News Search Test: '{query}' ===")
        output = search_financial_news.invoke({"query": query})
        data = json.loads(output)
        if "error" in data:
            print(f"Error: {data['error']}")
        else:
            print(f"Fetched {data['article_count']} articles")
            print(f"Overall sentiment: {data['sentiment_summary']['overall_sentiment']}")
            print(f"  Positive: {data['sentiment_summary']['positive']}")
            print(f"  Negative: {data['sentiment_summary']['negative']}")
            print(f"  Neutral : {data['sentiment_summary']['neutral']}")
            print("\nArticles:")
            for i, a in enumerate(data["articles"], 1):
                print(f"  {i}. [{a['sentiment']['label'].upper()}] {a['title'][:70]}")
