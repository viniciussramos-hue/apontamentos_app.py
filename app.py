import streamlit as st
import pandas as pd
import sqlite3
from datetime import time
import google.generativeai as genai

# =========================
# CONFIGURAÇÃO GEMINI
# =========================

genai.configure(
    api_key=st.secrets["GEMINI_API_KEY"]
)

model = genai.GenerativeModel("gemini-1.5-flash")

# =========================
# BANCO DE DADOS
# =========================

@st.cache_resource
def get_connection():
    return sqlite3.connect(
        "apontamentos.db",
        check_same_thread=False
    )

conn = get_connection()
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS apontamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT,
    hora_inicio TEXT,
    hora_fim TEXT,
    duracao_esperada REAL,
    eficiencia REAL
)
""")

conn.commit()

# =========================
# INTERFACE
# =========================

st.set_page_config(
    page_title="Calculadora de Eficiência",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Calculadora de Eficiência com IA")

st.markdown("---")

# =========================
# FOTO DO APONTAMENTO
# =========================

st.subheader("📷 Captura do Apontamento")

foto = st.camera_input("Tire uma foto do apontamento")

if foto is not None:

    with st.spinner("Analisando imagem..."):

        try:

            image_bytes = foto.getvalue()

            prompt = """
            Analise 
