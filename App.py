import os
import time
import math
import requests
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="SOL // QUANTUM RADAR",
    page_icon="🟣",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# CONFIGURACIÓN
# ============================================================

COIN = "SOLUSDT"

BINANCE_SPOT = "https://api.binance.com"
BINANCE_FUTURES = "https://fapi.binance.com"
FEAR_GREED = "https://api.alternative.me/fng/"
CRYPTOCOMPARE = "https://min-api.cryptocompare.com/data/v2/news/"

REQUEST_TIMEOUT = 8
CACHE_SECONDS = 60

# ============================================================
# TELEGRAM
#
# NO PONGAS EL TOKEN AQUÍ.
#
# En Streamlit Cloud:
#
# Settings -> Secrets
#
# Añade:
#
# TELEGRAM_BOT_TOKEN = "TU_TOKEN_NUEVO"
# TELEGRAM_CHAT_ID = "TU_CHAT_ID"
# ============================================================

TELEGRAM_BOT_TOKEN = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")


# ============================================================
# ESTILO HACKER / TRADER
# ============================================================

CSS = (
    "<style>"
    "html,body,[class*='css']{font-family:Consolas,monospace!important;}"
    ".stApp{background:#050609;color:#d8d8df;}"
    ".block-container{padding-top:1rem;max-width:1400px;}"
    ".topbar{border:1px solid #262638;background:#090912;padding:14px 18px;"
    "border-radius:8px;margin-bottom:14px;"
    "box-shadow:0 0 25px rgba(120,60,255,.08);}"
    ".title{font-size:28px;font-weight:800;color:#b36cff;"
    "letter-spacing:2px;}"
    ".sub{color:#77778a;font-size:12px;margin-top:4px;}"
    ".card{background:#090910;border:1px solid #252536;"
    "border-radius:8px;padding:16px;margin-bottom:12px;}"
    ".label{font-size:11px;color:#77778a;text-transform:uppercase;"
    "letter-spacing:1px;}"
    ".big{font-size:30px;font-weight:800;color:#f2f2f5;}"
    ".green{color:#20e58a!important;}"
    ".red{color:#ff4f67!important;}"
    ".yellow{color:#ffd166!important;}"
    ".purple{color:#b36cff!important;}"
    ".muted{color:#77778a;font-size:12px;}"
    ".bar{height:12px;background:#171722;border-radius:8px;"
    "overflow:hidden;border:1px solid #29293a;}"
    ".barup{height:100%;background:#20e58a;}"
    ".bardown{height:100%;background:#ff4f67;}"
    ".news{border-bottom:1px solid #1b1b28;padding:10px 0;}"
    ".news-title{color:#e8e8ee;font-size:13px;}"
    ".news-meta{color:#77778a;font-size:10px;margin-top:4px;}"
    ".signal{font-size:19px;font-weight:800;letter-spacing:1px;}"
    ".small{font-size:11px;}"
    "</style>"
)

st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
# FUNCIONES GENERALES
# ============================================================

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(value, low, high):
    return max(low, min(high, value))


def get_json(url, params=None):
    try:
        response = requests.get(
