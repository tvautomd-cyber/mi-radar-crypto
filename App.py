import streamlit as st
import requests
import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================
# SOL RADAR V4
# FAST / PARALLEL / FAIL-SAFE
# ============================================================

st.set_page_config(
    page_title="SOL RADAR // V4",
    page_icon="🟣",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CONFIG
# ============================================================

TIMEOUT = 3

HEADERS = {
    "User-Agent": "Mozilla/5.0 SOL-RADAR-V4"
}


# ============================================================
# TELEGRAM SECRETS
# ============================================================

def get_secret(section, key):

    try:
        value = st.secrets[section][key]

        if value:
            return str(value).strip()

    except Exception:
        pass

    return ""


TELEGRAM_TOKEN = get_secret(
    "telegram",
    "token"
)

TELEGRAM_CHAT_ID = get_secret(
    "telegram",
    "chat_id"
)


# ============================================================
# SESSION
# ============================================================

def request_json(url, params=None):

    try:

        r = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=TIMEOUT
        )

        if r.status_code != 200:
            return None

        return r.json()

    except Exception:

        return None


# ============================================================
# UTILITIES
# ============================================================

def clamp(value, low=5, high=95):

    return max(
        low,
        min(
            high,
            int(round(value))
        )
    )


def money(value):

    if value is None:
        return "N/D"

    if abs(value) >= 1000:
        return f"${value:,.0f}"

    return f"${value:,.4f}"


def clean_text(text):

    if not text:
        return ""

    text = re.sub(
        r"<[^>]+>",
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
# CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background:
        radial-gradient(
            circle at 85% 5%,
            rgba(120,40,255,.18),
            transparent 28%
        ),
        radial-gradient(
            circle at 10% 30%,
            rgba(0,170,255,.07),
            transparent 25%
        ),
        #040609;

    color:#d9dce4;
}

.block-container {
    max-width:1500px;
    padding-top:1rem;
}

.title {
    font-family:
        "Courier New",
        monospace;

    font-size:2.5rem;
    font-weight:900;

    color:#b86cff;

    text-shadow:
        0 0 12px
        rgba(150,70,255,.7);
}

.subtitle {
    font-family:
        "Courier New",
        monospace;

    color:#596273;
    letter-spacing:2px;
}

.card {
    background:
        linear-gradient(
            145deg,
            #090c12,
            #12091c
        );

    border:1px solid #6230bd;

    border-radius:16px;

    padding:22px;

    box-shadow:
        0 0 30px
        rgba(110,40,255,.12);
}

.metric {
    background:#080b10;

    border:1px solid #202632;

    border-radius:10px;

    padding:14px;
}

.green {
    color:#00ff88 !important;
}

.red {
    color:#ff4260 !important;
}

.yellow {
    color:#ffc857 !important;
}

.purple {
    color:#b86cff !important;
}

.small {
    color:#697284;
    font-size:.75rem;
}

.news {
    background:#080b10;

    border-left:3px solid #8b4dff;

    padding:11px;

    margin-bottom:7px;

    border-radius:5px;
}

.news-positive {
    border-left-color:#00ff88;
}

.news-negative {
    border-left-color:#ff4260;
}

.bar-bg {
    width:100%;
    height:15px;

    background:#171b24;

    border-radius:10px;

    overflow:hidden;
}

.bar-up {
    height:100%;
    background:#00e878;
}

.bar-down {
    height:100%;
    background:#ff3454;
}

.source-ok {
    color:#00ff88;
}

.source-fail {
    color:#ff4260;
}

.footer {
    text-align:center;

    color:#414856;

    font-size:.7rem;

    font-family:
        "Courier New",
        monospace;
}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# MARKET DATA
# ============================================================

def get_binance(symbol):

    data = request_json(
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


def get_candles():

    data = request_json(
        "https://api.binance.com/api/v3/klines",
        {
            "symbol": "SOLUSDT",
            "interval": "1h",
            "limit": 100
        }
    )

    if not data:
        return []

    return data


# ============================================================
# TECHNICAL ANALYSIS
# ============================================================

def calculate_technical(candles):

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
        float(x[4])
        for x in candles
    ]

    volumes = [
        float(x[5])
        for x in candles
    ]

    sma20 = (
        sum(closes[-20:])
        / 20
    )

    sma50 = (
        sum(closes[-50:])
        / 50
    )

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
            - 100 / (1 + rs)
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

    if closes[-1] > sma20:
        score += 10
    else:
        score -= 10

    if sma20 > sma50:
        score += 12
    else:
        score -= 12

    if 50 <= rsi <= 68:
        score += 8

    elif rsi > 75:
        score -= 8

    elif rsi < 30:
        score += 6

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

    data = request_json(
        "https://api.alternative.me/fng/",
        {
            "limit": 1
        }
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
            "ok": True
        }

    except Exception:

        return {
            "value": None,
            "label": "N/D",
            "ok": False
        }


# ============================================================
# GLOBAL MARKET
# ============================================================

def get_global():

    data = request_json(
        "https://api.coingecko.com/api/v3/global"
    )

    try:

        obj = data["data"]

        return {
            "btc_dominance":
                float(
                    obj[
                        "market_cap_percentage"
                    ]["btc"]
                ),

            "change":
                float(
                    obj[
                        "market_cap_change_percentage_24h_usd"
                    ]
                ),

            "ok": True
        }

    except Exception:

        return {
            "btc_dominance": None,
            "change": None,
            "ok": False
        }


# ============================================================
# NEWS
# ============================================================

NEWS_QUERIES = [

    "Solana SOL crypto",

    "Solana ETF institutional",

    "SEC crypto regulation",

    "Federal Reserve crypto Bitcoin",

    "crypto market liquidation hack"

]


POSITIVE = [
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
    "record"
]


NEGATIVE = [
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
    "recession"
]


def fetch_news(query):

    url = (
        "https://news.google.com/rss/search?"
        + "q="
        + quote_plus(query)
        + "&hl=en-US&gl=US&ceid=US:en"
    )

    try:

        r = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT
        )

        if r.status_code != 200:
            return []

        root = ET.fromstring(
            r.content
        )

        result = []

        for item in root.findall(
            "./channel/item"
        )[:4]:

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

            if not title:
                continue

            low = title.lower()

            pos = sum(
                word in low
                for word in POSITIVE
            )

            neg = sum(
                word in low
                for word in NEGATIVE
            )

            if pos > neg:
                sentiment = "POSITIVE"

            elif neg > pos:
                sentiment = "NEGATIVE"

            else:
                sentiment = "NEUTRAL"

            result.append({
                "title": title,
                "link": link,
                "date": pub_date,
                "sentiment": sentiment
            })

        return result

    except Exception:

        return []


def get_all_news():

    all_news = []

    # IMPORTANT:
    # All searches run simultaneously.

    with ThreadPoolExecutor(
        max_workers=5
    ) as executor:

        futures = [
            executor.submit(
                fetch_news,
                q
            )
            for q in NEWS_QUERIES
        ]

        for future in as_completed(
            futures
        ):

            try:

                all_news.extend(
                    future.result()
                )

            except Exception:

                pass

    unique = {}

    for item in all_news:

        key = item[
            "title"
        ].lower()

        if key not in unique:

            unique[key] = item

    return list(
        unique.values()
    )[:20]


def calculate_news_score(news):

    score = 0

    for item in news:

        if item[
            "sentiment"
        ] == "POSITIVE":

            score += 2

        elif item[
            "sentiment"
        ] == "NEGATIVE":

            score -= 2

    return max(
        -20,
        min(
            20,
            score
        )
    )


# ============================================================
# PARALLEL DATA COLLECTION
# ============================================================

def perform_scan():

    results = {}

    # --------------------------------------------------------
    # FIRST GROUP
    # --------------------------------------------------------

    tasks = {

        "sol":
            ("binance",
             "SOLUSDT"),

        "btc":
            ("binance",
             "BTCUSDT"),

        "eth":
            ("binance",
             "ETHUSDT"),

        "candles":
            ("candles",
             None),

        "fear":
            ("fear",
             None),

        "global":
            ("global",
             None),

        "news":
            ("news",
             None)

    }

    def worker(name, kind, argument):

        if kind == "binance":

            return name, get_binance(
                argument
            )

        if kind == "candles":

            return name, get_candles()

        if kind == "fear":

            return name, get_fear_greed()

        if kind == "global":

            return name, get_global()

        if kind == "news":

            return name, get_all_news()

        return name, None

    start = datetime.now(
        timezone.utc
    )

    with ThreadPoolExecutor(
        max_workers=7
    ) as executor:

        futures = []

        for name, item in tasks.items():

            futures.append(
                executor.submit(
                    worker,
                    name,
                    item[0],
                    item[1]
                )
            )

        for future in as_completed(
            futures
        ):

            try:

                name, value = (
                    future.result()
                )

                results[name] = value

            except Exception:

                pass

    # --------------------------------------------------------
    # TECHNICAL
    # --------------------------------------------------------

    technical = calculate_technical(
        results.get(
            "candles",
            []
        )
    )

    news = results.get(
        "news",
        []
    )

    news_score = calculate_news_score(
        news
    )

    score = (
        technical["score"]
        + news_score
    )

    fear = results.get(
        "fear",
        {}
    )

    fear_value = fear.get(
        "value"
    )

    if fear_value is not None:

        score += max(
            -7,
            min(
                7,
                (fear_value - 50) / 7
            )
        )

    global_data = results.get(
        "global",
        {}
    )

    global_change = global_data.get(
        "change"
    )

    if global_change is not None:

        score += max(
            -6,
            min(
                6,
                global_change * 1.5
            )
        )

    up = clamp(
        50 + score
    )

    down = (
        100 - up
    )

    confidence = clamp(
        50 + abs(score) * 1.5,
        50,
        92
    )

    elapsed = (
        datetime.now(
            timezone.utc
        )
        - start
    ).total_seconds()

    return {

        "sol":
            results.get(
                "sol"
            ),

        "btc":
            results.get(
                "btc"
            ),

        "eth":
            results.get(
                "eth"
            ),

        "technical":
            technical,

        "fear":
            fear,

        "global":
            global_data,

        "news":
            news,

        "news_score":
            news_score,

        "score":
            score,

        "up":
            up,

        "down":
            down,

        "confidence":
            confidence,

        "elapsed":
            elapsed,

        "time":
            datetime.now(
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

        return False, "TOKEN NO CONFIGURADO"

    try:

        url = (
            "https://api.telegram.org/bot"
            + TELEGRAM_TOKEN
            + "/sendMessage"
        )

        r = requests.post(
            url,
            data={
                "chat_id": chat_id,
                "text": message
            },
            timeout=5
        )

        data = r.json()

        if data.get("ok"):

            return True, ""

        return False, data.get(
            "description",
            "Telegram error"
        )

    except Exception as e:

        return False, str(e)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="title">🟣 SOL RADAR // QUANTUM</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">MULTI-VECTOR SOLANA MARKET INTELLIGENCE // V4</div>',
    unsafe_allow_html=True
)

st.write("")


# ============================================================
# SCAN BUTTON
# ============================================================

col1, col2, col3 = st.columns(
    [2, 2, 1]
)

with col1:

    scan = st.button(
        "⚡ SCAN SOL NOW",
        type="primary",
        use_container_width=True
    )

with col2:

    st.markdown(
        """
        <div class="small">
        ENGINE:
        <span class="green">
        PARALLEL MODE
        </span>
        <br>
        APIs: Binance / CoinGecko /
        Fear&Greed / Global News
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:

    st.markdown(
        """
        <div class="small">
        SYSTEM<br>
        <span class="green">
        ● READY
        </span>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# INITIAL
# ============================================================

if "radar" not in st.session_state:

    st.markdown(
        """
        <div class="card">

        <h2>◉ SOL MARKET CONTROL</h2>

        <p class="small">
        QUANTUM ENGINE READY
        </p>

        <br>

        <div class="purple"
        style="font-size:1.5rem">

        WAITING FOR SCAN...

        </div>

        <br>

        <p>
        Pulsa SCAN SOL NOW para analizar
        el mercado.
        </p>

        </div>
        """,
        unsafe_allow_html=True
    )

else:

    data = st.session_state.radar

    # ========================================================
    # VERDICT
    # ========================================================

    up = data["up"]
    down = data["down"]

    if up >= 65:

        verdict = "🟢 BULLISH BIAS"
        cls = "green"

    elif down >= 65:

        verdict = "🔴 BEARISH BIAS"
        cls = "red"

    else:

        verdict = "🟡 NEUTRAL / WAIT"
        cls = "yellow"

    st.markdown(
        f"""
        <div class="card">

        <div class="{cls}"
        style="font-size:1.6rem;font-weight:bold">

        {verdict}

        </div>

        <br>

        <div>
        ⬆️ CHANCE UP:
        <b>{up}%</b>
        </div>

        <div class="bar-bg">
        <div
        class="bar-up"
        style="width:{up}%">
        </div>
       
