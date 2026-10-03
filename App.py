import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timezone
from urllib.parse import quote

# ============================================================
# QUANTUM SOLANA INTELLIGENCE TERMINAL
# SOL ONLY
# ============================================================

st.set_page_config(
    page_title="QUANTUM // SOL INTELLIGENCE",
    page_icon="🟣",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CONFIG
# ============================================================

TELEGRAM_TOKEN = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")
TELEGRAM_USERNAME = st.secrets.get(
    "TELEGRAM_BOT_USERNAME",
    "Mycrypto_best_bot"
)

COINGECKO = "https://api.coingecko.com/api/v3"
FEAR_GREED = "https://api.alternative.me/fng/"
BINANCE = "https://api.binance.com/api/v3"

# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>

.stApp {
    background:
        radial-gradient(circle at top right, rgba(120,40,255,.08), transparent 35%),
        radial-gradient(circle at bottom left, rgba(0,255,170,.04), transparent 30%),
        #050607;
    color: #d5d5d5;
    font-family: "Consolas", "Courier New", monospace;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    padding-top: 1.2rem;
    max-width: 1600px;
}

h1, h2, h3 {
    font-family: "Consolas", monospace !important;
    letter-spacing: 1px;
}

.quantum-title {
    font-size: 2.0rem;
    font-weight: 800;
    letter-spacing: 4px;
    color: #ffffff;
}

.quantum-subtitle {
    color: #777;
    letter-spacing: 2px;
    font-size: .72rem;
}

.live {
    color: #00ff88;
    font-weight: bold;
}

.panel {
    background: linear-gradient(145deg, #0b0d10, #08090b);
    border: 1px solid #1d2026;
    border-radius: 8px;
    padding: 18px;
    margin-bottom: 14px;
    box-shadow: 0 0 20px rgba(0,0,0,.25);
}

.panel-purple {
    border: 1px solid #5f2b9e;
    box-shadow: 0 0 25px rgba(120,40,255,.10);
}

.metric-label {
    color: #707070;
    font-size: .68rem;
    letter-spacing: 1.5px;
}

.metric-value {
    color: #fff;
    font-size: 1.35rem;
    font-weight: bold;
    margin-top: 4px;
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

.score-big {
    font-size: 3.5rem;
    font-weight: 900;
    line-height: 1;
}

.progress-bg {
    background: #15171b;
    height: 9px;
    border-radius: 10px;
    overflow: hidden;
    margin-top: 8px;
}

.progress-green {
    height: 100%;
    background: #00ff88;
}

.progress-red {
    height: 100%;
    background: #ff405c;
}

.factor {
    border-bottom: 1px solid #191b20;
    padding: 9px 0;
    font-size: .82rem;
}

.factor:last-child {
    border-bottom: none;
}

.tag {
    display: inline-block;
    border: 1px solid #272b32;
    background: #0c0e11;
    padding: 4px 8px;
    border-radius: 4px;
    margin-right: 5px;
    font-size: .65rem;
    color: #888;
}

.alert-box {
    border-left: 3px solid #a96cff;
    background: #0d0a13;
    padding: 12px;
    border-radius: 4px;
    margin: 8px 0;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# API HELPERS
# ============================================================

@st.cache_data(ttl=30)
def get_sol_price():
    url = f"{COINGECKO}/simple/price"
    params = {
        "ids": "solana,bitcoin",
        "vs_currencies": "usd",
        "include_24hr_change": "true",
        "include_24hr_vol": "true",
        "include_market_cap": "true"
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


@st.cache_data(ttl=60)
def get_fear_greed():
    try:
        r = requests.get(FEAR_GREED, params={"limit": 1}, timeout=10)
        r.raise_for_status()
        data = r.json()["data"][0]

        return {
            "value": int(data["value"]),
            "classification": data["value_classification"]
        }
    except Exception:
        return {
            "value": None,
            "classification": "N/A"
        }


@st.cache_data(ttl=60)
def get_klines(interval="1h", limit=200):
    try:
        params = {
            "symbol": "SOLUSDT",
            "interval": interval,
            "limit": limit
        }

        r = requests.get(
            f"{BINANCE}/klines",
            params=params,
            timeout=10
        )

        r.raise_for_status()

        raw = r.json()

        df = pd.DataFrame(raw, columns=[
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
        ])

        for c in ["open", "high", "low", "close", "volume"]:
            df[c] = pd.to_numeric(df[c])

        df["time"] = pd.to_datetime(df["time"], unit="ms")

        return df

    except Exception:
        return pd.DataFrame()


# ============================================================
# TECHNICAL INDICATORS
# ============================================================

def calculate_rsi(series, period=14):

    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    return 100 - (100 / (1 + rs))


def calculate_indicators(df):

    if df.empty:
        return df

    df = df.copy()

    df["EMA20"] = df["close"].ewm(span=20).mean()
    df["EMA50"] = df["close"].ewm(span=50).mean()
    df["EMA200"] = df["close"].ewm(span=200).mean()

    df["RSI"] = calculate_rsi(df["close"])

    df["VOL_MA20"] = df["volume"].rolling(20).mean()

    return df


# ============================================================
# SCORING ENGINE
# ============================================================

def technical_score(df):

    if df.empty or len(df) < 50:
        return 0, []

    last = df.iloc[-1]

    score = 0
    factors = []

    # EMA trend
    if last["close"] > last["EMA20"]:
        score += 12
        factors.append(("🟢", "Precio sobre EMA20", "+12"))
    else:
        score -= 12
        factors.append(("🔴", "Precio bajo EMA20", "-12"))

    if last["EMA20"] > last["EMA50"]:
        score += 10
        factors.append(("🟢", "EMA20 > EMA50", "+10"))
    else:
        score -= 10
        factors.append(("🔴", "EMA20 < EMA50", "-10"))

    # RSI
    rsi = float(last["RSI"])

    if 50 <= rsi <= 68:
        score += 10
        factors.append(("🟢", f"RSI saludable ({rsi:.1f})", "+10"))
    elif rsi > 75:
        score -= 8
        factors.append(("🔴", f"RSI sobrecomprado ({rsi:.1f})", "-8"))
    elif rsi < 30:
        score += 5
        factors.append(("🟡", f"RSI sobrevendido ({rsi:.1f})", "+5"))
    else:
        factors.append(("⚪", f"RSI neutral ({rsi:.1f})", "0"))

    # Volume
    if last["volume"] > last["VOL_MA20"]:
        score += 8
        factors.append(("🟢", "Volumen sobre media", "+8"))
    else:
        score -= 3
        factors.append(("🔴", "Volumen bajo media", "-3"))

    return max(-50, min(50, score)), factors


def market_score(market):

    score = 0
    factors = []

    if not market:
        return 0, factors

    sol = market.get("solana", {})
    btc = market.get("bitcoin", {})

    sol_change = sol.get("usd_24h_change", 0) or 0
    btc_change = btc.get("usd_24h_change", 0) or 0

    # SOL momentum
    if sol_change > 2:
        score += 10
        factors.append(("🟢", f"SOL momentum +{sol_change:.2f}%", "+10"))
    elif sol_change < -2:
        score -= 10
        factors.append(("🔴", f"SOL momentum {sol_change:.2f}%", "-10"))
    else:
        factors.append(("⚪", f"SOL 24h {sol_change:.2f}%", "0"))

    # BTC influence
    if btc_change > 1:
        score += 8
        factors.append(("🟢", f"BTC fuerte +{btc_change:.2f}%", "+8"))
    elif btc_change < -1:
        score -= 8
        factors.append(("🔴", f"BTC débil {btc_change:.2f}%", "-8"))
    else:
        factors.append(("⚪", f"BTC neutral {btc_change:.2f}%", "0"))

    return max(-50, min(50, score)), factors


def sentiment_score(fng):

    if fng["value"] is None:
        return 0, []

    value = fng["value"]

    if value >= 75:
        return 8, [("🟢", f"Fear & Greed: {value}", "+8")]

    if value >= 55:
        return 5, [("🟢", f"Fear & Greed: {value}", "+5")]

    if value <= 25:
        return -8, [("🔴", f"Fear & Greed: {value}", "-8")]

    if value <= 45:
        return -4, [("🟡", f"Fear & Greed: {value}", "-4")]

    return 0, [("⚪", f"Fear & Greed: {value}", "0")]


# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(message):

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return False, "Telegram no configurado"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        response = requests.post(
            url,
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            },
            timeout=10
        )

        if response.ok:
            return True, "Telegram OK"

        return False, response.text

    except Exception as e:
        return False, str(e)


def telegram_test():

    message = """🟣 QUANTUM SOLANA TEST

Telegram connection: ONLINE

Bot:
@Mycrypto_best_bot

SOL Intelligence Terminal
Status: READY

This is only a connection test."""

    return send_telegram(message)


# ============================================================
# HEADER
# ============================================================

market = get_sol_price()
fear_greed = get_fear_greed()

sol = market.get("solana", {})
btc = market.get("bitcoin", {})

sol_price = sol.get("usd", 0)
sol_change = sol.get("usd_24h_change", 0)
sol_volume = sol.get("usd_24h_vol", 0)

btc_price = btc.get("usd", 0)
btc_change = btc.get("usd_24h_change", 0)


st.markdown("""
<div class="quantum-title">
QUANTUM // SOLANA INTELLIGENCE
</div>

<div class="quantum-subtitle">
MULTI-VECTOR MARKET ANALYSIS // SOL ONLY
&nbsp;&nbsp; <span class="live">● SYSTEM ONLINE</span>
</div>
""", unsafe_allow_html=True)

st.write("")


# ============================================================
# TOP METRICS
# ============================================================

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(
        f"""
        <div class="panel">
        <div class="metric-label">SOL / USD</div>
        <div class="metric-value">${sol_price:,.2f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c2:
    cls = "green" if sol_change >= 0 else "red"

    st.markdown(
        f"""
        <div class="panel">
        <div class="metric-label">SOL 24H</div>
        <div class="metric-value {cls}">{sol_change:+.2f}%</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c3:
    st.markdown(
        f"""
        <div class="panel">
        <div class="metric-label">SOL VOLUME</div>
        <div class="metric-value">${sol_volume/1e9:.2f}B</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c4:
    cls = "green" if btc_change >= 0 else "red"

    st.markdown(
        f"""
        <div class="panel">
        <div class="metric-label">BTC 24H</div>
        <div class="metric-value {cls}">{btc_change:+.2f}%</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c5:
    fg_value = fear_greed["value"]
    fg_text = fear_greed["classification"]

    st.markdown(
        f"""
        <div class="panel">
        <div class="metric-label">FEAR / GREED</div>
        <div class="metric-value purple">
        {fg_value if fg_value is not None else "N/A"}
        </div>
        <div class="metric-label">{fg_text}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# DATA
# ============================================================

df = get_klines("1h", 200)
df = calculate_indicators(df)

tech_score, tech_factors = technical_score(df)
market_score_value, market_factors = market_score(market)
sent_score, sentiment_factors = sentiment_score(fear_greed)

# Weighted global score
# Technical 45%
# Market 30%
# Sentiment 15%
# Reserve 10% for future derivatives/on-chain/news modules

global_score = (
    tech_score * 0.45 +
    market_score_value * 0.30 +
    sent_score * 0.15
)

global_score = max(-100, min(100, global_score))

# Convert score into directional chances
bullish = int(round(50 + global_score / 2))
bullish = max(5, min(95, bullish))
bearish = 100 - bullish

# Confidence based on data availability
confidence = 60

if not df.empty:
    confidence += 10

if market:
    confidence += 10

if fear_greed["value"] is not None:
    confidence += 5

if not df.empty and len(df) >= 150:
    confidence += 5

confidence = min(95, confidence)


if bullish >= 70:
    vector = "STRONG BULLISH"
    vector_class = "green"
elif bullish >= 58:
    vector = "BULLISH"
    vector_class = "green"
elif bullish <= 30:
    vector = "STRONG BEARISH"
    vector_class = "red"
elif bullish <= 42:
    vector = "BEARISH"
    vector_class = "red"
else:
    vector = "NEUTRAL"
    vector_class = "yellow"


# ============================================================
# MAIN VECTOR
# ============================================================

left, right = st.columns([1.7, 1])

with left:

    st.markdown(
        """
        <div class="panel panel-purple">
        <div class="metric-label">QUANTUM MARKET VECTOR</div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div style="display:flex;justify-content:space-between;align-items:end;">
            <div>
                <div class="score-big {vector_class}">
                    {bullish}%
                </div>
                <div class="metric-label">CHANCE OF UPSIDE</div>
            </div>

            <div style="text-align:right;">
                <div class="score-big red">{bearish}%</div>
                <div class="metric-label">CHANCE OF DOWNSIDE</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="progress-bg">
            <div class="progress-green" style="width:{bullish}%"></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <br>
        <span class="tag">VECTOR: {vector}</span>
        <span class="tag">CONFIDENCE: {confidence}%</span>
        <span class="tag">SCORE: {global_score:+.1f}</span>
        """,
        unsafe_allow_html=True
    )

    st.markdown("</div>", unsafe_allow_html=True)


with right:

    st.markdown(
        f"""
        <div class="panel">
        <div class="metric-label">MODEL STATUS</div>
        <br>

        <div class="factor">
        Technical
        <span style="float:right" class="cyan">{tech_score:+d}</span>
        </div>

        <div class="factor">
        Market / BTC
        <span style="float:right" class="cyan">{market_score_value:+d}</span>
        </div>

        <div class="factor">
        Sentiment
        <span style="float:right" class="cyan">{sent_score:+d}</span>
        </div>

        <div class="factor">
        Confidence
        <span style="float:right" class="green">{confidence}%</span>
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# CHART
# ============================================================

st.markdown("### 📈 SOL MARKET STRUCTURE")

if not df.empty:

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df["time"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="SOL"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["EMA20"],
            name="EMA 20",
            line=dict(width=1)
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["EMA50"],
            name="EMA 50",
            line=dict(width=1)
        )
    )

    fig.update_layout(
        height=560,
        template="plotly_dark",
        paper_bgcolor="#050607",
        plot_bgcolor="#050607",
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis_rangeslider_visible=False,
        legend=dict(
            orientation="h",
            y=1.02
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displaylogo": False,
            "scrollZoom": True
        }
    )


# ============================================================
# FACTORS
# ============================================================

st.markdown("### 🧠 VECTOR COMPONENTS")

all_factors = (
    tech_factors +
    market_factors +
    sentiment_factors
)

col1, col2 = st.columns(2)

with col1:

    st.markdown(
        '<div class="panel"><div class="metric-label">ACTIVE SIGNALS</div>',
        unsafe_allow_html=True
    )

    for icon, text_factor, value in all_factors:

        cls = "green" if value.startswith("+") else (
            "red" if value.startswith("-") else "yellow"
        )

        st.markdown(
            f"""
            <div class="factor">
            {icon} {text_factor}
            <span style="float:right" class="{cls}">
            {value}
            </span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)


with col2:

    st.markdown(
        """
        <div class="panel">
        <div class="metric-label">QUANTUM INTERPRETATION</div>
        <br>
        """,
        unsafe_allow_html=True
    )

    if bullish >= 70:

        interpretation = """
        <div class="alert-box">
        <span class="green"><b>🟢 STRONG BULLISH BIAS</b></span><br><br>
        Multiple market vectors currently support upside.
        The model detects more bullish than bearish pressure.
        </div>
        """

    elif bullish >= 58:

        interpretation = """
        <div class="alert-box">
        <span class="green"><b>🟢 BULLISH BIAS</b></span><br><br>
        The current data favors upside, although confirmation
        from additional vectors is recommended.
        </div>
        """

    elif bullish <= 30:

        interpretation = """
        <div class="alert-box">
        <span class="red"><b>🔴 STRONG BEARISH BIAS</b></span><br><br>
        Several available vectors currently favor downside risk.
        </div>
        """

    elif bullish <= 42:

        interpretation = """
        <div class="alert-box">
        <span class="red"><b>🔴 BEARISH BIAS</b></span><br><br>
        Current market structure favors downside.
        </div>
        """

    else:

        interpretation = """
        <div class="alert-box">
        <span class="yellow"><b>🟡 NEUTRAL MARKET</b></span><br><br>
        The available signals do not provide sufficient
        directional advantage.
        </div>
        """

    st.markdown(interpretation, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="metric-label">
        IMPORTANT: the percentage is a quantitative market
        score, not a guaranteed probab
