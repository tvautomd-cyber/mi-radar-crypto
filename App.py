import streamlit as st
import requests
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
from urllib.parse import quote
from datetime import datetime, timezone


# ============================================================
# QUANTUM // SOLANA RADAR
# Stable Streamlit Edition
# ============================================================

st.set_page_config(
    page_title="QUANTUM // SOL RADAR",
    page_icon="🟣",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONFIGURATION
# ============================================================

BINANCE_API = "https://api.binance.com/api/v3"
COINGECKO_API = "https://api.coingecko.com/api/v3"
FEAR_GREED_API = "https://api.alternative.me/fng/"

TELEGRAM_TOKEN = st.secrets.get(
    "TELEGRAM_BOT_TOKEN",
    ""
)

TELEGRAM_CHAT_ID = st.secrets.get(
    "TELEGRAM_CHAT_ID",
    ""
)

TELEGRAM_USERNAME = st.secrets.get(
    "TELEGRAM_BOT_USERNAME",
    "Mycrypto_best_bot"
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background:
        radial-gradient(
            circle at 85% 5%,
            rgba(120,40,255,0.14),
            transparent 30%
        ),
        radial-gradient(
            circle at 10% 90%,
            rgba(0,255,150,0.05),
            transparent 30%
        ),
        #050607;

    color: #d8d8d8;
    font-family:
        Consolas,
        "Courier New",
        monospace;
}

.block-container {
    max-width: 1550px;
    padding-top: 1.2rem;
}

h1, h2, h3, p, div, span {
    font-family:
        Consolas,
        "Courier New",
        monospace;
}

.q-title {
    font-size: 2.2rem;
    font-weight: 900;
    letter-spacing: 4px;
    color: white;
}

.q-subtitle {
    color: #666b72;
    letter-spacing: 2px;
    font-size: .7rem;
}

.panel {
    background:
        linear-gradient(
            145deg,
            #0c0e11,
            #070809
        );

    border: 1px solid #20242a;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 14px;
}

.panel-purple {
    border-color: #7138aa;
    box-shadow:
        0 0 25px rgba(140,60,255,.10);
}

.label {
    color: #666b72;
    font-size: .65rem;
    letter-spacing: 1.5px;
}

.big {
    color: white;
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

.metric-box {
    background: #090b0e;
    border: 1px solid #1d2025;
    padding: 14px;
    border-radius: 7px;
}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# HTTP HELPER
# ============================================================

def get_json(url, params=None, timeout=12):

    try:

        response = requests.get(
            url,
            params=params,
            timeout=timeout,
            headers={
                "User-Agent":
                    "Quantum-Solana-Radar/1.0"
            }
        )

        response.raise_for_status()

        return response.json()

    except Exception:

        return None


# ============================================================
# MARKET DATA
# ============================================================

@st.cache_data(ttl=30)
def get_market():

    data = get_json(
        f"{COINGECKO_API}/simple/price",
        {
            "ids":
                "solana,bitcoin,ethereum",
            "vs_currencies":
                "usd",
            "include_24hr_change":
                "true",
            "include_24hr_vol":
                "true"
        }
    )

    return data or {}


@st.cache_data(ttl=60)
def get_candles():

    data = get_json(
        f"{BINANCE_API}/klines",
        {
            "symbol":
                "SOLUSDT",

            "interval":
                "1h",

            "limit":
                250
        }
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
        "ignore"
    ]

    try:

        df = pd.DataFrame(
            data,
            columns=columns
        )

        for column in [
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

        df["time"] = pd.to_datetime(
            df["time"],
            unit="ms"
        )

        return df

    except Exception:

        return pd.DataFrame()


# ============================================================
# FEAR & GREED
# ============================================================

@st.cache_data(ttl=300)
def get_fear_greed():

    data = get_json(
        FEAR_GREED_API,
        {
            "limit": 1
        }
    )

    try:

        item = data["data"][0]

        return {
            "value":
                int(item["value"]),

            "classification":
                item[
                    "value_classification"
                ]
        }

    except Exception:

        return {
            "value": None,
            "classification": "N/A"
        }


# ============================================================
# NEWS
# ============================================================

@st.cache_data(ttl=300)
def get_news():

    query = (
        "Solana OR SOL crypto OR Bitcoin "
        "OR crypto ETF OR SEC crypto OR "
        "Federal Reserve OR Fed OR inflation "
        "OR tariffs OR Trump crypto OR "
        "crypto regulation"
    )

    url = (
        "https://news.google.com/rss/search?"
        "q="
        + quote(query)
        + "&hl=en-US&gl=US&ceid=US:en"
    )

    try:

        response = requests.get(
            url,
            timeout=12,
            headers={
                "User-Agent":
                    "Quantum-Solana-Radar/1.0"
            }
        )

        response.raise_for_status()

        root = ET.fromstring(
            response.text
        )

    except Exception:

        return []

    articles = []

    for item in root.findall(
        ".//item"
    )[:25]:

        title_node = item.find(
            "title"
        )

        source_node = item.find(
            "source"
        )

        date_node = item.find(
            "pubDate"
        )

        title = (
            title_node.text
            if title_node is not None
            else "Unknown"
        )

        source = (
            source_node.text
            if source_node is not None
            else "News"
        )

        date = (
            date_node.text
            if date_node is not None
            else ""
        )

        articles.append(
            {
                "title":
                    title or "Unknown",

                "source":
                    source or "News",

                "date":
                    date or ""
            }
        )

    return articles


# ============================================================
# NEWS SENTIMENT
# ============================================================

def calculate_news_score(
    articles
):

    bullish_words = [
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
        "investment"
    ]

    bearish_words = [
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
        "inflation"
    ]

    total = 0

    results = []

    for article in articles:

        title = article[
            "title"
        ].lower()

        bullish = sum(
            word in title
            for word in bullish_words
        )

        bearish = sum(
            word in title
            for word in bearish_words
        )

        score = max(
            -5,
            min(
                5,
                bullish - bearish
            )
        )

        total += score

        copy = article.copy()

        copy["score"] = score

        results.append(copy)

    if not results:

        return 0.0, []

    average = (
        total / len(results)
    )

    return (
        max(
            -10,
            min(
                10,
                average * 3
            )
        ),
        results
    )


# ============================================================
# TECHNICAL INDICATORS
# ============================================================

def calculate_rsi(
    series,
    period=14
):

    delta = series.diff()

    gain = delta.clip(
        lower=0
    )

    loss = -delta.clip(
        upper=0
    )

    average_gain = (
        gain.rolling(period)
        .mean()
    )

    average_loss = (
        loss.rolling(period)
        .mean()
    )

    rs = (
        average_gain /
        average_loss.replace(
            0,
            np.nan
        )
    )

    return 100 - (
        100 / (1 + rs)
    )


def calculate_indicators(
    df
):

    if df.empty:

        return df

    result = df.copy()

    result["EMA20"] = (
        result["close"]
        .ewm(
            span=20,
            adjust=False
        )
        .mean()
    )

    result["EMA50"] = (
        result["close"]
        .ewm(
            span=50,
            adjust=False
        )
        .mean()
    )

    result["EMA200"] = (
        result["close"]
        .ewm(
            span=200,
            adjust=False
        )
        .mean()
    )

    result["RSI"] = (
        calculate_rsi(
            result["close"]
        )
    )

    result["VOLMA20"] = (
        result["volume"]
        .rolling(20)
        .mean()
    )

    return result


# ============================================================
# TECHNICAL SCORE
# ============================================================

def technical_score(df):

    if (
        df.empty
        or len(df) < 50
    ):

        return 0, []

    row = df.iloc[-1]

    score = 0

    factors = []

    close = float(
        row["close"]
    )

    ema20 = float(
        row["EMA20"]
    )

    ema50 = float(
        row["EMA50"]
    )

    ema200 = float(
        row["EMA200"]
    )

    current_rsi = (
        float(row["RSI"])
        if pd.notna(row["RSI"])
        else 50
    )

    volume = float(
        row["volume"]
    )

    volume_average = (
        float(row["VOLMA20"])
        if pd.notna(
            row["VOLMA20"]
        )
        else volume
    )

    if close > ema20:

        score += 10

        factors.append(
            (
                "🟢",
                "Precio sobre EMA20",
                "+10"
            )
        )

    else:

        score -= 10

        factors.append(
            (
                "🔴",
                "Precio bajo EMA20",
                "-10"
            )
        )

    if ema20 > ema50:

        score += 10

        factors.append(
            (
                "🟢",
                "EMA20 > EMA50",
                "+10"
            )
        )

    else:

        score -= 10

        factors.append(
            (
                "🔴",
                "EMA20 < EMA50",
                "-10"
            )
        )

    if close > ema200:

        score += 8

        factors.append(
            (
                "🟢",
                "Precio sobre EMA200",
                "+8"
            )
        )

    else:

        score -= 8

        factors.append(
            (
                "🔴",
                "Precio bajo EMA200",
                "-8"
            )
        )

    if 50 <= current_rsi <= 68:

        score += 8

        factors.append(
            (
                "🟢",
                f"RSI saludable {current_rsi:.1f}",
                "+8"
            )
        )

    elif current_rsi >= 75:

        score -= 8

        factors.append(
            (
                "🔴",
                f"RSI sobrecomprado {current_rsi:.1f}",
                "-8"
            )
        )

    elif current_rsi <= 30:

        score += 5

        factors.append(
            (
                "🟡",
                f"RSI sobrevendido {current_rsi:.1f}",
                "+5"
            )
        )

    else:

        factors.append(
            (
                "⚪",
                f"RSI neutral {current_rsi:.1f}",
                "0"
            )
        )

    if volume > volume_average:

        score += 6

        factors.append(
            (
                "🟢",
                "Volumen > media 20",
                "+6"
            )
        )

    else:

        score -= 3

        factors.append(
            (
                "🔴",
                "Volumen < media 20",
                "-3"
            )
        )

    return (
        max(
            -50,
            min(
                50,
                score
            )
        ),
        factors
    )


# ============================================================
# MARKET SCORE
# ============================================================

def market_score(
    market
):

    sol = market.get(
        "solana",
        {}
    )

    btc = market.get(
        "bitcoin",
        {}
    )

    sol_change = float(
        sol.get(
            "usd_24h_change"
        ) or 0
    )

    btc_change = float(
        btc.get(
            "usd_24h_change"
        ) or 0
    )

    score = 0

    factors = []

    if sol_change >= 3:

        score += 12

        factors.append(
            (
                "🟢",
                f"SOL momentum {sol_change:+.2f}%",
                "+12"
            )
        )

    elif sol_change >= 1:

        score += 6

        factors.append(
            (
                "🟢",
                f"SOL momentum {sol_change:+.2f}%",
                "+6"
            )
        )

    elif sol_change <= -3:

        score -= 12

        factors.append(
            (
                "🔴",
                f"SOL momentum {sol_change:+.2f}%",
                "-12"
            )
        )

    elif sol_change <= -1:

        score -= 6

        factors.append(
            (
                "🔴",
                f"SOL momentum {sol_change:+.2f}%",
                "-6"
            )
        )

    else:

        factors.append(
            (
                "⚪",
                f"SOL 24h {sol_change:+.2f}%",
                "0"
            )
        )

    if btc_change >= 2:

        score += 10

        factors.append(
            (
                "🟢",
                f"BTC fuerte {btc_change:+.2f}%",
                "+10"
            )
        )

    elif btc_change >= .5:

        score += 5

        factors.append(
            (
                "🟢",
                f"BTC positivo {btc_change:+.2f}%",
                "+5"
            )
        )

    elif btc_change <= -2:

        score -= 10

        factors.append(
            (
                "🔴",
                f"BTC débil {btc_change:+.2f}%",
                "-10"
            )
        )

    elif btc_change <= -.5:

        score -= 5

        factors.append(
            (
                "🔴",
                f"BTC negativo {btc_change:+.2f}%",
                "-5"
            )
        )

    return (
        max(
            -50,
            min(
                50,
                score
            )
        ),
        factors
    )


# ============================================================
# SENTIMENT
# ============================================================

def sentiment_score(
    fear_greed
):

    value = fear_greed.get(
        "value"
    )

    if value is None:

        return 0, [
            (
                "⚪",
                "Fear & Greed no disponible",
                "0"
            )
        ]

    if value >= 75:

        return 7, [
            (
                "🟢",
                f"Fear & Greed {value}",
                "+7"
            )
        ]

    if value >= 55:

        return 4, [
            (
                "🟢",
                f"Fear & Greed {value}",
                "+4"
            )
        ]

    if value <= 25:

        return -7, [
            (
                "🔴",
                f"Fear & Greed {value}",
                "-7"
            )
        ]

    if value <= 45:

        return -4, [
            (
                "🟡",
                f"Fear & Greed {value}",
                "-4"
            )
        ]

    return 0, [
        (
            "⚪",
            f"Fear & Greed {value}",
            "0"
        )
    ]


# ============================================================
# TELEGRAM
# ============================================================

def telegram_send(
    message
):

    if not TELEGRAM_TOKEN:

        return (
            False,
            "Falta TELEGRAM_BOT_TOKEN"
        )

    if not TELEGRAM_CHAT_ID:

        return (
            False,
            "Falta TELEGRAM_CHAT_ID"
        )

    url = (
        "https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}"
        "/sendMessage"
    )

    try:

        response = requests.post(
            url,
            data={
                "chat_id":
                    TELEGRAM_CHAT_ID,

                "text":
                    message
            },
            timeout=12
        )

        if response.ok:

            return (
                True,
                "Mensaje enviado"
            )

        return (
            False,
            response.text
        )

    except Exception as exc:

        return (
            False,
            str(exc)
        )


def find_chat_id():

    if not TELEGRAM_TOKEN:

        return (
            None,
            "Token no configurado"
        )

    url = (
        "https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}"
        "/getUpdates"
    )

    try:

        response = requests.get(
            url,
            timeout=12
        )

        data = response.json()

        updates = data.get(
            "result",
            []
        )

        if not updates:

            return (
                None,
                "Escribe /start al bot primero."
            )

        for update in reversed(
            updates
        ):

            message = update.get(
                "message"
            )

            if message:

                chat = message.get(
         
