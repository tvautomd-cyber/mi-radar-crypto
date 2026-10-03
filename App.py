import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import xml.etree.ElementTree as ET
from urllib.parse import quote
from datetime import datetime, timezone

# ============================================================
# QUANTUM SOLANA RADAR
# SOL ONLY - Streamlit
# ============================================================

st.set_page_config(
    page_title="QUANTUM // SOL RADAR",
    page_icon="🟣",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------- CONFIG ----------------------------

BINANCE = "https://api.binance.com/api/v3"
COINGECKO = "https://api.coingecko.com/api/v3"
FEAR_GREED = "https://api.alternative.me/fng/"

TELEGRAM_TOKEN = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")
TELEGRAM_USERNAME = st.secrets.get(
    "TELEGRAM_BOT_USERNAME",
    "Mycrypto_best_bot",
)

# -------------------------- STYLE ----------------------------

st.markdown(
    """
<style>
.stApp {
    background:
        radial-gradient(circle at 85% 5%, rgba(130,55,255,.13), transparent 30%),
        radial-gradient(circle at 5% 95%, rgba(0,255,150,.05), transparent 28%),
        #050607;
    color: #d8d8d8;
    font-family: Consolas, "Courier New", monospace;
}

.block-container {
    max-width: 1600px;
    padding-top: 1.2rem;
}

h1, h2, h3, p, div, span {
    font-family: Consolas, "Courier New", monospace;
}

.q-title {
    font-size: 2.2rem;
    font-weight: 900;
    letter-spacing: 4px;
    color: #ffffff;
}

.q-subtitle {
    color: #666b72;
    letter-spacing: 2px;
    font-size: .7rem;
}

.panel {
    background: linear-gradient(145deg, #0b0d10, #08090b);
    border: 1px solid #20242a;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 14px;
}

.panel-purple {
    border-color: #6d35a8;
    box-shadow: 0 0 25px rgba(140,60,255,.10);
}

.label {
    color: #666b72;
    font-size: .65rem;
    letter-spacing: 1.5px;
}

.big {
    color: #fff;
    font-size: 2rem;
    font-weight: 900;
}

.score {
    font-size: 4rem;
    font-weight: 900;
    line-height: 1;
}

.green {
    color: #00ff88 !important;
}

.red {
    color: #ff405c !important;
}

.yellow {
    color: #ffc857 !important;
}

.purple {
    color: #a96cff !important;
}

.cyan {
    color: #00d9ff !important;
}

.muted {
    color: #666b72 !important;
}

.progress {
    width: 100%;
    height: 10px;
    background: #171a1f;
    border-radius: 10px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: #00ff88;
}

.factor {
    border-bottom: 1px solid #1b1e23;
    padding: 9px 0;
    font-size: .78rem;
}

.factor:last-child {
    border-bottom: 0;
}

.news {
    background: #090b0e;
    border-left: 3px solid #63339a;
    padding: 10px;
    margin-bottom: 8px;
    border-radius: 3px;
}

.news-title {
    color: #dddddd;
    font-size: .78rem;
    line-height: 1.4;
}

.news-meta {
    color: #666b72;
    font-size: .62rem;
    margin-top: 5px;
}

.alertbox {
    background: #0d0a13;
    border-left: 3px solid #a96cff;
    padding: 12px;
    border-radius: 4px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ------------------------- HELPERS ---------------------------

def get_json(url, params=None, timeout=12):
    try:
        r = requests.get(
            url,
            params=params,
            timeout=timeout,
            headers={"User-Agent": "Quantum-Solana-Radar/1.0"},
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


# ----------------------- MARKET DATA --------------------------

@st.cache_data(ttl=30)
def get_market():
    data = get_json(
        f"{COINGECKO}/simple/price",
        {
            "ids": "solana,bitcoin,ethereum",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
        },
    )
    return data or {}


@st.cache_data(ttl=60)
def get_candles(interval="1h", limit=250):
    data = get_json(
        f"{BINANCE}/klines",
        {
            "symbol": "SOLUSDT",
            "interval": interval,
            "limit": limit,
        },
    )

    if not isinstance(data, list):
        return pd.DataFrame()

    columns = [
        "time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_volume",
        "trades",
        "buy_base",
        "buy_quote",
        "ignore",
    ]

    try:
        df = pd.DataFrame(data, columns=columns)

        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df["time"] = pd.to_datetime(df["time"], unit="ms")

        return df

    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_fear_greed():
    data = get_json(
        FEAR_GREED,
        {"limit": 1},
    )

    try:
        item = data["data"][0]

        return {
            "value": int(item["value"]),
            "classification": item["value_classification"],
        }

    except Exception:
        return {
            "value": None,
            "classification": "N/A",
        }


# --------------------------- NEWS -----------------------------

@st.cache_data(ttl=300)
def get_news():

    query = (
        "Solana OR SOL crypto OR Bitcoin crypto OR Ethereum crypto "
        "OR crypto ETF OR SEC crypto OR Federal Reserve OR Fed "
        "OR inflation OR tariffs OR Trump crypto OR regulation"
    )

    url = (
        "https://news.google.com/rss/search?"
        + "q=" + quote(query)
        + "&hl=en-US&gl=US&ceid=US:en"
    )

    try:

        response = requests.get(
            url,
            timeout=12,
            headers={
                "User-Agent": "Quantum-Solana-Radar/1.0"
            },
        )

        response.raise_for_status()

        root = ET.fromstring(response.text)

    except Exception:

        return []

    articles = []

    for item in root.findall(".//item")[:25]:

        title_node = item.find("title")
        link_node = item.find("link")
        date_node = item.find("pubDate")
        source_node = item.find("source")

        title = (
            title_node.text
            if title_node is not None
            else "Unknown"
        )

        link = (
            link_node.text
            if link_node is not None
            else ""
        )

        pub_date = (
            date_node.text
            if date_node is not None
            else ""
        )

        source = (
            source_node.text
            if source_node is not None
            else "News"
        )

        articles.append(
            {
                "title": title or "Unknown",
                "link": link or "",
                "date": pub_date or "",
                "source": source or "News",
            }
        )

    return articles


def score_news(articles):

    bullish = [
        "etf",
        "approval",
        "approved",
        "adoption",
        "inflow",
        "bullish",
        "buy",
        "partnership",
        "integration",
        "launch",
        "institutional",
        "growth",
        "record",
        "upgrade",
        "positive",
        "staking",
        "investment",
    ]

    bearish = [
        "hack",
        "exploit",
        "attack",
        "outflow",
        "bearish",
        "sell",
        "lawsuit",
        "ban",
        "fraud",
        "collapse",
        "liquidation",
        "shutdown",
        "halt",
        "negative",
        "crash",
        "sanction",
        "tariff",
        "inflation",
    ]

    total = 0
    result = []

    for article in articles:

        text = article["title"].lower()

        up = sum(
            word in text
            for word in bullish
        )

        down = sum(
            word in text
            for word in bearish
        )

        score = max(
            -5,
            min(5, up - down)
        )

        total += score

        copy = article.copy()
        copy["score"] = score

        result.append(copy)

    if not result:
        return 0.0, []

    average = total / len(result)

    return (
        max(-10.0, min(10.0, average * 3.0)),
        result,
    )


# --------------------- TECHNICAL ANALYSIS ---------------------

def rsi(series, period=14):

    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss.replace(
        0,
        np.nan,
    )

    return 100 - (
        100 / (1 + rs)
    )


def indicators(df):

    if df.empty:
        return df

    out = df.copy()

    out["EMA20"] = (
        out["close"]
        .ewm(span=20, adjust=False)
        .mean()
    )

    out["EMA50"] = (
        out["close"]
        .ewm(span=50, adjust=False)
        .mean()
    )

    out["EMA200"] = (
        out["close"]
        .ewm(span=200, adjust=False)
        .mean()
    )

    out["RSI"] = rsi(
        out["close"]
    )

    out["VOLMA20"] = (
        out["volume"]
        .rolling(20)
        .mean()
    )

    return out


def technical_score(df):

    if df.empty or len(df) < 50:

        return 0.0, []

    row = df.iloc[-1]

    score = 0.0
    factors = []

    close = float(row["close"])
    ema20 = float(row["EMA20"])
    ema50 = float(row["EMA50"])
    ema200 = float(row["EMA200"])

    current_rsi = (
        float(row["RSI"])
        if pd.notna(row["RSI"])
        else 50.0
    )

    volume = float(row["volume"])

    volume_ma = (
        float(row["VOLMA20"])
        if pd.notna(row["VOLMA20"])
        else volume
    )

    if close > ema20:

        score += 10

        factors.append(
            ("🟢", "Precio sobre EMA20", "+10")
        )

    else:

        score -= 10

        factors.append(
            ("🔴", "Precio bajo EMA20", "-10")
        )

    if ema20 > ema50:

        score += 10

        factors.append(
            ("🟢", "EMA20 sobre EMA50", "+10")
        )

    else:

        score -= 10

        factors.append(
            ("🔴", "EMA20 bajo EMA50", "-10")
        )

    if close > ema200:

        score += 8

        factors.append(
            ("🟢", "Precio sobre EMA200", "+8")
        )

    else:

        score -= 8

        factors.append(
            ("🔴", "Precio bajo EMA200", "-8")
        )

    if 50 <= current_rsi <= 68:

        score += 8

        factors.append(
            (
                "🟢",
                f"RSI saludable {current_rsi:.1f}",
                "+8",
            )
        )

    elif current_rsi >= 75:

        score -= 8

        factors.append(
            (
                "🔴",
                f"RSI sobrecomprado {current_rsi:.1f}",
                "-8",
            )
        )

    elif current_rsi <= 30:

        score += 5

        factors.append(
            (
                "🟡",
                f"RSI sobrevendido {current_rsi:.1f}",
                "+5",
            )
        )

    else:

        factors.append(
            (
                "⚪",
                f"RSI neutral {current_rsi:.1f}",
                "0",
            )
        )

    if volume > volume_ma:

        score += 6

        factors.append(
            (
                "🟢",
                "Volumen sobre media 20",
                "+6",
            )
        )

    else:

        score -= 3

        factors.append(
            (
                "🔴",
                "Volumen bajo media 20",
                "-3",
            )
        )

    return (
        max(-50.0, min(50.0, score)),
        factors,
    )


def market_score(market):

    sol = market.get(
        "solana",
        {}
    )

    btc = market.get(
        "bitcoin",
        {}
    )

    sol_change = float(
        sol.get("usd_24h_change") or 0
    )

    btc_change = float(
        btc.get("usd_24h_change") or 0
    )

    score = 0.0
    factors = []

    if sol_change >= 3:

        score += 12

        factors.append(
            (
                "🟢",
                f"SOL momentum {sol_change:+.2f}%",
                "+12",
            )
        )

    elif sol_change >= 1:

        score += 6

        factors.append(
            (
                "🟢",
                f"SOL momentum {sol_change:+.2f}%",
                "+6",
            )
        )

    elif sol_change <= -3:

        score -= 12

        factors.append(
            (
                "🔴",
                f"SOL momentum {sol_change:+.2f}%",
                "-12",
            )
        )

    elif sol_change <= -1:

        score -= 6

        factors.append(
            (
                "🔴",
                f"SOL momentum {sol_change:+.2f}%",
                "-6",
            )
        )

    else:

        factors.append(
            (
                "⚪",
                f"SOL 24h {sol_change:+.2f}%",
                "0",
            )
        )

    if btc_change >= 2:

        score += 10

        factors.append(
            (
                "🟢",
                f"BTC fuerte {btc_change:+.2f}%",
                "+10",
            )
        )

    elif btc_change >= 0.5:

        score += 5

        factors.append(
            (
                "🟢",
                f"BTC positivo {btc_change:+.2f}%",
                "+5",
            )
        )

    elif btc_change <= -2:

        score -= 10

        factors.append(
            (
                "🔴",
                f"BTC débil {btc_change:+.2f}%",
                "-10",
            )
        )

    elif btc_change <= -0.5:

        score -= 5

        factors.append(
            (
                "🔴",
                f"BTC negativo {btc_change:+.2f}%",
                "-5",
            )
        )

    else:

        factors.append(
            (
                "⚪",
                f"BTC neutral {btc_change:+.2f}%",
                "0",
            )
        )

    return (
        max(-50.0, min(50.0, score)),
        factors,
    )


def sentiment_score(fg):

    value = fg.get("value")

    if value is None:

        return (
            0.0,
            [
                (
                    "⚪",
                    "Fear & Greed no disponible",
                    "0",
                )
            ],
        )

    if value >= 75:

        return (
            7.0,
            [
                (
                    "🟢",
                    f"Fear & Greed {value} - greed extremo",
                    "+7",
                )
            ],
        )

    if value >= 55:

        return (
            4.0,
            [
                (
                    "🟢",
                    f"Fear & Greed {value} - greed",
                    "+4",
                )
            ],
        )

    if value <= 25:

        return (
            -7.0,
            [
                (
                    "🔴",
                    f"Fear & Greed {value} - miedo extremo",
                    "-7",
                )
            ],
        )

    if value <= 45:

        return (
            -4.0,
            [
                (
                    "🟡",
                    f"Fear & Greed {value} - miedo",
                    "-4",
                )
            ],
        )

    return (
        0.0,
        [
            (
                "⚪",
                f"Fear & Greed {value} - neutral",
                "0",
            )
        ],
    )


# -------------------------- TELEGRAM --------------------------

def telegram_send(message):

    if not TELEGRAM_TOKEN:

        return (
            False,
            "Falta TELEGRAM_BOT_TOKEN en Streamlit Secrets.",
        )

    if not TELEGRAM_CHAT_ID:

        return (
            False,
            "Falta TELEGRAM_CHAT_ID en Streamlit Secrets.",
        )

    url = (
        "https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/sendMessage"
    )

    try:

        response = requests.post(
            url,
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
            },
            timeout=12,
        )

        if response.ok:

            return (
                True,
                "Mensaje enviado.",
            )

        return (
            False,
            response.text,
        )

    except Exception as exc:

        return (
            False,
            str(exc),
        )


def telegram_get_chat_id():

    if not TELEGRAM_TOKEN:

        return (
            None,
            "Falta TELEGRAM_BOT_TOKEN.",
        )

    url = (
        "https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/getUpdates"
    )

    try:

        response = requests.get(
            url,
            timeout=12,
        )

        if not response.ok:

            return (
                None,
                response.text,
            )

        updates = response.json().get(
            "result",
            []
        )

        if not updates:

            return (
                None,
                "Envía /start al bot y vuelve a pulsar el botón.",
            )

        for update in reversed(updates):

            message = update.get(
                "message"
            )

            if message and message.get("chat"):

                return (
                    str(
                        message["chat"]["id"]
                    ),
                    "Chat ID encontrado.",
                )

        return (
            None,
            "No se encontró un chat.",
        )

    except Exception as exc:

        return (
            None,
            str(exc),
        )


def make_alert(
    price,
    change,
    up,
    down,
    confidence,
    vector,
    score,
    factors,
):

    top = "\n".join(
        f"{icon} {text} {value}"
        for icon, text, value
        in factors[:7]
    )

    return (
        "🚨 QUANTUM SOL ALERT\n\n"
        f"SOL: ${price:,.2f}\n"
        f"24H: {change:+.2f}%\n\n"
        f"🟢 UPSIDE: {up}%\n"
        f"🔴 DOWNSIDE: {down}%\n"
        f"🎯 CONFIDENCE: {confidence}%\n"
        f"📡 VECTOR: {vector}\n"
        f"MODEL SCORE: {score:+.1f}\n\n"
        "TOP FACTORS\n"
        f"{top}\n\n"
        "Indicador cuantitativo. "
        "No garantiza el movimiento futuro."
    )


# ------------------------- LOAD DATA --------------------------

market = get_market()

df = get_candles()

df = indicators(df)

fear_greed = get_fear_greed()

news = get_news()

news_s, news_items = score_news(
    news
)

tech_s, tech_factors = technical_score(
    df
)

market_s, market_factors = market_score(
    market
)

sent_s, sent_factors = sentiment_score(
    fear_greed
)


# ----------------------- GLOBAL MODEL -------------------------

model_score = (
    tech_s * 0.45
    + market_s * 0.30
    + sent_s * 0.15
    + news_s * 0.10
)

model_score = max(
    -100.0,
    min(100.0, model_score),
)

upside = int(
    round(
        50 + model_score / 2
    )
)

upside = max(
    5,
    min(95, upside),
)

downside = 100 - upside


# ------------------------- CONFIDENCE -------------------------

confidence = 45

if market:
    confidence += 15

if not df.empty:
    confidence += 15

if len(df) >= 200:
    confidence += 5

if fear_greed.get("value") is not None:
    confidence += 5

if len(news) >= 5:
    confidence += 10

confidence = max(
    25,
    min(95, confidence),
)


# --------------------------- VECTOR ----------------------------

if upside >= 75:

    vector = "STRONG BULLISH"
    vector_class = "green"

elif upside >= 60:

    vector = "BULLISH"
    vector_class = "green"

elif upside <= 25:

    vector = "STRONG BEARISH"
    vector_class = "red"

elif upside <= 40:

    vector = "BEARISH"
    vector_class = "red"

else:

    vector = "NEUTRAL"
    vector_class = "yellow"


all_factors = (
    tech_factors
    + market_factors
    + sent_factors
)


