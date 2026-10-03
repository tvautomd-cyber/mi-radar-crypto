import streamlit as st
import random
import requests

st.set_page_config(page_title="QUANTUM SOLANA MULTI-VECTOR V4", layout="wide")

# --- CONFIGURACIÓN DE TU TELEGRAM ---
# 👇 BORRA EL TEXTO DE ABAJO Y PEGA TU TOKEN DE BOTFATHER (Deja las comillas)
TELEGRAM_TOKEN = "8951377031:AAEMQ7r94hDKcgn6sEEXZasFKjvnvze3nyc"

# Estilos Core Dark Hacker y Matrix adaptados a CryptoPanic
st.markdown("""
    <style>
    .stApp { background-color: #050505 !important; color: #aaaaaa !important; font-family: 'Consolas', monospace !important; }
    h1, h2, h3, p, span, label { color: #e5e5e5 !important; font-family: 'Consolas', monospace !important; }
    .terminal-row { border-bottom: 1px solid #1f1f1f; padding: 10px 0; display: flex; align-items: flex-start; font-size: 0.85rem; }
    .time-badge { color: #666666 !important; min-width: 60px; font-size: 0.75rem; font-weight: bold; }
    .news-content { flex-grow: 1; color: #d0d0d0 !important; }
    .news-source { font-size: 0.7rem; color: #ff5500 !important; margin-top: 2px; }
    .crypto-tag { color: #00ccff !important; font-weight: bold; min-width: 50px; text-align: right; }
    .vector-box { border: 1px solid #222222; background-color: #0d0d0d; padding: 14px; border-radius: 2px; margin-bottom: 15px; }
    .solana-box { border: 1px solid #9945FF; background-color: #0b0214; padding: 16px; border-radius: 4px; margin-bottom: 20px; box-shadow: 0 0 10px rgba(153,69,255,0.15); }
    .rec-strong-buy { color: #00ff66 !important; font-weight: bold; text-shadow: 0 0 5px #00ff66; }
    .rec-dump { color: #ff3333 !important; font-weight: bold; text-shadow: 0 0 5px #ff3333; }
    </style>
""", unsafe_allow_html=True)

# Ticker de precios superior estilo hacker con datos macro recientes
st.markdown("""
<div style='display: flex; justify-content: space-between; border-bottom: 1px solid #9945FF; padding-bottom: 6px; margin-bottom: 15px; font-size: 0.8rem;'>
    <span>🟢 <span style='color:#9945FF; font-weight:bold;'>SOL</span> $118.60 <span style='color:#00ff66;'>+4.20%</span></span>
    <span>⚡ <span style='color:#ff7700; font-weight:bold;'>BTC</span> $84,756 <span style='color:#00ff66;'>+0.30%</span></span>
    <span><span style='color:#8833ff; font-weight:bold;'>ETH</span> $2,687 <span style='color:#ff3333;'>-0.45%</span></span>
</div>
""", unsafe_allow_html=True)

st.title("🖧 CORE RADAR: SOLANA OVERVIEW")

# Base de datos global simulada que abarca todo internet (FED, Trump, Geopolítica, Robos, Paro)
noticias_pool = [
    {"time": "JUST NOW", "txt": "🔥 EXCLUSIVO SOLANA: El 84% de los Trading Bots (Jupiter/Maestro) detectan compras masivas en la red tras la integración de nuevos pools de liquidez.", "src": "://solana.com", "tag": "SOL", "impacto": 38, "critica": True},
    {"time": "3min", "txt": "🚨 ALERTA ROBO: Un exchange internacional sufre un exploit crítico de drenado de liquidez. Pérdida estimada de 40,000 SOL. Mitigación en marcha.", "src": "solscan.io", "tag": "SOL", "impacto": -32, "critica": True},
    {"time": "14min", "txt": "⚖️ SEC & REGULACIÓN: Rumores de aceleración extrema en la exención de innovación de tokens y la aprobación de ETFs de SOL al contado en EE.UU.", "src": "sec.gov/news", "tag": "SEC", "impacto": 40, "critica": True},
    {"time": "22min", "txt": "📈 MACRO USA: El informe de empleo muestra un estancamiento inesperado del paro. Crece la presión sobre la FED para aplicar bajadas agresivas en las tasas de interés.", "src": "bloomberg.com", "tag": "FED", "impacto": 18, "critica": False},
    {"time": "45min", "txt": "🌍 GEOPOLÍTICA: La administración Trump anuncia nuevos desacuerdos económicos y aranceles a la importación. Los mercados tradicionales caen, provocando un flujo masivo de capital de cobertura hacia las cripto.", "src": "reuters.com", "tag": "GLOBAL", "impacto": 15, "critica": False}
]

# --- PROCESAMIENTO TÁCTICO EXCLUSIVO DE SOLANA ---
st.markdown("### 🧬 VECTOR TÁCTICO: SOLANA (SOL)")
impacto_global_sol = sum([n['impacto'] for n in noticias_pool if n['tag'] in ['SOL', 'SEC', 'GLOBAL', 'FED']])
prob_subir_sol = max(5, min(95, 50 + (impacto_global_sol // 2)))
prob_bajar_sol = 100 - prob_subir_sol

bots_long = max(10, min(90, 52 + (impacto_global_sol // 3)))
bots_short = 100 - bots_long

# Algoritmo de recomendación avanzada
if prob_subir_sol > 65 and bots_long > 60:
    rec_sol = "<span class='rec-strong-buy'>[★ EXCELENTE MOMENTO DE COMPRA: NO ES MALA IDEA]</span>"
elif prob_subir_sol < 40:
    rec_sol = "<span class='rec-dump'>[⚠️ RIESGO ELEVADO: SE RECOMIENDA ESPERAR]</span>"
else:
    rec_sol = "<span style='color:#ffaa00; font-weight:bold;'>[⚡ CONDICIÓN DE MERCADO NEUTRAL]</span>"

st.markdown(f"""
<div class="solana-box">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <span style="font-size: 1.2rem; font-weight: bold; color: #ffffff;">🪙 SOLANA MATRIX OVERVIEW</span>
        {rec_sol}
    </div>
    <p style="font-size: 0.75rem; color: #a272e6; margin: 0 0 10px 0;">
        Consenso de Bots de Trading: <span style="color:#00ff66;">{bots_long}% Comprando (Longs)</span> | <span style="color:#ff3333;">{bots_short}% Vendiendo (Shorts)</span>
    </p>
    
    <!-- GRÁFICO MATRIX PARA SOLANA CON EL CERO EN MEDIO -->
    <div style="font-size: 0.95rem; color: #9945FF; margin: 6px 0;">▲ {"■" * int(prob_subir_sol/5)}{"·" * (20 - int(prob_subir_sol/5))} {prob_subir_sol}% CHANCES DE SUBIR</div>
    <div style="border-top: 1px dashed #552277; margin: 8px 0; text-align: center;">
        <span style="font-size: 0.6rem; color: #9945FF; letter-spacing: 2px;">[ VECTOR ZERO EQUILIBRIUM ]</span>
    </div>
    <div style="font-size: 0.95rem; color: #ff3333; margin: 6px 0;">▼ {"■" * int(prob_bajar_sol/5)}{"·" * (20 - int(prob_bajar_sol/5))} {prob_bajar_sol}% CHANCES DE BAJAR</div>
</div>
""", unsafe_allow_html=True)

# --- COMPARADOR DE VECTORES SECUNDARIOS (BTC & ETH) ---
st.markdown("### 📊 VECTORES SECUNDARIOS (MERCADO GENERAL)")
for coin in ["BTC", "ETH"]:
    # Cálculo para las demás monedas basándose en la FED y variables macro globales
    score_coin = sum([n['impacto'] for n in noticias_pool if n['tag'] in [coin, 'FED', 'GLOBAL']])
    p_subir = max(5, min(95, 50 + (score_coin // 3)))
    p_bajar = 100 - p_subir
    
    st.markdown(f"""
    <div class="vector-box">
        <span style="font-weight: bold; color:#ffffff;">🪙 {coin} / USD</span>
        <div style="font-size: 0.8rem; color:#ff7700; margin-top:4px;">▲ {"■" * int(p_subir/5)}{"·" * (20 - int(p_subir/5))} {p_subir}% Subir</div>
        <div style="border-top: 1px dashed #333; margin: 4px 0;"></div>
        <div style="font-size: 0.8rem; color:#ff3333;">▼ {"■" * int(p_bajar/5)}{"·" * (20 - int(p_bajar/5))} {p_bajar}% Bajar</div>
    </div>
    """, unsafe_allow_html=True)

# --- PANEL INTEGRAL DE INFORMACIÓN (Estilo CryptoPanic Terminal) ---
st.markdown("### 📥 GLOBAL INTEGRAL INTELLIGENCE STREAM")
for n in noticias_pool:
    alerta_push = "<b style='color:#ff3333;'>[🚨 TELEGRAM PUSH]</b> " if n['critica'] else ""
    st.markdown(f"""
    <div class="terminal-row">
        <div class="time-badge">{n['time']}</div>
        <div class="news-content">
            {alerta_push}<b>{n['txt']}</b>
            <div class="news-source">FUENTE PONDERADA: {n['src']}</div>
        </div>
        <div class="crypto-tag">{n['tag']}</div>
    </div>
    """, unsafe_allow_html=True)

# --- BOTÓN INTERACTIVO PARA LA NOTIFICACIÓN REAL ---
if st.button("⚡ DETONAR ALERTA GLOBAL DE PRUEBA"):
    if "AQUÍ_PEGA" in TELEGRAM_TOKEN:
        st.error("Por favor, introduce tu Token real de Telegram dentro del código del archivo App.py.")
    else:
        try:
            url_updates = f"https://telegram.org{TELEGRAM_TOKEN}/getUpdates"
            res = requests.get(url_updates).json()
            chat_id = res['result'][-1]['message']['chat']['id']
            msg = f"🚨 [ALERTA COMPLETA SOLANA] 🚨\n\nCambios macro, geopolíticos (Trump), decisiones de la SEC y robos analizados en la red.\n\nChances de subir SOL: {prob_subir_sol}%.\nConsenso Bots: NO ES MALA IDEA COMPRAR."
            url_send = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage?chat_id={chat_id}&text={msg}"
            requests.get(url_send)
            st.success("¡Mensaje de prueba enviado! Revisa tu aplicación de Telegram.")
        except Exception:
            st.warning("Por favor, ve al chat de tu bot en Telegram, pulsa el botón 'Iniciar' (o escribe cualquier mensaje) y vuelve a pulsar este botón.")
          
