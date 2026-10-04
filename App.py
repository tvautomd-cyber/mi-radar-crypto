import streamlit as st
import requests
import time
import html
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed


# ============================================================
# SOL VECTOR RADAR
# Version limpia para Streamlit Cloud
# Sin Plotly
# Sin triple-quoted strings
# ============================================================

st.set_page_config(
    page_title="SOL VECTOR RADAR",
    page_icon="🟣",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# CONFIG
# ============================================================

BINANCE_SYMBOL = "SOLUSDT"
REQUEST_TIMEOUT = 5

NEWS_QUERIES = [
    "Solana SOL crypto",
    "Solana ETF SEC crypto",
    "Federal Reserve interest rates crypto",
    "US inflation jobs dollar crypto",
    "Bitcoin Ethereum crypto market",
    "Trump tariffs financial markets crypto",
    "crypto exchange hack exploit",
    "geopolitics oil markets crypto"
]


# ============================================================
# SECRETS
# ============================================================

def get_secret(name, default=""):
    try:
        value = st.secrets.get(name, default)
        if value is None:
            return default
        return str(value)
    except Exception:
        return default


TELEGRAM_TOKEN = get_secret("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = get_secret("TELEGRAM_CHAT_ID")


# ============================================================
# CSS
# ============================================================

CSS = "\n".join([
    "<style>",
    ".stApp {",
    "    background:#05070b;",
    "    color:#d9dee7;",
    "}",
    "",
    "[data-testid='stHeader'] {",
    "    background:#05070b;",
    "}",
    "",
    ".block-container {",
    "    max-width:1450px;",
    "    padding-top:1.2rem;",
    "    padding-bottom:3rem;",
    "}",
    "",
    ".terminal {",
    "    background:#080b11;",
    "    border:1px solid #202733;",
    "    border-radius:12px;",
    "    padding:18px;",
    "    margin-bottom:14px;",
    "    box-shadow:0 0 18px rgba(0,0,0,.25);",
    "}",
    "",
    ".header-title {",
    "    color:#f5f7fa;",
    "    font-size:31px;",
    "    font-weight:900;",
    "    letter-spacing:3px;",
    "}",
    "",
    ".header-sub {",
    "    color:#697586;",
    "    font-size:11px;",
    "    letter-spacing:2px;",
    "    margin-bottom:18px;",
    "}",
    "",
    ".big-number {",
    "    font-size:38px;",
    "    font-weight:900;",
    "}",
    "",
    ".metric-label {",
    "    color:#727d8d;",
    "    font-size:11px;",
    "    letter-spacing:1px;",
    "}",
    "",
    ".green {",
    "    color:#00ff9d !important;",
    "}",
    "",
    ".red {",
    "    color:#ff4d67 !important;",
    "}",
    "",
    ".purple {",
    "    color:#a970ff !important;",
    "}",
    "",
    ".orange {",
    "    color:#ffb347 !important;",
    "}",
    "",
    ".gray {",
    "    color:#7c8797 !important;",
    "}",
    "",
    ".signal-box {",
    "    background:linear-gradient(135deg,#0b0712,#090b12);",
    "    border:1px solid #7c3aed;",
    "    border-radius:14px;",
    "    padding:22px;",
    "    box-shadow:0 0 25px rgba(124,58,237,.12);",
    "}",
    "",
    ".news-row {",
    "    background:#080b11;",
    "    border-bottom:1px solid #1b222d;",
    "    padding:12px 4px;",
    "}",
    "",
    ".source {",
    "    color:#697586;",
    "    font-size:11px;",
    "    margin-top:4px;",
    "}",
    "",
    ".tiny {",
    "    color:#687385;",
    "    font-size:10px;",
    "}",
    "",
    ".status-online {",
    "    color:#00ff9d;",
    "    font-weight:800;",
    "}",
    "",
    ".status-offline {",
    "    color:#ff4d67;",
    "    font-weight:800;",
    "}",
    "",
    "</style>"
])

st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
# HTTP
# ============================================================

def get_json(url, params=None):
    try:
        response = requests.get(
            url,
            params=params,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": "SOL-Vector-Radar/2.0"
            }
        )

        if response.status_code != 200:
            return None

        return response.json()

    except Exception:
        return None


def get_text(url, params=None):
    try:
        response = requests.get(
            url,
            params=params,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": "SOL-Vector-Radar/2.0"
            }
        )

        if response.status_code != 200:
            return ""

        return response.text

    except Exception:
        return ""


# ============================================================
# COINGECKO
# ============================================================

@st.cache_data(ttl=30)
def get_market_data():

    data = get_json(
        "https://api.coingecko.com/api/v3/simple/price",
        {
            "ids": "solana,bitcoin,ethereum",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_market_cap": "true"
        }
    )

    empty = {
        "sol": 0.0,
        "sol_change": 0.0,
        "sol_volume": 0.0,
        "sol_market_cap": 0.0,
        "btc": 0.0,
        "btc_change": 0.0,
        "eth": 0.0,
        "eth_change": 0.0
    }

    if not isinstance(data, dict):
        return empty

    sol = data.get("solana", {})
    btc = data.get("bitcoin", {})
    eth = data.get("ethereum", {})

    return {
        "sol": float(sol.get("usd", 0) or 0),
        "sol_change": float(sol.get("usd_24h_change", 0) or 0),
        "sol_volume": float(sol.get("usd_24h_vol", 0) or 0),
        "sol_market_cap": float(sol.get("usd_market_cap", 0) or 0),

        "btc": float(btc.get("usd", 0) or 0),
        "btc_change": float(btc.get("usd_24h_change", 0) or 0),

        "eth": float(eth.get("usd", 0) or 0),
        "eth_change": float(eth.get("usd_24h_change", 0) or 0)
    }


# ============================================================
# BINANCE FUTURES
# ============================================================

def get_binance_ticker():
    return get_json(
        "https://fapi.binance.com/fapi/v1/ticker/24hr",
        {"symbol": BINANCE_SYMBOL}
    )


def get_binance_open_interest():
    return get_json(
        "https://fapi.binance.com/fapi/v1/openInterest",
        {"symbol": BINANCE_SYMBOL}
    )


def get_binance_funding():
    return get_json(
        "https://fapi.binance.com/fapi/v1/premiumIndex",
        {"symbol": BINANCE_SYMBOL}
    )


def get_binance_long_short():
    return get_json(
        "https://fapi.binance.com/futures/data/globalLongShortAccountRatio",
        {
            "symbol": BINANCE_SYMBOL,
            "period": "5m",
            "limit": 1
        }
    )


def get_binance_taker():
    return get_json(
        "https://fapi.binance.com/futures/data/takerlongshortRatio",
        {
            "symbol": BINANCE_SYMBOL,
            "period": "5m",
            "limit": 1
        }
    )


@st.cache_data(ttl=30)
def get_futures_data():

    functions = [
        get_binance_ticker,
        get_binance_open_interest,
        get_binance_funding,
        get_binance_long_short,
        get_binance_taker
    ]

    results = []

    with ThreadPoolExecutor(max_workers=5) as executor:

        jobs = [executor.submit(fn) for fn in functions]

        for job in jobs:
            try:
                results.append(job.result())
            except Exception:
                results.append(None)

    ticker = results[0]
    open_interest = results[1]
    funding = results[2]
    long_short = results[3]
    taker = results[4]

    result = {
        "change": 0.0,
        "volume": 0.0,
        "open_interest": 0.0,
        "funding": 0.0,
        "long_pct": 50.0,
        "short_pct": 50.0,
        "taker_ratio": 1.0
    }

    if isinstance(ticker, dict):
        result["change"] = float(
            ticker.get("priceChangePercent", 0) or 0
        )

        result["volume"] = float(
            ticker.get("quoteVolume", 0) or 0
        )

    if isinstance(open_interest, dict):
        result["open_interest"] = float(
            open_interest.get("openInterest", 0) or 0
        )

    if isinstance(funding, dict):
        result["funding"] = (
            float(funding.get("lastFundingRate", 0) or 0) * 100
        )

    if isinstance(long_short, list) and len(long_short) > 0:

        row = long_short[0]

        long_value = float(
            row.get("longAccount", 0.5) or 0.5
        )

        short_value = float(
            row.get("shortAccount", 0.5) or 0.5
        )

        total = long_value + short_value

        if total > 0:
            result["long_pct"] = (
                long_value / total * 100
            )

            result["short_pct"] = (
                short_value / total * 100
            )

    if isinstance(taker, list) and len(taker) > 0:

        result["taker_ratio"] = float(
            taker[0].get("buySellRatio", 1) or 1
        )

    return result


# ============================================================
# FEAR & GREED
# ============================================================

@st.cache_data(ttl=300)
def get_fear_greed():

    data = get_json(
        "https://api.alternative.me/fng/",
        {"limit": 1}
    )

    if (
        isinstance(data, dict)
        and isinstance(data.get("data"), list)
        and len(data["data"]) > 0
    ):

        row = data["data"][0]

        try:
            value = int(row.get("value", 50))
        except Exception:
            value = 50

        label = str(
            row.get(
                "value_classification",
                "Neutral"
            )
        )

        return value, label

    return 50, "Neutral"


# ============================================================
# NEWS
# ============================================================

def read_news_feed(query):

    url = (
        "https://news.google.com/rss/search?q="
        + quote_plus(query)
        + "&hl=en-US&gl=US&ceid=US:en"
    )

    xml = get_text(url)

    if not xml:
        return []

    articles = []

    try:

        root = ET.fromstring(xml)

        items = root.findall(".//item")

        for item in items[:6]:

            title = item.findtext("title") or ""
            link = item.findtext("link") or ""
            date = item.findtext("pubDate") or ""
            source = item.findtext("source") or "News"

            if title.strip():

                articles.append({
                    "title": title.strip(),
                    "link": link.strip(),
                    "date": date.strip(),
                    "source": source.strip()
                })

    except Exception:
        return []

    return articles


@st.cache_data(ttl=180)
def get_global_news():

    all_articles = []

    with ThreadPoolExecutor(max_workers=8) as executor:

        futures = [
            executor.submit(read_news_feed, query)
            for query in NEWS_QUERIES
        ]

        for future in as_completed(futures):

            try:
                data = future.result()

                if data:
                    all_articles.extend(data)

            except Exception:
                pass

    unique = []
    seen = set()

    for article in all_articles:

        key = article["title"].lower().strip()

        if key not in seen:

            seen.add(key)
            unique.append(article)

    return unique[:40]


# ============================================================
# SENTIMENT / SIGNAL ENGINE
# ============================================================

def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def calculate_signal(
    market,
    futures,
    fear_value,
    news_count
):

    score = 50.0
    reasons = []

    # -------------------------
    # SOL MOMENTUM
    # -------------------------

    if market["sol_change"] >= 4:
        score += 12
        reasons.append(
            "Momentum SOL claramente positivo"
        )

    elif market["sol_change"] >= 1:
        score += 6
        reasons.append(
            "Momentum SOL positivo"
        )

    elif market["sol_change"] <= -4:
        score -= 12
        reasons.append(
            "Momentum SOL claramente negativo"
        )

    elif market["sol_change"] <= -1:
        score -= 6
        reasons.append(
            "Momentum SOL negativo"
        )

    # -------------------------
    # BTC
    # -------------------------

    if market["btc_change"] >= 2:
        score += 6
        reasons.append(
            "BTC confirma fortaleza del mercado"
        )

    elif market["btc_change"] <= -2:
        score -= 6
        reasons.append(
            "BTC está presionando al mercado"
        )

    # -------------------------
    # LONG / SHORT
    # -------------------------

    if futures["long_pct"] >= 57:
        score += 5
        reasons.append(
            "Predominio de cuentas Long"
        )

    elif futures["long_pct"] <= 43:
        score -= 5
        reasons.append(
            "Predominio de cuentas Short"
        )

    # -------------------------
    # TAKER FLOW
    # -------------------------

    if futures["taker_ratio"] >= 1.10:
        score += 7
        reasons.append(
            "Flujo agresivo de compradores"
        )

    elif futures["taker_ratio"] <= 0.90:
        score -= 7
        reasons.append(
            "Flujo agresivo de vendedores"
        )

    # -------------------------
    # FUNDING
    # -------------------------

    if futures["funding"] > 0.05:
        score -= 4
        reasons.append(
            "Funding elevado: posible saturación Long"
        )

    elif futures["funding"] < -0.03:
        score += 3
        reasons.append(
            "Funding negativo: presión Long reducida"
        )

    # -------------------------
    # FEAR & GREED
    # -------------------------

    if fear_value >= 80:
        score += 3
        reasons.append(
            "Sentimiento global muy optimista"
        )

    elif fear_value <= 20:
        score -= 3
        reasons.append(
            "Sentimiento global muy defensivo"
        )

    # -------------------------
    # CONFIDENCE
    # -------------------------

    confidence = 45 + min(
        news_count * 1.5,
        35
    )

    score = clamp(score, 5, 95)

    return score, confidence, reasons


# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(message):

    if not TELEGRAM_TOKEN:
        return False, "Falta TELEGRAM_TOKEN en Secrets."

    if not TELEGRAM_CHAT_ID:
        return False, "Falta TELEGRAM_CHAT_ID en Secrets."

    url = (
        "https://api.telegram.org/bot"
        + TELEGRAM_TOKEN
        + "/sendMessage"
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": True
    }

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )

        if response.ok:
            return True, "Telegram: mensaje enviado correctamente."

        return False, (
            "Telegram respondió HTTP "
            + str(response.status_code)
        )

    except Exception as exc:

        return False, (
            "Error de conexión Telegram: "
            + str(exc)
        )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    "<div class='header-title'>🟣 SOL VECTOR RADAR</div>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='header-sub'>"
    "MULTI-SOURCE INTELLIGENCE & MACRO RADAR V2.0</div>",
    unsafe_allow_html=True
)


# ============================================================
# MAIN EXECUTION & DASHBOARD LAYOUT
# ============================================================

market = get_market_data()
futures = get_futures_data()
fear_value, fear_label = get_fear_greed()
news_articles = get_global_news()

score, confidence, reasons = calculate_signal(
    market,
    futures,
    fear_value,
    len(news_articles)
)

# Sidebar para alertas de Telegram y controles
with st.sidebar:
    st.markdown("### ⚙️ Panel de Control")
    st.write(f"Estado de Telegram: {'✅ Configurado' if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID else '⚠️ No Configurado'}")
    
    custom_msg = st.text_input("Mensaje personalizado", "Radar alerta manual")
    if st.button("Enviar Alerta a Telegram"):
        success, msg = send_telegram(custom_msg)
        if success:
            st.success(msg)
        else:
            st.error(msg)
            
    if st.button("Enviar Señal Actual"):
        signal_text = f"🟣 SOL VECTOR RADAR\nScore: {score:.1f}/100\nConfianza: {confidence}%\nPrecio SOL: ${market['sol']}"
        success, msg = send_telegram(signal_text)
        if success:
            st.success("Señal enviada a Telegram.")
        else:
            st.error(msg)

    st.markdown("---")
    if st.button("🔄 Refrescar Datos"):
        st.cache_data.clear()
        st.rerun()

# Pestañas principales
tab1, tab2 = st.tabs(["📊 Radar & Métricas", "📰 Noticias Globales"])

with tab1:
    col1, col2 = st.columns([1.2, 1.8], gap="medium")
    
    with col1:
        st.markdown("<div class='signal-box'>", unsafe_allow_html=True)
        st.markdown("### 🎯 Vector Signal Engine", unsafe_allow_html=True)
        
        color_class = "green" if score >= 60 else ("red" if score <= 40 else "purple")
        st.markdown(f"<div class='big-number {color_class}'>{score:.1f} <span style='font-size:16px;color:#7c8797;'>/100</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-label'>CONFIANZA: {confidence}%</div>", unsafe_allow_html=True)
        
        st.markdown("<br><b>Factores Clave:</b>", unsafe_allow_html=True)
        if reasons:
            for r in reasons:
                st.markdown(f"- {r}")
        else:
            st.markdown("- Mercado en rango / sin catalizadores fuertes")
            
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col2:
        st.markdown("<div class='terminal'>", unsafe_allow_html=True)
        st.markdown("### 📊 Métricas del Mercado", unsafe_allow_html=True)
        
        m_cols = st.columns(3)
        with m_cols[0]:
            st.metric("Solana (SOL)", f"${market['sol']:,.2f}", f"{market['sol_change']:+.2f}%")
        with m_cols[1]:
            st.metric("Bitcoin (BTC)", f"${market['btc']:,.2f}", f"{market['btc_change']:+.2f}%")
        with m_cols[2]:
            st.metric("Ethereum (ETH)", f"${market['eth']:,.2f}", f"{market['eth_change']:+.2f}%")
            
        st.markdown("<hr style='border-color:#202733;'>", unsafe_allow_html=True)
        
        f_cols = st.columns(3)
        with f_cols[0]:
            st.metric("Open Interest", f"${futures['open_interest']:,.0f}")
        with f_cols[1]:
            st.metric("Funding Rate", f"{futures['funding']:.4f}%")
        with f_cols[2]:
            st.metric("Fear & Greed", f"{fear_value} ({fear_label})")
            
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='terminal'>", unsafe_allow_html=True)
    st.markdown("### ⚡ Derivados Binance Futures (SOLUSDT)", unsafe_allow_html=True)
    
    d_cols = st.columns(4)
    with d_cols[0]:
        st.metric("Volume 24h", f"${market['sol_volume']:,.0f}")
    with d_cols[1]:
        st.metric("Ratio Long / Short", f"L: {futures['long_pct']:.1f}% / S: {futures['short_pct']:.1f}%")
    with d_cols[2]:
        st.metric("Taker Buy/Sell Ratio", f"{futures['taker_ratio']:.2f}")
    with d_cols[3]:
        st.metric("Cambio 24h (Futures)", f"{futures['change']:+.2f}%")
        
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<div class='terminal'>", unsafe_allow_html=True)
    st.markdown("### 📰 Últimas Noticias Globales y Cripto", unsafe_allow_html=True)
    
    if not news_articles:
        st.info("No se pudieron cargar las noticias en este momento o la red está limitada.")
    else:
        for article in news_articles:
            st.markdown(
                f"<div class='news-row'>"
                f"<a href='{article['link']}' target='_blank' style='color:#f5f7fa;text-decoration:none;font-weight:600;'>{html.escape(article['title'])}</a>"
                f"<div class='source'>{html.escape(article['source'])} &bull; <span class='tiny'>{html.escape(article['date'])}</span></div>"
                f"</div>",
                unsafe_allow_html=True
            )
            
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    "<div style='text-align:center;color:#697586;font-size:11px;margin-top:30px;letter-spacing:1px;'>"
    "SOL VECTOR RADAR &bull; Creado para Streamlit Cloud &bull; Sin dependencias pesadas de gráficos"
    "</div>",
    unsafe_allow_html=True
)
