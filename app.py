import streamlit as st
import pandas as pd
import sqlite3
from datetime import time
import google.generativeai as genai
from PIL import Image
import io

# ==================================
# CONFIGURAÇÃO DA IA (GEMINI)
# ==================================
# Certifique-se de configurar sua chave de API corretamente
# (Você pode usar st.secrets["GEMINI_API_KEY"] ou inserir diretamente)
try:
    genai.configure(api_key=st.secrets.get("GEMINI_API_KEY", "SUA_CHAVE_API_AQUI"))
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
    page_title="Calculadora de Eficiência com IA",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Calculadora de Eficiência - Leitura por IA")

# Variáveis de estado para armazenar o que a IA leu (se houver)
if "ia_codigo" not in st.session_state:
    st.session_state["ia_codigo"] = ""
if "ia_inicio" not in st.session_state:
    st.session_state["ia_inicio"] = time(8, 0)
if "ia_fim" not in st.session_state:
    st.session_state["ia_fim"] = time(9, 0)

# ==================================
# FOTO E PROCESSAMENTO COM IA
# ==================================

st.subheader("📷 Capturar Foto do Apontamento")

foto = st.camera_input("Tire uma foto clara da folha de apontamento")

if foto is not None:
    imagem_pil = Image.open(foto)
    st.image(imagem_pil, caption="Foto capturada", use_container_width=True)

    if model is not None:
        if st.button("🤖 Ler Apontamento com IA"):
            with st.spinner("Analisando a folha de apontamento..."):
                try:
                    prompt = (
                        "Analise esta imagem de um Relatório de Auto Apontamento. "
                        "Identifique as informações das linhas de apontamento. "
                        "Procure pela coluna 'Código' (Atv / Cód Paradas), onde o código '0' significa produção, "
                        "e extraia o primeiro ou principal Código encontrado, a 'Hora de Início' e a 'Hora de Fim'. "
                        "Retorne a resposta EXATAMENTE no formato JSON com as chaves: "
                        "\"codigo\", \"hora_inicio\" (formato HH:MM), \"hora_fim\" (formato HH:MM)."
                    )
                    
                    resposta = model.generate_content([prompt, imagem_pil])
                    texto_resposta = resposta.text.strip()
                    
                    # Limpeza básica caso a IA retorne blocos de código markdown
                    if "```json" in texto_resposta:
                        texto_resposta = texto_resposta.split("```json")[1].split("```")[0].strip()
                    elif "```" in texto_resposta:
                        texto_resposta = texto_resposta.split("```")[1].split("```")[0].strip()

                    import json
                    dados_ia = json.loads(texto_resposta)
                    
                    st.session_state["ia_codigo"] = str(dados_ia.get("codigo", ""))
                    
                    # Converte strings de hora (HH:MM) para objetos time
                    h_ini = dados_ia.get("hora_inicio", "08:00").split(":")
                    h_fi = dados_ia.get("hora_fim", "09:00").split(":")
                    
                    st.session_state["ia_inicio"] = time(int(h_ini[0]), int(h_ini[1]))
                    st.session_state["ia_fim"] = time(int(h_fi[0]), int(h_fi[1]))
                    
                    st.success("✨ Dados extraídos com sucesso pela IA! Verifique abaixo no formulário.")
                except Exception as e:
                    st.error(f"Erro ao processar a imagem com a IA: {e}")
    else:
        st.warning("⚠️ Modelo do Gemini não configurado. Verifique sua chave de API.")

# ==================================
# FORMULÁRIO (PRÉ-PREENCHIDO PELA IA OU MANUAL)
# ==================================

st.subheader("📝 Conferência e Registro")

with st.form("registro", clear_on_submit=True):

    codigo = st.text_input("Código (0 para Produção ou Código da Parada)", value=st.session_state["ia_codigo"])

    col1, col2 = st.columns(2)

    with col1:
        hora_inicio = st.time_input(
            "Hora de Início",
            value=st.session_state["ia_inicio"]
        )

    with col2:
        hora_fim = st.time_input(
            "Hora de Fim",
            value=st.session_state["ia_fim"]
        )

    duracao_esperada = st.number_input(
        "Duração Esperada (min)",
        min_value=1.0,
        value=60.0
    )

    salvar = st.form_submit_button(
        "Calcular Eficiência"
    )

    if salvar:

        inicio_min = (
            hora_inicio.hour * 60
            + hora_inicio.minute
        )

        fim_min = (
            hora_fim.hour * 60
            + hora_fim.minute
        )

        if fim_min <= inicio_min:
            fim_min += 1440

        duracao_real = fim_min - inicio_min

        eficiencia = (
            duracao_esperada /
            duracao_real
        ) * 100

        conn.execute(
            """
            INSERT INTO apontamentos
            (
                codigo,
                hora_inicio,
                hora_fim,
                duracao_esperada,
                duracao_real,
                eficiencia
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                codigo if codigo != "" else "0", # Identifica o código 0 de produção se estiver vazio
                str(hora_inicio),
                str(hora_fim),
                duracao_esperada,
                duracao_real,
                eficiencia
            )
        )

        conn.commit()

        st.success(
            f"Apontamento salvo com sucesso! Eficiência: {eficiencia:.2f}%"
        )

# ==================================
# HISTÓRICO
# ==================================

st.subheader("📋 Histórico")

df = pd.read_sql_query(
    "SELECT * FROM apontamentos ORDER BY id DESC",
    conn
)

st.dataframe(
    df,
    use_container_width=True
)

if not df.empty:

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Total de Registros",
            len(df)
        )

    with col2:
        st.metric(
            "Eficiência Média",
            f"{df['eficiencia'].mean():.2f}%"
        )
