import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import xml.etree.ElementTree as ET
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
# SECRETS
# ============================================================

TELEGRAM_TOKEN = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")
TELEGRAM_USERNAME = st.secrets.get(
    "TELEGRAM_BOT_USERNAME",
    "Mycrypto_best_bot"
)


# ============================================================
# API
# ============================================================

COINGECKO_URL = "https://api.coingecko.com/api/v3"
BINANCE_URL = "https://api.binance.com/api/v3"
FEAR_GREED_URL = "https://api.alternative.me/fng/"


# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background:
        radial-gradient(
            circle at 85% 5%,
            rgba(120, 40, 255, 0.12),
            transparent 32%
        ),
        radial-gradient(
            circle at 10% 90%,
            rgba(0, 255, 160, 0.05),
            transparent 30%
        ),
        #050607;
    color: #d6d6d6;
    font-family: Consolas, "Courier New", monospace;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 1650px;
    padding-top: 1.2rem;
}

h1, h2, h3 {
    font-family: Consolas, "Courier New", monospace !important;
}

.quantum-title {
    font-size: 2.15rem;
    font-weight: 900;
    letter-spacing: 4px;
    color: #ffffff;
}

.quantum-subtitle {
    margin-top: 4px;
    color: #686868;
    letter-spacing: 2px;
    font-size: 0.70rem;
}

.live {
    color: #00ff88;
    font-weight: bold;
}

.panel {
    background: linear-gradient(
        145deg,
        #0b0d10,
        #08090b
    );
    border: 1px solid #1d2026;
    border-radius: 8px;
    padding: 17px;
    margin-bottom: 14px;
    box-shadow: 0 0 25px rgba(0, 0, 0, 0.28);
}

.panel-purple {
    border: 1px solid #5c2695;
    box-shadow: 0 0 25px rgba(130, 50, 255, 0.10);
}

.metric-label {
    color: #666b72;
    font-size: 0.66rem;
    letter-spacing: 1.6px;
}

.metric-value {
    color: #ffffff;
    font-size: 1.35rem;
    font-weight: bold;
    margin-top: 5px;
}

.score-big {
    font-size: 3.7rem;
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

.gray {
    color: #777777 !important;
}

.progress-background {
    width: 100%;
    height: 10px;
    background: #16191e;
    border-radius: 10px;
    overflow: hidden;
    margin-top: 12px;
}

.progress-up {
    height: 100%;
    background: #00ff88;
}

.factor {
    border-bottom: 1px solid #191c21;
    padding: 9px 0;
    font-size: 0.80rem;
}

.factor:last-child {
    border-bottom: none;
}

.tag {
    display: inline-block;
    border: 1px solid #292d34;
    background: #0c0e11;
    padding: 4px 8px;
    border-radius: 4px;
    margin-right: 5px;
    margin-top: 5px;
    font-size: 0.63rem;
    color: #888888;
}

.news-card {
    background: #090b0e;
    border-left: 3px solid #5d2b91;
    padding: 11px;
    margin-bottom: 8px;
    border-radius: 3px;
}

.news-title {
    color: #dddddd;
    font-size: 0.80rem;
    line-height: 1.45;
}

.news-meta {
    color: #666666;
    font-size: 0.62rem;
    margin-top: 5px;
}

.alert-box {
    border-left: 3px solid #a96cff;
    background: #0d0a13;
    padding: 13px;
    border-radius: 4px;
}

.warning-box {
    border-left: 3px solid #ffc857;
    background: #131006;
    padding: 13px;
    border-radius: 4px;
}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# GENERIC REQUEST
# ============================================================

def safe_get(url, params=None, timeout=12):

    try:
        response = requests.get(
            url,
            params=params,
            timeout=timeout,
            headers={
                "User-Agent": "Quantum-Solana-Terminal/1.0"
            }
        )

        response.raise_for_status()
        return response

    except Exception:
        return None


# ============================================================
# MARKET DATA
# ============================================================

@st.cache_data(ttl=30)
def get_market_data():

    response = safe_get(
        f"{COINGECKO_URL}/simple/price",
        params={
            "ids": "solana,bitcoin,ethereum",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_market_cap": "true"
        }
    )

    if response is None:
        return {}

    try:
        return response.json()
    except Exception:
        return {}


# ============================================================
# CANDLES
# ============================================================

@st.cache_data(ttl=60)
def get_candles(interval="1h", limit=250):

    response = safe_get(
        f"{BINANCE_URL}/klines",
        params={
            "symbol": "SOLUSDT",
            "interval": interval,
            "limit": limit
        }
    )

    if response is None:
        return pd.DataFrame()

    try:

        raw = response.json()

        df = pd.DataFrame(
            raw,
            columns=[
                "timestamp",
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
        )

        numeric_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]

        for column in numeric_columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
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

    response = safe_get(
        FEAR_GREED_URL,
        params={"limit": 1}
    )

    if response is None:
        return {
            "value": None,
            "classification": "N/A"
        }

    try:

        data = response.json()["data"][0]

        return {
            "value": int(data["value"]),
            "classification": data["value_classification"]
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
        "Solana OR SOL crypto OR Bitcoin crypto OR "
        "Ethereum crypto OR crypto ETF OR SEC crypto OR "
        "Federal Reserve OR Fed OR inflation OR tariffs OR "
        "Trump crypto OR cryptocurrency regulation"
    )

    url = (
        "https://news.google.com/rss/search?"
        "q=" + quote(query) +
        "&hl=en-US&gl=US&ceid=US:en"
    )

    response = safe_get(url)

    if response is None:
        return []

    try:

        root = ET.fromstring(response.text)

        articles = []

        for item in root.findall(".//item")[:20]:

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
