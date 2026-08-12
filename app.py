import streamlit as st
import pandas as pd
import sqlite3
from datetime import time

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
    page_title="Calculadora de Eficiência",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Calculadora de Eficiência")

# ==================================
# FOTO
# ==================================

st.subheader("📷 Capturar Foto")

foto = st.camera_input("Tire uma foto do apontamento")

if foto is not None:
    st.image(foto, caption="Foto capturada")

# ==================================
# FORMULÁRIO
# ==================================

st.subheader("📝 Registro Manual")

with st.form("registro", clear_on_submit=True):

    codigo = st.text_input("Código")

    col1, col2 = st.columns(2)

    with col1:
        hora_inicio = st.time_input(
            "Hora de Início",
            value=time(8, 0)
        )

    with col2:
        hora_fim = st.time_input(
            "Hora de Fim",
            value=time(9, 0)
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
            f"Eficiência: {eficiencia:.2f}%"
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
