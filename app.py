import streamlit as st
import pandas as pd

st.set_page_config(page_title="Relatório Maxion", layout="wide")

# Estilização para compactar a grade
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; }
        .stDataFrame { font-size: 11px; }
    </style>
""", unsafe_allow_html=True)

st.title("📋 Relatório de Auto Apontamento - PM/OTS")

uploaded_file = st.sidebar.file_uploader("Upload da planilha (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, engine="openpyxl")
    
    # Função para aplicar cores (condicional)
    def aplicar_estilo(df):
        styler = df.style
        # Coloração de fundo para a coluna 'Grupo' (verde claro se for PRODUÇÃO)
        styler = styler.map(lambda x: 'background-color: #d9ead3' if x == 'PRODUÇÃO' else '', subset=['Grupo'])
        # Coloração na coluna 'Duração' (Lógica simplificada)
        # Você pode ajustar os thresholds conforme o seu Excel
        styler = styler.map(lambda x: 'background-color: #f4cccc', subset=['Duração']) # Exemplo: Vermelho
        return styler

    # Filtros simples
    c1, c2, c3 = st.columns(3)
    with c1: filtro_ct = st.multiselect("CT", options=df["CT"].unique())
    with c2: filtro_maq = st.multiselect("Máquina", options=df["Máq."].unique())
    with c3: filtro_grupo = st.multiselect("Grupo", options=df["Grupo"].unique())

    # Filtragem
    df_f = df.copy()
    if filtro_ct: df_f = df_f[df_f["CT"].isin(filtro_ct)]
    if filtro_maq: df_f = df_f[df_f["Máq."].isin(filtro_maq)]
    if filtro_grupo: df_f = df_f[df_f["Grupo"].isin(filtro_grupo)]

    # Exibição com o Styler aplicado
    st.dataframe(df_f.style.apply(lambda x: ['background: #d9ead3' if x['Grupo'] == 'PRODUÇÃO' else '' for i in x], axis=1), 
                 use_container_width=True, hide_index=True)
else:
    st.info("Envie o arquivo .xlsx para visualizar a grade estilizada.")
