import streamlit as st
import pandas as pd

# 1. Configuração de tela larga
st.set_page_config(page_title="Relatório Maxion", layout="wide")

# 2. CSS para compactar o layout
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 0rem; }
        .stDataFrame { font-size: 12px; }
    </style>
""", unsafe_allow_html=True)

# 3. Título alinhado à esquerda e upload
st.title("📋 Relatório de Auto Apontamento")
uploaded_file = st.sidebar.file_uploader("Upload da planilha (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, engine="openpyxl")
    
    # --- FILTROS SUPERIORES (Estilo Slicers) ---
    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        filtro_desc = st.multiselect("Descrição CT", options=df["Descrição"].unique())
    with c2:
        filtro_grupo = st.multiselect("Grupo", options=df["Grupo"].unique())
    with c3:
        filtro_maq = st.multiselect("Máquina", options=df["Máq."].unique())

    # --- FILTRAGEM ---
    df_f = df.copy()
    if filtro_desc: df_f = df_f[df_f["Descrição"].isin(filtro_desc)]
    if filtro_grupo: df_f = df_f[df_f["Grupo"].isin(filtro_grupo)]
    if filtro_maq: df_f = df_f[df_f["Máq."].isin(filtro_maq)]

    # --- GRADE DE DADOS (Layout denso) ---
    st.dataframe(df_f, use_container_width=True, hide_index=True)
else:
    st.info("Faça o upload do arquivo para ver a grade de dados.")
