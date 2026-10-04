import streamlit as st
import requests
import time
import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import quote_plus

# ============================================================
# SOL RADAR // GLOBAL MULTI-VECTOR
# No Plotly - solo Streamlit + Requests + librería estándar
# ============================================================

st.set_page_config(
    page_title="SOL RADAR // QUANTUM",
    page_icon="🟣",
    layout="wide"
)

# ============================================================
# TELEGRAM
# ============================================================
# NO pongas el token directamente aquí.
#
# En Streamlit Cloud:
#
# Settings -> Secrets
#
# [telegram]
# token = "TU_NUEVO_TOKEN"
# chat_id = "TU_CHAT_ID"
#
# ============================================================

def get_secret(section, key, env_key=""):
    try:
        value = st.secrets[section][key]
        if value:
            return str(value).strip()
    except Exception:
        pass

    import os

    if env_key:
        return os.getenv(env_key, "").strip()

    return ""


TELEGRAM_TOKEN = get_secret(
    "telegram",
    "token",
    "TELEGRAM_TOKEN"
)

TELEGRAM_CHAT_ID = get_secret(
    "telegram",
    "chat_id",
    "TELEGRAM_CHAT_ID"
)

# ============================================================
# HTTP SESSION
# ============================================================

SESSION = requests.Session()

SESSION.headers.update({
    "User-Agent": "SOL-RADAR/2.0"
})

# ============================================================
# ESTILO HACKER / TRADER
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background:
        radial-gradient(circle at top right, #160b2b 0%, #050609 35%),
        #050609;
    color: #d7d7dc;
    font-family: Consolas, "Courier New", monospace;
}

.block-container {
    padding-top: 1.2rem;
    max-width: 1450px;
}

h1, h2, h3 {
    font-family: Consolas, "Courier New", monospace !important;
}

[data-testid="stMetric"] {
    background: #090c13;
    border: 1px solid #252b3a;
    padding: 12px;
    border-radius: 10px;
}

[data-testid="stMetricValue"] {
    font-family: Consolas, "Courier New", monospace;
}

.radar {
    background:
        linear-gradient(
            135deg,
            rgba(10,10,20,0.98),
            rgba(22,5,38,0.98)
        );

    border: 1px solid #713cff;
    border-radius: 14px;
    padding: 24px;

    box-shadow:
        0 0 25px rgba(120,60,255,0.16),
        inset 0 0 30px rgba(120,60,255,0.04);
}

.panel {
    background: #090c12;
    border: 1px solid #202634;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 14px;
}

.news {
    background: #080a0f;
    border-left: 3px solid #8a4dff;
    padding: 11px 14px;
    margin: 7px 0;
    border-radius: 4px;
}

.small {
    color: #7f8798;
    font-size: 0.78rem;
}

.green {
    color: #00ff88 !important;
    font-weight: bold;
}

.red {
    color: #ff4965 !important;
    font-weight: bold;
}

.yellow {
    color: #ffc857 !important;
    font-weight: bold;
}

.purple {
    color: #b875ff !important;
    font-weight: bold;
}

.bar {
    height: 13px;
    background: #171b25;
    border-radius: 10px;
    overflow: hidden;
}

.bar-green {
    height: 100%;
    background: #00ff88;
    border-radius: 10px;
}

.bar-red {
    height: 100%;
    background: #ff3150;
    border-radius: 10px;
}

.signal-box {
    background: #070910;
    border: 1px solid #242a38;
    border-radius: 9px;
    padding: 14px;
    margin-bottom: 10px;
}

</style>
""",
    unsafe_allow_html=True
)

# ============================================================
# FUNCIONES GENERALES
# ============================================================

def get_json(url, params=None, timeout=8):
    try:
        response = SESSION.get(
            url,
            params=params,
            timeout=timeout
        )

        response.raise_for_status()

        return response.json()

    except Exception:
        return None


def clamp(value, minimum=5, maximum=95):
    return max(
        minimum,
        min(
            maximum,
            int(round(value))
        )
    )


def format_money(value):

    if value is None:
        return "—"

    if abs(value) >= 1000:
        return f"${value:,.0f}"

    return f"${value:,.4f}"


def clean_text(value):

    value = value or ""

    value = re.sub(
        r"<[^>]+>",
        " ",
        value
    )

    value = html.unescape(value)

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


# ============================================================
# BINANCE - PRECIO
# ============================================================

def binance_24h(symbol):

    data = get_json(
        "https://api.binance.com/api/v3/ticker/24hr",
        {
            "symbol": symbol
        },
        timeout=7
    )

    if not data:
        return None

    try:

        return {
            "price": float(
                data.get(
                    "lastPrice",
                    0
                )
            ),

            "change": float(
                data.get(
                    "priceChangePercent",
                    0
                )
            ),

            "volume": float(
                data.get(
                    "quoteVolume",
                    0
                )
            )
        }

    except Exception:

        return None


# ============================================================
# BINANCE - VELAS
# ============================================================

def binance_klines(
    symbol,
    interval="1h",
    limit=100
):

    data = get_json(
        "https://api.binance.com/api/v3/klines",
        {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        },
        timeout=8
    )

    if not data:
        return []

    return data


# ============================================================
# ANALISIS TECNICO SOL
# ============================================================

def technical_analysis():

    candles = binance_klines(
        "SOLUSDT",
        "1h",
        100
    )

    if len(candles) < 50:

        return 0, {}

    closes = [
        float(candle[4])
        for candle in candles
    ]

    volumes = [
        float(candle[5])
        for candle in candles
    ]

    def sma(period):

        return (
            sum(closes[-period:])
            / period
        )

    sma20 = sma(20)

    sma50 = sma(50)

    last_price = closes[-1]

    # --------------------------------------------------------
    # RSI
    # --------------------------------------------------------

    gains = []
    losses = []

    for i in range(
        1,
        len(closes)
    ):

        difference = (
            closes[i]
            - closes[i - 1]
        )

        gains.append(
            max(
                difference,
                0
            )
        )

        losses.append(
            max(
                -difference,
                0
            )
        )

    average_gain = (
        sum(gains[-14:])
        / 14
    )

    average_loss = (
        sum(losses[-14:])
        / 14
    )

    if average_loss == 0:

        rsi = 100

    else:

        relative_strength = (
            average_gain
            / average_loss
        )

        rsi = (
            100
            - (
                100
                / (
                    1
                    + relative_strength
                )
            )
        )

    # --------------------------------------------------------
    # VOLUMEN
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    score = 0

    if last_price > sma20:
        score += 10
    else:
        score -= 10

    if sma20 > sma50:
        score += 10
    else:
        score -= 10

    if 50 <= rsi <= 68:

        score += 10

    elif rsi > 75:

        score -= 8

    elif rsi < 30:

        score += 5

    if (
        volume_ratio > 1.20
        and last_price > sma20
    ):

        score += 7

    return score, {
        "rsi": rsi,
        "sma20": sma20,
        "sma50": sma50,
        "volume_ratio": volume_ratio,
        "last": last_price
    }


# ============================================================
# FEAR & GREED
# ============================================================

def fear_greed():

    data = get_json(
        "https://api.alternative.me/fng/",
        {
            "limit": 1
        },
        timeout=7
    )

    try:

        item = data["data"][0]

        return (
            int(item["value"]),
            item["value_classification"]
        )

    except Exception:

        return (
            None,
            "N/D"
        )


# ============================================================
# MERCADO GLOBAL
# ============================================================

def global_market():

    data = get_json(
        "https://api.coingecko.com/api/v3/global",
        timeout=8
    )

    try:

        global_data = data["data"]

        return {

            "btc_dominance":
                float(
                    global_data[
                        "market_cap_percentage"
                    ]["btc"]
                ),

            "market_change":
                float(
                    global_data[
                        "market_cap_change_percentage_24h_usd"
                    ]
                )
        }

    except Exception:

        return {

            "btc_dominance": None,

            "market_change": None
        }


# ============================================================
# GOOGLE NEWS RSS
# ============================================================

def google_news(
    query,
    limit=8
):

    url = (
        "https://news.google.com/rss/search?q="
        + quote_plus(query)
        + "&hl=en-US&gl=US&ceid=US:en"
    )

    try:

        response = SESSION.get(
            url,
            timeout=10
        )

        response.raise_for_status()

        root = ET.fromstring(
            response.content
        )

        results = []

        for item in root.findall(
            "./channel/item"
        )[:limit]:

            title = clean_text(
                item.findtext(
                    "title",
                    ""
                )
            )

            date = item.findtext(
                "pubDate",
                ""
            )

            link = item.findtext(
                "link",
                ""
            )

            if title:

                results.append(
                    {
                        "title": title,
                        "date": date,
                        "link": link
                    }
                )

        return results

    except Exception:

        return []


# ============================================================
# NOTICIAS QUE PUEDEN AFECTAR SOL
# ============================================================

NEWS_QUERIES = [

    "Solana SOL cryptocurrency",

    "Solana ETF institutional",

    "Solana network hack exploit outage",

    "Bitcoin ETF cryptocurrency",

    "SEC cryptocurrency regulation",

    "Federal Reserve interest rates crypto",

    "US inflation CPI PCE crypto",

    "US jobs unemployment payrolls crypto",

    "Trump tariffs markets cryptocurrency",

    "geopolitics oil markets cryptocurrency",

    "crypto market liquidation",

    "crypto institutional inflows",

    "stablecoin regulation",

    "US dollar DXY cryptocurrency",

    "global financial markets crypto"

]


# ============================================================
# SENTIMIENTO SIMPLE DE NOTICIAS
# ============================================================

POSITIVE_WORDS = [

    "approval",
    "approved",
    "etf",
    "inflow",
    "bullish",
    "adoption",
    "record",
    "surge",
    "rally",
    "buy",
    "growth",
    "positive",
    "rate cut",
    "cuts",
    "integration",
    "partnership",
    "institutional",
    "investment"

]

NEGATIVE_WORDS = [

    "hack",
    "exploit",
    "outage",
    "lawsuit",
    "ban",
    "sell",
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
    "negative",
    "recession"

]


def calculate_news_score(news):

    score = 0

    for item in news:

        title = item[
            "title"
        ].lower()

        for word in POSITIVE_WORDS:

            if word in title:
                score += 2

        for word in NEGATIVE_WORDS:

            if word in title:
                score -= 2

    return max(
        -20,
        min(
            20,
            score
        )
    )


# ============================================================
# TELEGRAM API
# ============================================================

def telegram_request(
    method,
    params=None
):

    if not TELEGRAM_TOKEN:

        return (
            None,
            "Telegram token no configurado."
        )

    url = (
        "https://api.telegram.org/bot"
        + TELEGRAM_TOKEN
        + "/"
        + method
    )

    try:

        response = SESSION.get(
            url,
            params=params or {},
            timeout=10
        )

        data = response.json()

        if not data.get("ok"):

            return (
                None,
                data.get(
                    "description",
                    "Error Telegram"
                )
            )

        return (
            data,
            None
        )

    except Exception as error:

        return (
            None,
            str(error)
        )


# ============================================================
# ENVIAR TELEGRAM
# ============================================================

def send_telegram(
    chat_id,
    message
):

    data, error = telegram_request(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": True
        }
    )

    if error:

        return (
            False,
            error
        )

    return (
        True,
        None
    )


# ============================================================
# DETECTAR CHAT ID
# ============================================================

def detect_chat_id():

    data, error = telegram_request(
        "getUpdates",
        {
            "limit": 20,
            "timeout": 1
        }
    )

    if error:

        return (
            None,
            error
        )

    if not data:

        return (
            None,
            "No se recibió respuesta."
        )

    chats = []

    for update in data.get(
        "result",
        []
    ):

        message = (
            update.get("message")
            or update.get("edited_message")
        )

        if not message:
            continue

        chat = message.get(
            "chat"
        )

        if not chat:
            continue

        chats.append(
            {
                "id": str(
                    chat.get("id")
                ),
                "username":
                    chat.get(
                        "username",
                        ""
                    ),
                "name":
                    chat.get(
                        "first_name",
                        ""
                    )
            }
        )

    if not chats:

        return (
            None,
            "No hay mensajes. Abre tu bot en Telegram y envía /start."
        )

    return (
        chats[-1]["id"],
        None
    )


# ============================================================
# CONSTRUIR RADAR
# ============================================================

@st.cache_data(ttl=60)
def build_radar():

    sol = binance_24h(
        "SOLUSDT"
    )

    btc = binance_24h(
        "BTCUSDT"
    )

    eth = binance_24h(
        "ETHUSDT"
    )

    technical_score_value, technical_data = (
        technical_analysis()
    )

    fear_value, fear_label = (
        fear_greed()
    )

    global_data = (
        global_market()
    )

    all_news = []

    seen_titles = set()

    for query in NEWS_QUERIES:

        news = google_news(
            query,
            8
        )

        for item in news:

            key = item[
                "title"
            ].lower()

            if key not in seen_titles:

                seen_titles.add(
                    key
                )

                all_news.append(
                    item
                )

    news_score = (
        calculate_news_score(
            all_news
        )
    )

    # --------------------------------------------------------
    # SCORE FINAL
    # --------------------------------------------------------

    score = (
        technical_score_value
        + news_score
    )

    # Fear & Greed
    if fear_value is not None:

        fear_adjustment = (
            (fear_value - 50)
            / 6
        )

        fear_adjustment = max(
            -8,
            min(
                8,
                fear_adjustment
            )
        )

        score += fear_adjustment

    # Mercado global
    if (
        global_data[
            "market_change"
        ] is not None
    ):

        global_adjustment = (
            global_data[
                "market_change"
            ] * 1.5
        )

        global_adjustment = max(
            -6,
            min(
                6,
                global_adjustment
            )
        )

        score += global_adjustment

    # --------------------------------------------------------
    # PROBABILIDADES
    # --------------------------------------------------------

    probability_up = clamp(
        50 + score
    )

    probability_down = (
        100
        - probability_up
    )

    confidence = clamp(
        50 + abs(score) * 1.2,
        50,
        92
    )

    return {

        "sol": sol,

        "btc": btc,

        "eth": eth,

        "technical_score":
            technical_score_value,

        "technical":
            technical_data,

        "fear":
            fear_value,

        "fear_label":
            fear_label,

        "global":
            global_data,

        "news":
            all_news[:40],

        "news_score":
            news_score,

        "score":
            score,

        "up":
            probability_up,

        "down":
            probability_down,

        "confidence":
            confidence,

        "timestamp":
            datetime.now(
                timezone.utc
            ).strftime(
                "%Y-%m-%d %H:%M UTC"
            )
    }


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown(
    "# ⚙️ CONTROL CENTER"
)

refresh_seconds = st.sidebar.slider(
    "Intervalo de actualización",
    30,
    300,
    90,
    10
)

if st.sidebar.button(
    "🔄 ACTUALIZAR AHORA"
):

    st.cache_data.clear()

    st.rerun()


st.sidebar.markdown("---")

st.sidebar.markdown(
    """
### Fuentes utilizadas

🟣 Binance  
🌐 Google News  
😱 Fear & Greed  
🌍 CoinGecko  
📊 Indicadores técnicos  

El radar combina estas señales para generar
un escenario probabilístico para SOL.
"""
)


# ============================================================
# EJECUTAR RADAR
# =====
