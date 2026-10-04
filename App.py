import streamlit as st
import requests
import html
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

# ============================================================
# SOL RADAR // V6
# Stable Streamlit version
# No Plotly
# No triple-quoted strings
# ============================================================

st.set_page_config(
    page_title="SOL RADAR // V6",
    page_icon="🟣",
    layout="wide",
)

TIMEOUT = 5
HEADERS = {"User-Agent": "SOL-RADAR-V6/1.0"}

# ============================================================
# TELEGRAM
#
# Streamlit Cloud -> Manage app -> Settings -> Secrets
#
# [telegram]
# token = "YOUR_NEW_BOT_TOKEN"
# chat_id = "YOUR_CHAT_ID"
#
# NO pongas el token dentro de este archivo.
# ============================================================

def get_secret(section, key):
    try:
        value = st.secrets[section][key]
        return str(value).strip()
    except Exception:
        return ""


TELEGRAM_TOKEN = get_secret("telegram", "token")
TELEGRAM_CHAT_ID = get_secret("telegram", "chat_id")


# ============================================================
# GENERAL HELPERS
# ============================================================

def api_json(url, params=None, timeout=TIMEOUT):
    try:
        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=timeout,
        )

        if response.status_code != 200:
            return None

        return response.json()

    except Exception:
        return None


def clamp(value, low=0, high=100):
    return max(low, min(high, float(value)))


def fmt_price(value):
    if value is None:
        return "N/D"

    if value >= 1000:
        return f"${value:,.0f}"

    if value >= 1:
        return f"${value:,.2f}"

    return f"${value:,.5f}"


def clean_text(value):
    if not value:
        return ""

    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


# ============================================================
# MARKET DATA - BINANCE
# ============================================================

def get_ticker(symbol):
    data = api_json(
        "https://api.binance.com/api/v3/ticker/24hr",
        {"symbol": symbol},
    )

    if not data:
        return None

    try:
        return {
            "price": float(data["lastPrice"]),
            "change": float(data["priceChangePercent"]),
            "volume": float(data["quoteVolume"]),
            "high": float(data["highPrice"]),
            "low": float(data["lowPrice"]),
        }

    except Exception:
        return None


def get_klines(
    symbol="SOLUSDT",
    interval="1h",
    limit=200,
):
    data = api_json(
        "https://api.binance.com/api/v3/klines",
        {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        },
    )

    if isinstance(data, list):
        return data

    return []


# ============================================================
# TECHNICAL INDICATORS
# ============================================================

def sma(values, period):
    if len(values) < period:
        return None

    return sum(values[-period:]) / period


def ema(values, period):
    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)

    result = sum(values[:period]) / period

    for price in values[period:]:
        result = (
            (price - result) * multiplier
            + result
        )

    return result


def rsi(values, period=14):
    if len(values) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(values)):

        difference = (
            values[i]
            - values[i - 1]
        )

        gains.append(
            max(difference, 0)
        )

        losses.append(
            max(-difference, 0)
        )

    avg_gain = (
        sum(gains[-period:])
        / period
    )

    avg_loss = (
        sum(losses[-period:])
        / period
    )

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss

    return 100 - (
        100 / (1 + rs)
    )


def macd(values):
    if len(values) < 35:
        return None, None

    fast = ema(values, 12)
    slow = ema(values, 26)

    if fast is None or slow is None:
        return None, None

    macd_line = fast - slow

    return macd_line, None


def technical_vector(candles):

    if len(candles) < 60:

        return {
            "score": 0,
            "rsi": None,
            "sma20": None,
            "sma50": None,
            "ema20": None,
            "macd": None,
            "volume_ratio": None,
            "prices": [],
        }

    closes = [
        float(x[4])
        for x in candles
    ]

    volumes = [
        float(x[5])
        for x in candles
    ]

    last = closes[-1]

    sma20 = sma(
        closes,
        20,
    )

    sma50 = sma(
        closes,
        50,
    )

    ema20 = ema(
        closes,
        20,
    )

    current_rsi = rsi(
        closes,
        14,
    )

    macd_line, _ = macd(
        closes
    )

    average_volume = (
        sum(volumes[-20:])
        / 20
    )

    if average_volume:
        volume_ratio = (
            volumes[-1]
            / average_volume
        )
    else:
        volume_ratio = 1

    score = 0

    # Precio frente a SMA20
    if sma20 is not None:

        if last > sma20:
            score += 10
        else:
            score -= 10

    # Precio frente a SMA50
    if sma50 is not None:

        if last > sma50:
            score += 12
        else:
            score -= 12

    # Cruce SMA20 / SMA50
    if (
        sma20 is not None
        and sma50 is not None
    ):

        if sma20 > sma50:
            score += 10
        else:
            score -= 10

    # EMA20
    if ema20 is not None:

        if last > ema20:
            score += 6
        else:
            score -= 6

    # RSI
    if current_rsi is not None:

        if 52 <= current_rsi <= 68:
            score += 8

        elif current_rsi >= 75:
            score -= 8

        elif current_rsi <= 30:
            score += 5

    # MACD
    if macd_line is not None:

        if macd_line > 0:
            score += 6
        else:
            score -= 6

    # Volumen
    if volume_ratio >= 1.25:

        if last >= (
            sma20
            if sma20 is not None
            else last
        ):
            score += 5
        else:
            score -= 5

    return {
        "score": score,
        "rsi": current_rsi,
        "sma20": sma20,
        "sma50": sma50,
        "ema20": ema20,
        "macd": macd_line,
        "volume_ratio": volume_ratio,
        "prices": closes[-100:],
    }


# ============================================================
# FEAR & GREED
# ============================================================

def get_fear_greed():

    data = api_json(
        "https://api.alternative.me/fng/?limit=1"
    )

    try:

        item = data["data"][0]

        return {
            "value": int(
                item["value"]
            ),
            "label": item[
                "value_classification"
            ],
        }

    except Exception:

        return {
            "value": None,
            "label": "N/D",
        }


# ============================================================
# GLOBAL MARKET
# ============================================================

def get_global_market():

    data = api_json(
        "https://api.coingecko.com/api/v3/global"
    )

    try:

        obj = data["data"]

        return {
            "btc_dominance": float(
                obj[
                    "market_cap_percentage"
                ]["btc"]
            ),
            "change": float(
                obj[
                    "market_cap_change_percentage_24h_usd"
                ]
            ),
        }

    except Exception:

        return {
            "btc_dominance": None,
            "change": None,
        }


# ============================================================
# NEWS ENGINE
# ============================================================

NEWS_QUERIES = [
    "Solana SOL crypto",
    "Solana ETF institutional",
    "Solana network upgrade",
    "SEC crypto regulation",
    "Federal Reserve crypto interest rates",
    "Bitcoin crypto market",
    "crypto hack exploit liquidation",
    "tariffs inflation markets crypto",
]


POSITIVE_TERMS = [
    "approval",
    "approved",
    "etf",
    "inflow",
    "bullish",
    "adoption",
    "surge",
    "rally",
    "growth",
    "rate cut",
    "institutional",
    "investment",
    "partnership",
    "integration",
    "record",
    "upgrade",
    "launch",
    "positive",
]


NEGATIVE_TERMS = [
    "hack",
    "exploit",
    "ban",
    "lawsuit",
    "dump",
    "crash",
    "collapse",
    "war",
    "tariff",
    "inflation",
    "hawkish",
    "liquidation",
    "fraud",
    "attack",
    "drain",
    "recession",
    "outflow",
    "negative",
    "delay",
]


def classify_news(title):

    low = title.lower()

    positive = sum(
        term in low
        for term in POSITIVE_TERMS
    )

    negative = sum(
        term in low
        for term in NEGATIVE_TERMS
    )

    if positive > negative:
        return "POSITIVE"

    if negative > positive:
        return "NEGATIVE"

    return "NEUTRAL"


def fetch_news(query):

    url = (
        "https://news.google.com/rss/search?q="
        + quote_plus(query)
        + "&hl=en-US&gl=US&ceid=US:en"
    )

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
        )

        if response.status_code != 200:
            return []

        root = ET.fromstring(
            response.content
        )

        result = []

        items = root.findall(
            "./channel/item"
        )[:7]

        for item in items:

            title = clean_text(
                item.findtext(
                    "title",
                    "",
                )
            )

            link = item.findtext(
                "link",
                "",
            )

            pub_date = item.findtext(
                "pubDate",
                "",
            )

            if not title:
                continue

            result.append(
                {
                    "title": title,
                    "link": link,
                    "date": pub_date,
                    "sentiment": classify_news(
                        title
                    ),
                }
            )

        return result

    except Exception:

        return []


def collect_news():

    all_items = []

    with ThreadPoolExecutor(
        max_workers=8
    ) as executor:

        futures = [
            executor.submit(
                fetch_news,
                query,
            )
            for query in NEWS_QUERIES
        ]

        for future in as_completed(
            futures
        ):

            try:

                all_items.extend(
                    future.result()
                )

            except Exception:
                pass

    unique = {}

    for item in all_items:

        key = item[
            "title"
        ].lower()

        if key not in unique:
            unique[key] = item

    return list(
        unique.values()
    )[:35]


def news_vector(news):

    score = 0

    for item in news:

        if (
            item["sentiment"]
            == "POSITIVE"
        ):
            score += 2

        elif (
            item["sentiment"]
            == "NEGATIVE"
        ):
            score -= 2

    return max(
        -20,
        min(
            20,
            score,
        ),
    )


# ============================================================
# SOL VS BTC
# ============================================================

def relative_strength(
    sol,
    btc,
):

    if not sol or not btc:
        return 0

    sol_change = sol[
        "change"
    ]

    btc_change = btc[
        "change"
    ]

    difference = (
        sol_change
        - btc_change
    )

    if difference > 3:
        return 7

    if difference > 1:
        return 4

    if difference < -3:
        return -7

    if difference < -1:
        return -4

    return 0


# ============================================================
# COMPLETE SCAN
# ============================================================

def run_scan():

    start = datetime.now(
        timezone.utc
    )

    jobs = {
        "sol": lambda: get_ticker(
            "SOLUSDT"
        ),
        "btc": lambda: get_ticker(
            "BTCUSDT"
        ),
        "eth": lambda: get_ticker(
            "ETHUSDT"
        ),
        "candles": lambda: get_klines(
            "SOLUSDT",
            "
