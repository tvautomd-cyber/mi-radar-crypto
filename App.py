import streamlit as st
import requests
import html
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

# ============================================================
# SOL RADAR V5 - FAST / FAIL-SAFE / NO PLOTLY
# ============================================================

st.set_page_config(
    page_title="SOL RADAR // QUANTUM",
    page_icon="🟣",
    layout="wide",
)

TIMEOUT = 4
HEADERS = {"User-Agent": "SOL-RADAR/5.0"}

# ============================================================
# TELEGRAM - USA STREAMLIT SECRETS
#
# Streamlit Cloud > Manage app > Settings > Secrets
#
# [telegram]
# token = "TU_NUEVO_TOKEN"
# chat_id = "TU_CHAT_ID"
#
# NO pongas el token directamente aquí.
# ============================================================

def secret(section, key):
    try:
        value = st.secrets[section][key]
        return str(value).strip()
    except Exception:
        return ""


TELEGRAM_TOKEN = secret("telegram", "token")
TELEGRAM_CHAT_ID = secret("telegram", "chat_id")


# ============================================================
# HELPERS
# ============================================================

def clamp(value, low=5, high=95):
    return max(low, min(high, int(round(value))))


def money(value):
    if value is None:
        return "N/D"

    if abs(value) >= 1000:
        return f"${value:,.0f}"

    return f"${value:,.4f}"


def clean_text(value):
    if not value:
        return ""

    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def get_json(url, params=None, timeout=TIMEOUT):
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


# ============================================================
# MARKET DATA
# ============================================================

def get_ticker(symbol):
    data = get_json(
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
        }

    except Exception:
        return None


def get_candles():
    data = get_json(
        "https://api.binance.com/api/v3/klines",
        {
            "symbol": "SOLUSDT",
            "interval": "1h",
            "limit": 100,
        },
    )

    if isinstance(data, list):
        return data

    return []


# ============================================================
# TECHNICAL ANALYSIS
# ============================================================

def technical_analysis(candles):

    if len(candles) < 50:
        return {
            "score": 0,
            "rsi": None,
            "sma20": None,
            "sma50": None,
            "volume_ratio": None,
            "prices": [],
        }

    closes = [float(x[4]) for x in candles]
    volumes = [float(x[5]) for x in candles]

    sma20 = sum(closes[-20:]) / 20
    sma50 = sum(closes[-50:]) / 50

    gains = []
    losses = []

    for i in range(1, len(closes)):
        difference = closes[i] - closes[i - 1]

        gains.append(max(difference, 0))
        losses.append(max(-difference, 0))

    avg_gain = sum(gains[-14:]) / 14
    avg_loss = sum(losses[-14:]) / 14

    if avg_loss == 0:
        rsi = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))

    avg_volume = sum(volumes[-20:]) / 20

    if avg_volume:
        volume_ratio = volumes[-1] / avg_volume
    else:
        volume_ratio = 1.0

    score = 0

    # Precio vs SMA20
    if closes[-1] > sma20:
        score += 10
    else:
        score -= 10

    # Tendencia SMA20 vs SMA50
    if sma20 > sma50:
        score += 12
    else:
        score -= 12

    # RSI
    if 50 <= rsi <= 68:
        score += 8

    elif rsi > 75:
        score -= 8

    elif rsi < 30:
        score += 6

    # Volumen
    if volume_ratio > 1.20:

        if closes[-1] > sma20:
            score += 8
        else:
            score -= 5

    return {
        "score": score,
        "rsi": rsi,
        "sma20": sma20,
        "sma50": sma50,
        "volume_ratio": volume_ratio,
        "prices": closes,
    }


# ============================================================
# FEAR & GREED
# ============================================================

def get_fear_greed():

    data = get_json(
        "https://api.alternative.me/fng/",
        {"limit": 1},
    )

    try:
        item = data["data"][0]

        return {
            "value": int(item["value"]),
            "label": item["value_classification"],
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

    data = get_json(
        "https://api.coingecko.com/api/v3/global"
    )

    try:
        obj = data["data"]

        return {
            "btc_dominance": float(
                obj["market_cap_percentage"]["btc"]
            ),
            "change": float(
                obj["market_cap_change_percentage_24h_usd"]
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
    "SEC crypto regulation",
    "Federal Reserve interest rates crypto",
    "crypto market liquidation hack",
    "Bitcoin Ethereum global markets",
]


POSITIVE_WORDS = [
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
]


NEGATIVE_WORDS = [
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
]


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

        root = ET.fromstring(response.content)

        results = []

        for item in root.findall("./channel/item")[:5]:

            title = clean_text(
                item.findtext("title", "")
            )

            link = item.findtext("link", "")

            pub_date = item.findtext(
                "pubDate",
                "",
            )

            if not title:
                continue

            low = title.lower()

            positive = sum(
                word in low
                for word in POSITIVE_WORDS
            )

            negative = sum(
                word in low
                for word in NEGATIVE_WORDS
            )

            if positive > negative:
                sentiment = "POSITIVE"

            elif negative > positive:
                sentiment = "NEGATIVE"

            else:
                sentiment = "NEUTRAL"

            results.append(
                {
                    "title": title,
                    "link": link,
                    "date": pub_date,
                    "sentiment": sentiment,
                }
            )

        return results

    except Exception:
        return []


def collect_news():

    all_news = []

    with ThreadPoolExecutor(
        max_workers=6
    ) as executor:

        jobs = [
            executor.submit(
                fetch_news,
                query,
            )
            for query in NEWS_QUERIES
        ]

        for job in as_completed(jobs):

            try:
                all_news.extend(
                    job.result()
                )

            except Exception:
                pass

    unique = {}

    for item in all_news:

        key = item["title"].lower()

        if key not in unique:
            unique[key] = item

    return list(unique.values())[:25]


def news_score(news):

    score = 0

    for item in news:

        if item["sentiment"] == "POSITIVE":
            score += 2

        elif item["sentiment"] == "NEGATIVE":
            score -= 2

    return max(
        -20,
        min(20, score),
    )


# ============================================================
# COMPLETE SCAN
# ============================================================

def run_scan():

    start = datetime.now(timezone.utc)

    tasks = {
        "sol": lambda: get_ticker("SOLUSDT"),
        "btc": lambda: get_ticker("BTCUSDT"),
        "eth": lambda: get_ticker("ETHUSDT"),
        "candles": get_candles,
        "fear": get_fear_greed,
        "global": get_global_market,
        "news": collect_news,
    }

    results = {}

    with ThreadPoolExecutor(
        max_workers=7
    ) as executor:

        future_map = {
            executor.submit(
                function
            ): name

            for name, function in tasks.items()
        }

        for future in as_completed(
            future_map
        ):

            name = future_map[future]

            try:
                results[name] = future.result()

            except Exception:
                results[name] = None

    technical = technical_analysis(
        results.get("candles") or []
    )

    news = results.get("news") or []

    n_score = news_score(news)

    score = float(
        technical["score"]
    )

    score += n_score

    fear = results.get("fear") or {}

    fear_value = fear.get("value")

    if fear_value is not None:

        score += max(
            -7,
            min(
                7,
                (fear_value - 50) / 7,
            ),
        )

    global_data = (
        results.get("global") or {}
    )

    global_change = global_data.get(
        "change"
    )

    if global_change is not None:

        score += max(
            -6,
            min(
                6,
                global_change * 1.5,
            ),
        )

    up = clamp(
        50 + score
    )

    down = 100 - up

    confidence = clamp(
        50 + abs(score) * 1.5,
        50,
        92,
    )

    elapsed = (
        datetime.now(timezone.utc)
        - start
    ).total_seconds()

    return {
        "sol": results.get("sol"),
        "btc": results.get("btc"),
        "eth": results.get("eth"),
        "technical": technical,
        "fear": fear,
        "global": global_data,
        "news": news,
        "news_score": n_score,
        "score": score,
        "up": up,
        "down": down,
        "confidence": confidence,
        "elapsed": elapsed,
        "time": datetime.now(
            timezone.utc
        ).strftime("%H:%M:%S UTC"),
    }


# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(message):

    if (
        not TELEGRAM_TOKEN
        or not TELEGRAM_CHAT_ID
    ):
        return (
            False,
            "Telegram Secrets no configurados.",
        )

    try:

        url = (
            "https://api.telegram.org/bot"
            + TELEGRAM_TOKEN
            + "/sendMessage"
        )

        response = requests.post(
            url,
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
            },
            timeout=5,
        )

        data = response.json()

        if data.get("ok"):
            return True, ""

        return (
            False,
            data.get(
                "description",
                "Error de Telegram",
            ),
        )

    except Exception as exc:

        return False, str(exc)


# ============================================================
# VISUAL STYLE
# ============================================================

CSS = """
<style>

.stApp {

    background:
        radial-gradient(
            circle at 85% 5%,
            rgba(130,50,255,.18),
            transparent 28%
        ),

        radial-gradient(
            circle at 10% 30%,
            rgba(0,180,255,.07),
            transparent 25%
        ),

        #040609;

    color: #d9dce4;
}


.block-container {

    max-width: 1500px;

    padding-top: 1rem;
}


.radar-title {

    font-family:
        "Courier New",
        monospace;

    font-size: 2.4rem;

    font-weight: 900;

    color: #b86cff;

    text-shadow:
        0 0 14px
        rgba(150,70,255,.7);
}


.subtitle {

    font-family:
        "Courier New",
        monospace;

    color: #697284;

    letter-spacing: 2px;
}


.card {

    background:
        linear-gradient(
            145deg,
            #090c12,
            #12091c
        );

    border:
        1px solid #6230bd;

    border-radius: 16px;

    padding: 22px;

    box-shadow:
        0 0 30px
        rgba(110,40,255,.12);
}


.news {

    background: #080b10;

    border-left:
        3px solid #8b4dff;

    padding: 11px;

    margin-bottom: 7px;

    border-radius: 5px;
}


.news-positive {
    border-left-color: #00ff88;
}


.news-negative {
    border-left-color: #ff4260;
}


.small {

    color: #697284;

    font-size: .75rem;
}


.green {
    color: #00ff88 !important;
}


.red {
    color: #ff4260 !important;
}


.yellow {
    color: #ffc857 !important;
}


.purple {
    color: #b86cff !important;
}


.footer {

    text-align: center;
