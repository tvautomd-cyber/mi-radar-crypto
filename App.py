import streamlit as st
import requests
import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import quote_plus

# ============================================================
# SOL RADAR V3
# Fast startup / no Plotly / resilient APIs
# ============================================================

st.set_page_config(
    page_title="SOL RADAR // V3",
    page_icon="🟣",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CONFIG
# ============================================================

REQUEST_TIMEOUT = 5

session = requests.Session()

session.headers.update({
    "User-Agent": "Mozilla/5.0 SOL-RADAR-V3"
})


# ============================================================
# TELEGRAM SECRETS
# ============================================================

def read_secret(section, key, env_name):

    try:
        value = st.secrets[section][key]

        if value:
            return str(value).strip()

    except Exception:
        pass

    try:
        import os

        return os.getenv(
            env_name,
            ""
        ).strip()

    except Exception:
        return ""


TELEGRAM_TOKEN = read_secret(
    "telegram",
    "token",
    "TELEGRAM_TOKEN"
)

TELEGRAM_CHAT_ID = read_secret(
    "telegram",
    "chat_id",
    "TELEGRAM_CHAT_ID"
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
            rgba(115, 40, 255, 0.16),
            transparent 28%
        ),
        radial-gradient(
            circle at 10% 20%,
            rgba(0, 180, 255, 0.07),
            transparent 25%
        ),
        #05070b;

    color: #d7d9e0;
}

.block-container {
    max-width: 1500px;
    padding-top: 1rem;
}

h1, h2, h3 {
    font-family:
        "Courier New",
        Consolas,
        monospace !important;
}

.title {
    font-family:
        "Courier New",
        Consolas,
        monospace;

    color: #b875ff;
    font-size: 2.4rem;
    font-weight: 800;

    text-shadow:
        0 0 12px rgba(150, 70, 255, 0.7);
}

.subtitle {
    color: #596273;
    font-family:
        "Courier New",
        monospace;
    letter-spacing: 2px;
}

.radar-card {
    background:
        linear-gradient(
            145deg,
            #0b0d14,
            #100a1d
        );

    border:
        1px solid #6835c8;

    border-radius: 16px;

    padding: 24px;

    box-shadow:
        0 0 35px
        rgba(115, 50, 255, 0.12),

        inset 0 0 30px
        rgba(115, 50, 255, 0.04);
}

.signal {
    background: #090c12;
    border: 1px solid #202633;
    border-radius: 10px;
    padding: 14px;
}

.news-card {
    background: #080b10;
    border-left: 3px solid #854cff;
    border-radius: 5px;
    padding: 12px;
    margin-bottom: 8px;
}

.news-positive {
    border-left-color: #00ff88;
}

.news-negative {
    border-left-color: #ff4260;
}

.small {
    color: #697284;
    font-size: 0.76rem;
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
    color: #b875ff !important;
}

.big-number {
    font-size: 2.5rem;
    font-weight: 800;
    font-family:
        "Courier New",
        monospace;
}

.progress-bg {
    background: #171b24;
    height: 15px;
    border-radius: 10px;
    overflow: hidden;
}

.progress-up {
    background: #00e878;
    height: 100%;
}

.progress-down {
    background: #ff3454;
    height: 100%;
}

.footer {
    color: #454c5b;
    text-align: center;
    font-size: 0.72rem;
    font-family:
        "Courier New",
        monospace;
}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# UTILS
# ============================================================

def clamp(
    value,
    minimum=5,
    maximum=95
):

    return max(
        minimum,
        min(
            maximum,
            int(round(value))
        )
    )


def money(value):

    if value is None:
        return "—"

    if abs(value) >= 1000:

        return f"${value:,.0f}"

    return f"${value:,.4f}"


def api_json(
    url,
    params=None,
    timeout=REQUEST_TIMEOUT
):

    try:

        response = session.get(
            url,
            params=params,
            timeout=timeout
        )

        response.raise_for_status()

        return response.json()

    except Exception:

        return None


def clean_text(text):

    text = text or ""

    text = re.sub(
        r"<[^>]*>",
        " ",
        text
    )

    text = html.unescape(text)

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# BINANCE PRICE
# ============================================================

def get_market(symbol):

    data = api_json(
        "https://api.binance.com/api/v3/ticker/24hr",
        {
            "symbol": symbol
        }
    )

    if not data:

        return None

    try:

        return {
            "price": float(
                data["lastPrice"]
            ),

            "change": float(
                data["priceChangePercent"]
            ),

            "volume": float(
                data["quoteVolume"]
            )
        }

    except Exception:

        return None


# ============================================================
# CANDLES
# ============================================================

def get_candles(
    symbol="SOLUSDT",
    interval="1h",
    limit=100
):

    data = api_json(
        "https://api.binance.com/api/v3/klines",
        {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
    )

    if not data:

        return []

    return data


# ============================================================
# TECHNICAL ANALYSIS
# ============================================================

def technical_analysis():

    candles = get_candles()

    if len(candles) < 50:

        return {
            "score": 0,
            "rsi": None,
            "sma20": None,
            "sma50": None,
            "volume_ratio": None,
            "prices": []
        }

    closes = [
        float(c[4])
        for c in candles
    ]

    volumes = [
        float(c[5])
        for c in candles
    ]

    sma20 = (
        sum(closes[-20:])
        / 20
    )

    sma50 = (
        sum(closes[-50:])
        / 50
    )

    # RSI

    gains = []
    losses = []

    for i in range(
        1,
        len(closes)
    ):

        diff = (
            closes[i]
            - closes[i - 1]
        )

        if diff >= 0:

            gains.append(diff)
            losses.append(0)

        else:

            gains.append(0)
            losses.append(-diff)

    avg_gain = (
        sum(gains[-14:])
        / 14
    )

    avg_loss = (
        sum(losses[-14:])
        / 14
    )

    if avg_loss == 0:

        rsi = 100

    else:

        rs = (
            avg_gain
            / avg_loss
        )

        rsi = (
            100
            - (
                100
                / (1 + rs)
            )
        )

    avg_volume = (
        sum(volumes[-20:])
        / 20
    )

    volume_ratio = (
        volumes[-1]
        / avg_volume
        if avg_volume
        else 1
    )

    score = 0

    # Trend

    if closes[-1] > sma20:
        score += 10
    else:
        score -= 10

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

    # Volume

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
        "prices": closes
    }


# ============================================================
# FEAR & GREED
# ============================================================

def get_fear_greed():

    data = api_json(
        "https://api.alternative.me/fng/",
        {
            "limit": 1
        }
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
# GLOBAL MARKET
# ============================================================

def get_global_market():

    data = api_json(
        "https://api.coingecko.com/api/v3/global"
    )

    try:

        obj = data["data"]

        dominance = float(
            obj[
                "market_cap_percentage"
            ]["btc"]
        )

        change = float(
            obj[
                "market_cap_change_percentage_24h_usd"
            ]
        )

        return {
            "btc_dominance": dominance,
            "market_change": change
        }

    except Exception:

        return {
            "btc_dominance": None,
            "market_change": None
        }


# ============================================================
# NEWS
# ============================================================

NEWS_SEARCHES = [

    "Solana SOL crypto",

    "Solana ETF institutional",

    "SEC crypto regulation",

    "Federal Reserve crypto interest rates",

    "US inflation crypto markets",

    "Bitcoin ETF crypto market",

    "crypto liquidation market",

    "crypto hack exploit",

    "Trump tariffs financial markets",

    "global markets cryptocurrency"

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
    "cuts",
    "institutional",
    "investment",
    "partnership",
    "integration",
    "record"

]


NEGATIVE_TERMS = [

    "hack",
    "exploit",
    "outage",
    "ban",
    "lawsuit",
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
    "recession"
]


def get_news(
    query,
    limit=5
):

    url = (
        "https://news.google.com/rss/search?"
        + "q="
        + quote_plus(query)
        + "&hl=en-US&gl=US&ceid=US:en"
    )

    try:

        response = session.get(
            url,
            timeout=REQUEST_TIMEOUT
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

            link = item.findtext(
                "link",
                ""
            )

            pub_date = item.findtext(
                "pubDate",
                ""
            )

            if title:

                results.append({
                    "title": title,
                    "link": link,
                    "date": pub_date
                })

        return results

    except Exception:

        return []


def collect_news():

    results = []

    seen = set()

    # Only 5 searches to keep app fast

    for query in NEWS_SEARCHES[:5]:

        items = get_news(
            query,
            5
        )

        for item in items:

            key = item["title"].lower()

            if key in seen:
                continue

            seen.add(key)

            title_lower = key

            positive = sum(
                1
                for word in POSITIVE_TERMS
                if word in title_lower
            )

            negative = sum(
                1
                for word in NEGATIVE_TERMS
                if word in title_lower
            )

            if positive > negative:

                sentiment = "POSITIVE"

            elif negative > positive:

                sentiment = "NEGATIVE"

            else:

                sentiment = "NEUTRAL"

            item["sentiment"] = sentiment

            results.append(item)

    return results[:25]


def news_score(news):

    score = 0

    for item in news:

        if item["sentiment"] == "POSITIVE":

            score += 2

        elif item["sentiment"] == "NEGATIVE":

            score -= 2

    return max(
        -20,
        min(
            20,
            score
        )
    )


# ============================================================
# COMPLETE SCAN
# ============================================================

def run_scan():

    sol = get_market(
        "SOLUSDT"
    )

    btc = get_market(
        "BTCUSDT"
    )

    eth = get_market(
        "ETHUSDT"
    )

    technical = (
        technical_analysis()
    )

    fear_value, fear_label = (
        get_fear_greed()
    )

    global_market = (
        get_global_market()
    )

    news = collect_news()

    nscore = news_score(
        news
    )

    score = (
        technical["score"]
        + nscore
    )

    # Fear / Greed adjustment

    if fear_value is not None:

        adjustment = (
            fear_value - 50
        ) / 7

        score += max(
            -7,
            min(
                7,
                adjustment
            )
        )

    # Global market adjustment

    market_change = (
        global_market[
            "market_change"
        ]
    )

    if market_change is not None:

        score += max(
            -6,
            min(
                6,
                market_change * 1.5
            )
        )

    up = clamp(
        50 + score
    )

    down = (
        100 - up
    )

    confidence = clamp(
        50 + abs(score) * 1.4,
        50,
        92
    )

    return {

        "sol": sol,

        "btc": btc,

        "eth": eth,

        "technical": technical,

        "fear": fear_value,

        "fear_label": fear_label,

        "global": global_market,

        "news": news,

        "news_score": nscore,

        "score": score,

        "up": up,

        "down": down,

        "confidence": confidence,

        "time": datetime.now(
            timezone.utc
        ).strftime(
            "%H:%M:%S UTC"
        )
    }


# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(
    chat_id,
    message
):

    if not TELEGRAM_TOKEN:

        return (
            False,
            "Telegram token no configurado."
        )

    url = (
        "https://api.telegram.org/bot"
        + TELEGRAM_TOKEN
        + "/sendMessage"
    )

    try:

        response = session.post(
            url,
            data={
                "chat_id": chat_id,
                "text": message
            },
            timeout=8
        )

        data = response.json()

        if data.get("ok"):

            return (
                True,
                ""
            )

        return (
            False,
            data.get(
                "description",
                "Telegram error"
            )
        )

    except Exception as error:

        return (
            False,
            str(error)
        )


def detect_telegram_chat():

    if not TELEGRAM_TOKEN:

        return (
            None,
            "Token Telegram no configurado."
        )

    url = (
        "https://api.telegram.org/bot"
        + TELEGRAM_TOKEN
        + "/getUpdates"
    )

    try:

        response = session.get(
            url,
            params={
                "limit": 20
            },
            timeout=8
        )

        data = response.json()

        if not data.get("ok"):

            return (
                None,
                data.get(
                    "description",
                    "Telegram error"
                )
            )

        results = data.get(
            "result",
            []
        )

        for update in reversed(
            results
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

            if chat:

                return (
                    str(
                        chat.get("id")
                    ),
                    None
                )

        return (
            None,
            "No encontrado. Abre el bot y envía /start."
        )

    except Exception as error:

        return (
            None,
            str(error)
        )


# ============================================================
# HEADER - APPEARS IMMEDIATELY
# ============================================================

st.markdown(
    '<div class="title">🟣 SOL RADAR // QUANTUM</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">GLOBAL MULTI-VECTOR TRADING INTELLIGENCE // V3</div>',
    unsafe_allow_html=True
)

st.write("")


# ============================================================
# TOP CONTROL
# ============================================================

left, middle, right = st.columns(
    [2, 2, 1]
)

with left:

    scan = st.button(
        "⚡ SCAN SOL NOW",
        use_container_width=True,
        type="primary"
    )

with middle:

    st.info(
        "El análisis comienza al pulsar SCAN."
    )

with right:

    st.markdown(
        """
        <div class="small">
        SYSTEM<br>
        <span class="green">● ONLINE</span>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# INITIAL SCREEN
# ============================================================

if "radar_data" not in st.session_state:

    st.markdown(
        """
        <div class="radar-card">

        <h2>◉ SOL MARKET CONTROL</h2>

        <p class="small">
        SYSTEM READY
        </p>

        <br>

        <div class="purple"
        style="font-size:1.4rem">

        WAITING FOR MARKET SCAN...

        </div>

        <br>

        <p>
        El sistema analizará precio, tendencia,
        volumen, RSI, Fear & Greed, mercado global
        y noticias capaces de mover SOL.
        </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.stop()


# ============================================================
# RUN SCAN
# ============================================================

if scan:

    with st.spinner(
        "SCANNING GLOBAL MARKET..."
    ):

        st.session_state.radar_data = (
            run_scan()
        )


data = st.session_state.radar_data


# ============================================================
# VERDICT
# ============================================================

up = data["up"]

down = data["down"]

if up >= 65:

    verdict = "🟢 BULLISH BIAS"
    color_class = "green"

elif down >= 65:

    verdict = "🔴 BEARISH BIAS"
    color_class = "red"

else:

    verdict = "🟡 NEUTRAL / WAIT"
    color_class = "yellow"


st.markdown(
    f"""
    <div class="radar-card">

    <div class="{color_class}"
    style="font-size:1.5rem;font-weight:bold">

    {verdict}

    </div>

    <br>

    <div>
    CHANCE OF UP
    <b>{up}%</b>
    </div>

    <div class="progress-bg">
    <div
    class="progress-up"
    style="width:{up}%">
    </div>
    </div>

    <br>

    <div>
    CHANCE OF DOWN
    <b>{down}%</b>
    </div>

    <div class="progress-bg">
    <div
    class="progress-down"
    style="width:{down}%">
    </div>
    </div>

    <br>

    <div class="small">

    MODEL CONFIDENCE:
    {data["confidence"]:.0f}%

    &nbsp; | &nbsp;

    VECTOR SCORE:
    {data["score"]:+.1f}

    &nbsp; | &nbsp;

    {data["time"]}

    </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# MARKET METRICS
# ============================================================

st.markdown(
    "### 📡 LIVE MARKET"
)

c1, c2, c3, c4 = st.columns(4)


with c1:

    sol = data["sol"]

    if sol:

        st.metric(
            "SOL / USDT",
            money(sol["price"]),
            f'{sol["change"]:+.2f}%'
        )

    else:

        st.metric(
            "SOL / USDT",
            "N/D"
        )


with c2:

    btc = data["btc"]

    if btc:

        st.metric(
            "BTC",
            money(btc["price"]),
            f'{btc["change"]:+.2f}%'
        )

    else:

        st.metric(
            "BTC",
            "N/D"
        )


with c3:

    eth = data["eth"]

    if eth:

        st.metric(
            "ETH",
            money(eth["price"]),
            f'{eth["change"]:+.2f}%'
        )

    else:

        st.metric(
            "ETH",
            "N/D"
        )


with c4:

    fear = data["fear"]

    if fear is not None:

        st.metric(
            "FEAR / GREED",
            fear,
            data["fear_label"]
        )

    else:

        st.metric(
            "FEAR / GREED",
            "N/D"
        )


# ============================================================
# VECTOR ENGINE
# ============================================================

st.markdown(
    "### 🧬 VECTOR ENGINE"
)

technical = data["technical"]

v1, v2, v3, v4 = st.columns(4)


with v1:

    st.metric(
        "TECHNICAL",
        f'{technical["score"]:+.0f}'
    )


with v2:

    if technical["rsi"] is not None:

        st.metric(
            "RSI 1H",
            f'{technical["rsi"]:.1f}'
        )

    else:

        st.metric(
            "RSI 1H",
            "N/D"
        )


with v3:

    st.metric(
        "NEWS VECTOR",
        f'{data["news_score"]:+.0f}'
    )


with v4:

    if technical["volume_ratio"]:

        st.metric(
            "VOLUME",
            f'{technical["volume_ratio"]:.2f}x'
        )

    else:

        st.metric(
            "VOLUME",
            "N/D"
        )


# ============================================================
# TECHNICAL DETAILS
# ============================================================

with st.expander(
    "📊 TECHNICAL MATRIX"
):

    t1, t2, t3, t4 = st.columns(4)

    with t1:

        st.write("SMA 20")

        st.write(
            money(
                technical["sma20"]
            )
        )

    with t2:

        st.write("SMA 50")

        st.write(
            money(
                technical["sma50"]
            )
        )

    with t3:

        st.write("RSI")

        if technical["rsi"]:

            st.write(
                f'{technical["rsi"]:.2f}'
            )

    with t4:

        st.write("Volume / Average")

        if technical["volume_ratio"]:

            st.write(
                f'{technical["volume_ratio"]:.2f}x'
            )

    if technical["prices"]:

        st.line_chart(
            technical["prices"],
            height=260
        )


# ============================================================
# GLOBAL MARKET
# ============================================================

st.markdown(
    "### 🌍 GLOBAL VECTOR"
)

g1, g2 = st.columns(2)

with g1:

    dominance = data[
        "global"
    ]["btc_dominance"]

    if dominance is not None:

        st.metric(
            "BTC DOMINANCE",
            f"{dominance:.2f}%"
        )

    else:

        st.metric(
            "BTC DOMINANCE",
            "N/D"
        )


with g2:

    change = data[
        "global"
    ]["market_change"]

    if change is not None:

        st.metric(
            "TOTAL CRYPTO MARKET 24H",
            f"{change:+.2f}%"
        )

    else:

        st.metric(
            "TOTAL CRYPTO MARKET 24H",
            "N/D"
        )


# ============================================================
# NEWS
# ============================================================

st.markdown(
    "### 🌐 GLOBAL INTELLIGENCE STREAM"
)

news = data["news"]

if not news:

    st.warning(
        "No se pudieron recuperar noticias en este momento."
    )

else:

    for item in news:

        sentiment = item[
            "sentiment"
        ]

        if sentiment == "POSITIVE":

            css = "news-positive"

            icon = "🟢"

        elif sentiment == "NEGATIVE":

            css = "news-negative"

            icon = "🔴"

        else:

            css = ""

            icon = "⚪"

        title = html.escape(
            item["title"]
        )

        link = html.escape(
            item["link"]
        )

        date = html.escape(
            item["date"]
        )

        st.markdown(
            f"""
            <div class="news-card {css}">

            {icon}
            <b>{title}</b>

            <div class="small">

            {sentiment}
            &nbsp; • &nbsp;
            {date}

            &nbsp; • &nbsp;

            <a
            href="{link}"
            target="_blank">

            SOURCE

            </a>

            </div>

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# TELEGRAM
# ============================================================

st.markdown(
    "### 📲 TELEGRAM CONTROL"
)

if not TELEGRAM_TOKEN:

    st.warning(
        "Telegram no está configurado todavía. "
        "Añade [telegram] en Streamlit Secrets."
    )

else:

    tg1, tg2 = st.columns(2)

    with tg1:

        if st.button(
            "🔎 DETECT CHAT ID",
            use_container_width=True
        ):

            chat_id, error = (
                detect_telegram_chat()
            )

            if chat_id:

                st.success(
                    "CHAT ID DETECTADO"
                )

                st.code(
                    chat_id
                )

            else:

                st.error(
                    error
                )

    with tg2:

        chat_id = (
            TELEGRAM_CHAT_ID
        )

        if not chat_id:

            chat_id = st.text_input(
                "Telegram Chat ID"
            )

        if st.button(
            "🚨 SEND SOL ALERT",
            use_container_width=True
        ):

            if not chat_id:

                st.error(
                    "Introduce primero el Chat ID."
                )

            else:

                message = (

                    "🟣 SOL RADAR V3\n\n"

                    f"{verdict}\n\n"

                    f"⬆️ SUBIDA: {up}%\n"

                    f"⬇️ BAJADA: {down}%\n\n"

                    f"🎯 CONFIANZA: "
                    f"{data['confidence']:.0f}%\n\n"

                    f"🧬 TECHNICAL: "
                    f"{data['technical']['score']:+.0f}\n"

                    f"🌐 NEWS: "
                    f"{data['news_score']:+.0f}\n\n"

                    "⚠️ Probabilidad del modelo, "
                    "no garantía de precio."
                )

                ok, error = send_telegram(
                    chat_id,
                    message
                )

                if ok:

                    st.success(
                        "Telegram enviado correctamente."
                    )

                else:

                    st.error(
                        f"Telegram: {error}"
                    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <br><br>

    <div class="footer">

    SOL RADAR V3
    //
    MULTI-VECTOR MARKET INTELLIGENCE
    //
    NOT FINANCIAL ADVICE

    </div>
    """,
    unsafe_allow_html=True
)
