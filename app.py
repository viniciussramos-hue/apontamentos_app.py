import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
from PIL import Image
import json

# ==================================
# CONFIGURAÇÃO DA IA (GEMINI)
# ==================================
# COLE SUA CHAVE API DO GEMINI AQUI ENTRE AS ASPAS:
# Exemplo: API_KEY = "AIzaSy..."
API_KEY = "SUA_CHAVE_API_AQUI" 

try:
    if API_KEY != "SUA_CHAVE_API_AQUI":
        genai.configure(api_key=API_KEY)
    else:
        # Tenta pegar dos segredos do Streamlit se não colocar direto
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
if imagem_pil is not None:
    st.image(imagem_pil, caption="Imagem selecionada", use_container_width=True)

    if model is not None and API_KEY != "SUA_CHAVE_API_AQUI":
        if st.button("🚀 Processar e Salvar Apontamento com IA", use_container_width=True):
            with st.spinner("Analisando imagem e calculando eficiência..."):
                try:
                    prompt = (
                        "Analise esta imagem de um Relatório de Auto Apontamento. "
                        "Identifique as informações da linha principal preenchida. "
                        "Procure pela coluna 'Código' (Atv / Cód Paradas) — lembre-se que o código '0' significa produção, "
                        "extraia o Código, a 'Hora de Início' (HH:MM) e a 'Hora de Fim' (HH:MM). "
                        "Estime também ou defina uma 'duracao_esperada' padrão em minutos (ex: 60). "
                        "Retorne a resposta EXATAMENTE em formato JSON puro, contendo as chaves: "
                        "\"codigo\", \"hora_inicio\", \"hora_fim\", \"duracao_esperada\"."
                    )
                    
                    resposta = model.generate_content([prompt, imagem_pil])
                    texto_resposta = resposta.text.strip()
                    
                    if "```json" in texto_resposta:
                        texto_resposta = texto_resposta.split("```json")[1].split("```")[0].strip()
                    elif "```" in texto_resposta:
                        texto_resposta = texto_resposta.split("
