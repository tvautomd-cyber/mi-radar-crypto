import os
import requests
import streamlit as st
import xml.etree.ElementTree as ET
from datetime import datetime, timezone


# ============================================================
# SOLANA RADAR // TRADER CORE
# Version estable para Streamlit Cloud
# ============================================================

st.set_page_config(
    page_title="SOLANA RADAR // TRADER CORE",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# TELEGRAM
# ============================================================

def get_secret(name, default=""):
    try:
        value = st.secrets[name]
        if value:
            return str(value)
    except Exception:
        pass

    return os.getenv(name, default)


TELEGRAM_TOKEN = get_secret("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = get_secret("TELEGRAM_CHAT_ID")


# ============================================================
# ESTILO
# ============================================================

CSS = (
    "<style>"

    ":root{"
    "--bg:#05070b;"
    "--panel:#0b1018;"
    "--line:#1b2633;"
    "--text:#dce7f3;"
    "--muted:#718096;"
    "--green:#00ff9d;"
    "--red:#ff3b6b;"
    "--cyan:#00d9ff;"
    "--purple:#9945ff;"
    "--yellow:#ffd166;"
    "}"

    ".stApp{"
    "background:radial-gradient(circle at 50% -10%,#111a2b 0%,#05070b 48%);"
    "color:#dce7f3;"
    "}"

    ".block-container{"
    "max-width:1500px;"
    "padding-top:1rem;"
    "padding-bottom:3rem;"
    "}"

    "h1,h2,h3{"
    "font-family:monospace!important;"
    "}"

    ".mono{"
    "font-family:monospace;"
    "}"

    ".topbar{"
    "border:1px solid #1b2633;"
    "background:#070b11;"
    "padding:14px;"
    "border-radius:10px;"
    "box-shadow:0 0 30px rgba(0,217,255,.05);"
    "}"

    ".brand{"
    "font-family:monospace;"
    "font-weight:900;"
    "font-size:1.35rem;"
    "color:white;"
    "}"

    ".sub{"
    "font-family:monospace;"
    "font-size:.68rem;"
    "color:#718096;"
    "margin-top:4px;"
    "}"

    ".card{"
    "background:linear-gradient(180deg,#0d141e,#080c12);"
    "border:1px solid #1b2633;"
    "border-radius:10px;"
    "padding:14px;"
    "min-height:105px;"
    "}"

    ".label{"
    "font:700 .67rem monospace;"
    "letter-spacing:1px;"
    "color:#718096;"
    "}"

    ".value{"
    "font:900 1.5rem monospace;"
    "margin-top:7px;"
    "color:white;"
    "}"

    ".green{color:#00ff9d!important;}"
    ".red{color:#ff3b6b!important;}"
    ".cyan{color:#00d9ff!important;}"
    ".purple{color:#b889ff!important;}"
    ".yellow{color:#ffd166!important;}"

    ".hero{"
    "background:linear-gradient(135deg,#0e0718,#090e16 55%,#071b19);"
    "border:1px solid #44206b;"
    "border-radius:12px;"
    "padding:20px;"
    "margin-top:10px;"
    "box-shadow:0 0 40px rgba(153,69,255,.10);"
    "}"

    ".score{"
    "font:900 3.1rem monospace;"
    "line-height:1;"
    "}"

    ".meter{"
    "height:14px;"
    "background:#171d26;"
    "border-radius:20px;"
    "overflow:hidden;"
    "border:1px solid #283241;"
    "margin-top:15px;"
    "}"

    ".meter-inner{"
    "height:100%;"
    "background:linear-gradient(90deg,#ff3b6b,#ffd166,#00ff9d);"
    "}"

    ".section{"
    "font:800 .76rem monospace;"
    "color:#8ea3b8;"
    "letter-spacing:2px;"
    "margin:20px 0 8px;"
    "}"

    ".signal{"
    "border-left:3px solid #00d9ff;"
    "padding:10px 12px;"
    "background:#081018;"
    "border-radius:5px;"
    "margin:7px 0;"
    "font:700 .76rem monospace;"
    "}"

    ".signal-good{"
    "border-left-color:#00ff9d;"
    "}"

    ".signal-bad{"
    "border-left-color:#ff3b6b;"
    "}"

    ".signal-warn{"
    "border-left-color:#ffd166;"
    "}"

    ".news{"
    "border:1px solid #1b2633;"
    "background:#080d14;"
    "padding:11px 13px;"
    "margin:7px 0;"
    "border-radius:8px;"
    "}"

    ".news-title{"
    "font:700 .85rem monospace;"
    "color:#dbe7f4;"
    "line-height:1.4;"
    "}"

    ".news-meta{"
    "font:600 .65rem monospace;"
    "color:#5f7184;"
    "margin-top:5px;"
    "}"

    ".footer{"
    "color:#526273;"
    "font:600 .65rem monospace;"
    "text-align:center;"
    "margin-top:25px;"
    "}"

    "</style>"
)

st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
# HTTP
# ============================================================

SESSION = requests.Session()

SESSION.headers.update(
    {
        "User-Agent": "SolanaRadar/2.0"
    }
)


def get_json(url, params=None, timeout=5):
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


def get_text(url, timeout=4):
    try:
        response = SESSION.get(
            url,
            timeout=timeout
        )

        response.raise_for_status()

        return response.text

    except Exception:
        return ""


# ============================================================
# MARKET DATA
# ============================================================

@st.cache_data(ttl=20, show_spinner=False)
def get_market_data():

    data = get_json(
        "https://api.coingecko.com/api/v3/simple/price",
        {
            "ids": "solana,bitcoin,ethereum",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_market_cap": "true",
        },
        timeout=5
    )

    if not data:

        return {
            "ok": False,
            "sol": {
                "price": 0,
                "change": 0,
                "volume": 0,
                "cap": 0
            },
            "btc": {
                "price": 0,
                "change": 0,
                "volume": 0,
                "cap": 0
            },
            "eth": {
                "price": 0,
                "change": 0,
                "volume": 0,
                "cap": 0
            }
        }


    def parse_coin(name):

        item = data.get(name, {})

        return {
            "price": float(item.get("usd", 0)),
            "change": float(item.get("usd_24h_change", 0)),
            "volume": float(item.get("usd_24h_vol", 0)),
            "cap": float(item.get("usd_market_cap", 0))
        }


    return {
        "ok": True,
        "sol": parse_coin("solana"),
        "btc": parse_coin("bitcoin"),
        "eth": parse_coin("ethereum")
    }


# ============================================================
# BINANCE TECHNICAL DATA
# ============================================================

@st.cache_data(ttl=30, show_spinner=False)
def get_binance_data():

    data = get_json(
        "https://api.binance.com/api/v3/klines",
        {
            "symbol": "SOLUSDT",
            "interval": "15m",
            "limit": 96
        },
        timeout=5
    )

    if not data or len(data) < 30:

        return {
            "ok": False,
            "rsi": 50,
            "momentum": 0,
            "trend": 0,
            "price": 0
        }


    closes = []

    for candle in data:

        try:
            closes.append(float(candle[4]))
        except Exception:
            pass


    if len(closes) < 30:

        return {
            "ok": False,
            "rsi": 50,
            "momentum": 0,
            "trend": 0,
            "price": 0
        }


    # -------------------------
    # RSI
    # -------------------------

    gains = []
    losses = []

    for i in range(1, len(closes)):

        difference = closes[i] - closes[i - 1]

        if difference >= 0:

            gains.append(difference)
            losses.append(0)

        else:

            gains.append(0)
            losses.append(abs(difference))


    avg_gain = sum(gains[-14:]) / 14
    avg_loss = sum(losses[-14:]) / 14


    if avg_loss == 0:

        rsi = 100

    else:

        relative_strength = avg_gain / avg_loss

        rsi = 100 - (
            100 / (1 + relative_strength)
        )


    # -------------------------
    # Momentum
    # -------------------------

    short_average = sum(closes[-6:]) / 6
    long_average = sum(closes[-24:]) / 24

    if long_average != 0:

        momentum = (
            (short_average / long_average) - 1
        ) * 100

    else:

        momentum = 0


    trend = max(
        -100,
        min(
            100,
            momentum * 25
        )
    )


    return {
        "ok": True,
        "rsi": rsi,
        "momentum": momentum,
        "trend": trend,
        "price": closes[-1]
    }


# ============================================================
# NEWS
# ============================================================

RSS_FEEDS = [

    (
        "CoinDesk",
        "https://www.coindesk.com/arc/outboundfeeds/rss/"
    ),

    (
        "Cointelegraph",
        "https://cointelegraph.com/rss"
    ),

    (
        "Decrypt",
        "https://decrypt.co/feed"
    ),

    (
        "Google News",
        "https://news.google.com/rss/search?q=Solana%20crypto&hl=en-US&gl=US&ceid=US:en"
    )

]


@st.cache_data(ttl=180, show_spinner=False)
def get_news():

    collected = []


    for source, url in RSS_FEEDS:

        raw = get_text(
            url,
            timeout=4
        )

        if not raw:
            continue


        try:

            root = ET.fromstring(raw)

        except Exception:

            continue


        items = root.findall(".//item")


        for item in items[:12]:

            title = (
                item.findtext("title")
                or ""
            ).strip()

            link = (
                item.findtext("link")
                or ""
            ).strip()

            date = (
                item.findtext("pubDate")
                or ""
            ).strip()


            if title:

                collected.append(
                    {
                        "source": source,
                        "title": title,
                        "link": link,
                        "date": date
                    }
                )


    # -------------------------
    # Ranking de relevancia
    # -------------------------

    keywords = [

        "solana",
        "sol",
        "etf",
        "sec",
        "fed",
        "fomc",
        "inflation",
        "rates",
        "bitcoin",
        "crypto",
        "tariff",
        "trump",
        "hack",
        "exploit",
        "liquidation",
        "defi",
        "stablecoin",
        "regulation",
        "jobs",
        "cpi"

    ]


    def relevance(item):

        title = item["title"].lower()

        score = 0

        for keyword in keywords:

            if keyword in title:

                score += 2


        if "solana" in title:

            score += 5


        return score


    collected.sort(
        key=relevance,
        reverse=True
    )


    return collected[:25]


# ============================================================
# SENTIMENT
# ============================================================

POSITIVE_WORDS = [

    "approval",
    "approved",
    "bullish",
    "surge",
    "rally",
    "inflow",
    "adoption",
    "partnership",
    "record",
    "launch",
    "growth",
    "rate cut",
    "cuts",
    "etf",
    "buy",
    "accumulation",
    "institutional",
    "upgrade"

]


NEGATIVE_WORDS = [

    "hack",
    "exploit",
    "outflow",
    "lawsuit",
    "ban",
    "bearish",
    "crash",
    "dump",
    "liquidation",
    "fraud",
    "attack",
    "downgrade",
    "tariff",
    "inflation",
    "higher rates",
    "rate hike",
    "sell",
    "bankruptcy"

]


def calculate_news_score(news):

    score = 0


    for item in news:

        title = item["title"].lower()

        positive = 0
        negative = 0


        for word in POSITIVE_WORDS:

            if word in title:

                positive += 1


        for word in NEGATIVE_WORDS:

            if word in title:

                negative += 1


        item_score = (
            positive - negative
        ) * 4


        item_score = max(
            -10,
            min(
                10,
                item_score
            )
        )


        score += item_score


    return max(
        -100,
        min(
            100,
            score
        )
    )


# ============================================================
# SIGNAL ENGINE
# ============================================================

def clamp(value, minimum, maximum):

    return max(
        minimum,
        min(
            maximum,
            value
        )
    )


def calculate_signal(
    market,
    technical,
    news
):

    news_score = calculate_news_score(
        news
    )


    sol_change = market["sol"]["change"]
    btc_change = market["btc"]["change"]
    eth_change = market["eth"]["change"]


    # -------------------------
    # Market momentum
    # -------------------------

    sol_component = clamp(
        sol_change * 5,
        -25,
        25
    )


    btc_component = clamp(
        btc_change * 2,
        -12,
        12
    )


    eth_component = clamp(
        eth_change * 1.5,
        -8,
        8
    )


    # -------------------------
    # Technical
    # -------------------------

    if technical["ok"]:

        technical_component = clamp(
            technical["trend"] * 0.35,
            -20,
            20
        )

    else:

        technical_component = 0


    # -------------------------
    # RSI
    # -------------------------

    rsi_component = 0


    if technical["ok"]:

        rsi = technical["rsi"]


        if rsi < 30:

            rsi_component = 10

        elif rsi > 70:

            rsi_component = -10

        elif rsi < 45:

            rsi_component = 4

        elif rsi > 55:

            rsi_component = -4


    # -------------------------
    # Final score
    # -------------------------

    score = (

        50

        + news_score * 0.20

        + sol_component * 0.35

        + btc_component * 0.35

        + eth_component * 0.25

        + technical_component * 0.55

        + rsi_component * 0.45

    )


    score = clamp(
        score,
        5,
        95
    )


    # -------------------------
    # Data confidence
    # -------------------------

    confidence = 0


    if market["ok"]:

        confidence += 35


    if technical["ok"]:

        confidence += 35


    confidence += min(
        30,
        len(news) * 2
    )


    confidence = clamp(
        confidence,
        20,
        95
    )


    return {

        "up": round(
            score,
            1
        ),

        "down": round(
            100 - score,
            1
        ),

        "confidence": round(
            confidence
        ),

        "news": round(
            news_score
        ),

        "technical": round(
            technical_component
        ),

        "rsi": round(
            technical["rsi"],
            1
        ),

        "momentum": round(
            technical["momentum"],
            3
        )

    }


# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(message):

    if not TELEGRAM_TOKEN:

        return (
            False,
            "TELEGRAM_TOKEN no configurado"
        )


    if not TELEGRAM_CHAT_ID:

        return (
            False,
            "TELEGRAM_CHAT_ID no configurado"
        )


    try:

        url = (
            "https://api.telegram.org/bot"
            + TELEGRAM_TOKEN
            + "/sendMessage"
        )


        response = SESSION.post(

            url,

            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            },

            timeout=8

        )


        if response.ok:

            return (
                True,
                "Telegram enviado correctamente"
            )


        return (
            False,
            "Telegram HTTP "
            + str(response.status_code)
        )


    except Exception as error:

        return (
            False,
            "Error Telegram: "
            + str(error)
        )


# ============================================================
# LOAD DATA
# ============================================================

market = get_market_data()

technical = get_binance_data()

news = get_news()


signal = calculate_signal(

    market,
    technical,
    news

)


sol = market["sol"]
btc = market["btc"]
eth = market["eth"]


now = datetime.now(
    timezone.utc
).strftime(
    "%Y-%m-%d %H:%M:%S UTC"
)


# ============================================================
# HEADER
# ============================================================

st.markdown(

    '<div class="topbar">'
    '<div class="brand">'
    '⚡ SOLANA RADAR // TRADER CORE'
    '</div>'
    '<div class="sub">'
    'MULTI-VECTOR MARKET SCANNER · LIVE MARKET DATA · '
    + now +
    '</div>'
    '</div>',

    unsafe_allow_html=True

)


# ============================================================
# TOP CARDS
# ============================================================

col1, col2, col3, col4 = st.columns(4)


with col1:

    color = (
        "green"
        if sol["change"] >= 0
        else "red"
    )

    st.markdown(

        '<div class="card">'
        '<div class="label">SOL / USD</div>'
        '<div class="value purple">$'
        + f"{sol['price']:,.2f}"
        + '</div>'
        '<div class="'
        + color +
        ' mono">'
        + f"{sol['change']:+.2f}% 24H"
        + '</div>'
        '</div>',

        unsafe_allow_html=True

    )


with col2:

    color = (
        "green"
        if btc["change"] >= 0
        else "red"
    )

    st.markdown(

        '<div class="card">'
        '<div class="label">BTC / USD</div>'
        '<div class="value">$'
        + f"{btc['price']:,.0f}"
        + '</div>'
        '<div class="'
        + color +
        ' mono">'
        + f"{btc['change']:+.2f}% 24H"
        + '</div>'
        '</div>',

        unsafe_allow_html=True

    )


with col3:

    color = (
        "green"
        if eth["change"] >= 0
        else "red"
    )

    st.markdown(

        '<div class="card">'
        '<div class="label">ETH / USD</div>'
        '<div class="value">$'
        + f"{eth['price']:,.0f}"
        + '</div>'
        '<div class="'
        + color +
        ' mono">'
        + f"{eth['change']:+.2f}% 24H"
        + '</div>'
        '</div>',

        unsafe_allow_html=True

    )


with col4:

    st.markdown(

        '<div class="card">'
        '<div class="label">DATA CONFIDENCE</div>'
        '<div class="value">'
        + str(signal["confidence"])
        + '%'
        '</div>'
        '<div class="cyan mono">'
        'LIVE DATA COVERAGE'
        '</div>'
        '</div>',

        unsafe_allow_html=True

    )


# ============================================================
# MAIN SIGNAL
# ============================================================

st.markdown(

    '<div class="section">'
    '01 // SOLANA DIRECTION ENGINE'
    '</div>',

    unsafe_allow_html=True

)


if signal["up"] >= signal["down"]:

    direction = "SUBIDA"

    direction_color = "green"

else:

    direction = "BAJADA"

    direction_color = "red"


st.markdown(

    '<div class="hero">'

    '<div class="label">'
    'PROBABILIDAD MODELO · NO ES GARANTÍA'
    '</div>'

    '<div style="display:flex;'
    'justify-content:space-between;'
    'align-items:end;'
    'gap:20px;'
    'flex-wrap:wrap;">'

    '<div>'

    '<div class="score '
    + direction_color +
    '">'

    + str(signal["up"])
    + '%'

    + '</div>'

    '<div class="'
    + direction_color +
    ' mono">'

    'CHANCE MODELO DE SUBIDA'

    '</div>'

    '</div>'

    '<div c
