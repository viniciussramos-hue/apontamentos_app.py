import streamlit as st
import pandas as pd
import sqlite3
from datetime import time
import google.generativeai as genai

# ==================================
# CONFIGURAÇÃO DA PÁGINA
# ==================================

st.set_page_config(
    page_title="Calculadora de Eficiência",
    page_icon="📊",
    layout="wide"
)

# ==================================
# CONFIGURAÇÃO GEMINI
# ==================================

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")
    ia_disponivel = True
except Exception as e:
    ia_disponivel = False
    st.warning(
        "Gemini não configurado. Verifique o GEMINI_API_KEY nos Secrets."
    )

# ==================================
# BANCO DE DADOS
# ==================================

@st.cache_resource
def conectar_banco():
    conn = sqlite3.connect(
        "apontamentos.db",
        check_same_thread=False
    )

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS apontamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            hora_inicio TEXT,
            hora_fim TEXT,
            duracao_esperada REAL,
            duracao_real REAL,
            eficiencia REAL,
            data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    return conn

conn = conectar_banco()
cursor = conn.cursor()

# ==================================
# TÍTULO
# ==================================

st.title("📊 Calculadora de Eficiência com IA")

# ==================================
# FOTO DO APONTAMENTO
# ==================================

st.subheader("📷 Leitura do Apontamento por Foto")

foto = st.camera_input(
    "Tire uma foto do apontamento"
)

if foto is not None:

    st.image(foto, width=400)

    if ia_disponivel:

        with st.spinner("Analisando imagem..."):

            try:

                imagem_bytes = foto.getvalue()

                prompt = """
Analise a foto enviada.

Extraia as seguintes informações:

- Código do apontamento
- Hora de início
- Hora de término
- Informe se o código é 0 (produção)

Retorne exatamente neste formato:

Código:
Hora Início:
Hora Fim:
Código Zero:
"""

                resposta = model.generate_content(
                    [
                        prompt,
                        {
                            "mime_type": foto.type,
                            "data": imagem_bytes
                        }
                    ]
                )

                st.success("Análise concluída")

                st.text_area(
                    "Resultado da IA",
                    value=resposta.text,
                    height=200
                )

            except Exception as erro:
                st.error(f"Erro ao processar imagem: {erro}")

# ==================================
# FORMULÁRIO
# ==================================

st.subheader("📝 Registro Manual")

with st.form(
    "form_apontamento",
    clear_on_submit=True
):

    codigo = st.text_input(
        "Código do Apontamento"
    )

    col1, col2 = st.columns(2)

    with col1:
        hora_inicio = st.time_input(
            "Hora de Início",
            value=time(8, 0)
        )

    with col2:
        hora_fim = st.time_input(
            "Hora de Término",
            value=time(9, 0)
        )

    duracao_esperada = st.number_input(
        "Duração Esperada (minutos)",
        min_value=1.0,
        value=60.0,
        step=5.0
    )

    salvar = st.form_submit_button(
        "Calcular e Registrar"
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

        # Caso atravesse a meia-noite
        if fim_min <= inicio_min:
            fim_min += 1440

        duracao_real = fim_min - inicio_min

        eficiencia = (
            duracao_esperada / duracao_real
        ) * 100

        try:

            cursor.execute("""
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
                codigo,
                str(hora_inicio),
                str(hora_fim),
                duracao_esperada,
                duracao_real,
                eficiencia
            )
            )

            conn.commit()

            st.success(
                f"Eficiência calculada: {eficiencia:.2f}%"
            )

        except Exception as erro:
            st.error(
                f"Erro ao gravar dados: {erro}"
            )

# ==================================
# HISTÓRICO
# ==================================

st.subheader("📋 Histórico")

try:

    df = pd.read_sql_query("""
        SELECT *
        FROM apontamentos
        ORDER BY id DESC
    """, conn)

    if not df.empty:

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Registros",
                len(df)
            )

        with col2:
            st.metric(
                "Eficiência Média",
                f"{df['eficiencia'].mean():.2f}%"
            )

        with col3:
            st.metric(
                "Maior Eficiência",
                f"{df['eficiencia'].max():.2f}%"
            )

    st.dataframe(
        df,
        use_container_width=True
    )

except Exception as erro:
    st.error(
        f"Erro ao carregar histórico: {erro}"
    )
