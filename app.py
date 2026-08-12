import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
from PIL import Image
import json

# ==================================
# CONFIGURAÇÃO DA IA (GEMINI)
# ==================================
# Insira sua chave da API abaixo entre as aspas
API_KEY = "SUA_CHAVE_API_AQUI" 

try:
    if API_KEY != "SUA_CHAVE_API_AQUI":
        genai.configure(api_key=API_KEY)
    else:
        genai.configure(api_key=st.secrets.get("GEMINI_API_KEY", ""))
    
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    model = None

# ==================================
# BANCO DE DADOS
# ==================================

@st.cache_resource
def conectar_banco():
    conn = sqlite3.connect(
        "apontamentos.db",
        check_same_thread=False
    )

    conn.execute("""
    CREATE TABLE IF NOT EXISTS apontamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT,
        hora_inicio TEXT,
        hora_fim TEXT,
        duracao_esperada REAL,
        duracao_real REAL,
        eficiencia REAL
    )
    """)

    conn.commit()
    return conn

conn = conectar_banco()

# ==================================
# PÁGINA
# ==================================

st.set_page_config(
    page_title="Leitor de Apontamento por IA",
    page_icon="📷",
    layout="wide"
)

st.title("📷 Leitor Automático de Apontamento & Eficiência")
st.write("Tire uma foto ou faça o upload da imagem da folha de apontamento. A IA fará a leitura, identificará o código (0 para produção) e calculará a eficiência automaticamente.")

# ==================================
# ESCOLHA: CÂMERA OU UPLOAD DE ARQUIVO
# ==================================

modo_entrada = st.radio("Escolha o método para enviar a imagem:", ["📸 Tirar Foto (Câmera)", "📁 Enviar Arquivo de Imagem"])

imagem_pil = None

if modo_entrada == "📸 Tirar Foto (Câmera)":
    foto = st.camera_input("Tire uma foto clara da folha de apontamento")
    if foto is not None:
        imagem_pil = Image.open(foto)
else:
    arquivo_up = st.file_uploader("Escolha a imagem do apontamento", type=["jpg", "jpeg", "png"])
    if arquivo_up is not None:
        imagem_pil = Image.open(arquivo_up)

# Se houver uma imagem (seja da câmera ou do upload)
if
