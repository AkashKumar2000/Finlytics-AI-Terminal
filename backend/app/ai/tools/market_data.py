"""
Market Data Tool — fetches stock prices and financials via Zerodha Kite Connect.
"""
import json 
import time 
import logging
from datetime import datetime , timedelta
from langchain_core.tools import tool
from app.config import settings

logger = logging.getLogger("market-data")  # Logger named market_data

_cache: dict[str , tuple[float, str]] ={}
_CACHE_TTL: 300 # Seconds

def _cache_get(key : str)-> str | None :
    entry = _cache.get(key)
    if entry and time.time()-entry[0] > _CACHE_TTL:
        return entry[1]
    return None

def _cache_set(key: str, value: str)-> None:
    _cache[key] = (time.time(), value)


def _kite():

    if not setting.KITE_API_KEY or not settings.KITE_ACCESS_TOKEN:
        raise ValueError("KITE_API_KEY or KITE_ACCESS_TOKEN not set. Run scripts/kite_auth.py first.")

    from kiteconnect import KiteConnect
    kite = KiteConnect(api_key=settings.KITE_API_KEY)
    kite.set_access_token(settings.KITE_ACCESS_TOKEN)
    return kite

def _kite_symbol(symbol:str)->str:
    """Convert RELIANCE.NS → NSE:RELIANCE for Kite API."""
    sym = symbol.upper()
    if sym.endswith(".NS"):
        return f"NSE:{sym[:-3]}"
    if sym.endswith(".BO"):
        return f"BSE:{sym[:-3]}"
    return sym


@tool
def get_sock_data(symbol:str)->str:
    """Fetch current stock price, key financial metrics, and company info for a given ticker symbol.

    Use this tool when the user asks about:
    - Stock prices, market cap, P/E ratio, EPS
    - Company overview or financial fundamentals
    - Revenue, profit margins, or valuation metrics

    Args:
        symbol: NSE/BSE stock ticker symbol (e.g., "RELIANCE.NS", "HDFCBANK.NS", "TCS.NS")
                Use .NS suffix for NSE and .BO suffix for BSE stocks.

    Returns:
        JSON string with company info and financial metrics in INR.
    """

    cache_key = f"stock:{symbol.upper()}"
    cached = _cache_get(cache_key)
    if cached:
        logger.debug("Cache hit: %s", cache_key)
        return cached
    
    try:
        kite = _kite()
        kite_sym = _kite_symbol(symbol)
        quote = kite.quote([kite_sym])[kite_sym]
        ohlc = quote.get("ohlc", {})
        
        data = {
            "symbol": symbol.upper(),
            "company_name": kite_sym.split(":")[1],
            "exchange": kite_sym.split(":")[0],
            "current_price": quote.get("last_price"),
            "previous_close": ohlc.get("close"),
            "day_open": ohlc.get("open"),
            "day_high": ohlc.get("high"),
            "day_low": ohlc.get("low"),
            "volume": quote.get("volume"),
            "change": quote.get("net_change"),
            "upper_circuit": quote.get("upper_circuit_limit"),
            "lower_circuit": quote.get("lower_circuit_limit"),
            "52_week_high": quote.get("upper_circuit_limit"),
            "52_week_low": quote.get("lower_circuit_limit"),
            "currency": "INR",
            "source": "Zerodha Kite Connect",
            "fetched_at": datetime.now().isoformat(),
        }

        result = json.dumps(data, default=str)
        _cache_set(cache_key, result)
        return result
    
    except Exception as e:
        return json.dumps({
            "error": f"Failed to fetch data for {symbol}: {str(e)}",
            "symbol": symbol.upper(),
            "source": "Zerodha Kite Connect",
        })

@tool
def get_historical_prices(symbol: str, period: str = "3mo") -> str:
    """Fetch historical stock price data for charting.

    Use this tool when the user asks about:
    - Stock performance over time
    - Price trends, charts, or historical comparison
    - Quarter-over-quarter or year-over-year performance

    Args:
        symbol: NSE/BSE stock ticker symbol (e.g., "RELIANCE.NS", "TCS.NS")
        period: Time period — "1mo", "3mo", "6mo", "1y", "2y", "5y" (default: "3mo")

    Returns:
        JSON string with date-price data points for charting.
    """
    cache_key = f"hist:{symbol.upper()}:{period}"
    
    cached = _cache_get(cache_key)
    if cached:
        logger.debug("Cache hit: %s", cache_key)
        return cached

    try:
        kite = _kite()
        kite_sym = _kite_symbol(symbol)
        exchange = kite_sym.split(":")[0]
        tradingsymbol = kite_sym.split(":")[1] 

        instruments = kite.instruments(exchange)
        token = next(
            (i["instrument_token"] for i in instruments if i["tradingsymbol"] == tradingsymbol),
            None,
        )
        if not token:
            return json.dumps({"error": f"Instrument not found: {symbol}", "symbol": symbol})

        period_days = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730, "5y": 1825}
        days = period_days.get(period, 90)
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)

        hist = kite.historical_data(token, from_date, to_date, "day")

        prices = [
            {
                "date": row["date"].strftime("%Y-%m-%d"),
                "open": round(row["open"], 2),
                "high": round(row["high"], 2),
                "low": round(row["low"], 2),
                "close": round(row["close"], 2),
                "volume": int(row["volume"]),
            }
            for row in hist
        ]

        result = json.dumps({
            "symbol": symbol.upper(),
            "period": period,
            "data_points": len(prices),
            "prices": prices,
            "source": "Zerodha Kite Connect",
            "fetched_at": datetime.now().isoformat(),
        })
        _cache_set(cache_key, result)
        return result

    except Exception as e:
        return json.dumps({
            "error": f"Failed to fetch history for {symbol}: {str(e)}",
            "symbol": symbol.upper(),
            "source": "Zerodha Kite Connect",
        })


