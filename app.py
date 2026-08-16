import streamlit as st
import pandas as pd

st.set_page_config(page_title="Relatório Maxion", layout="wide")

# Estilo para ficar com cara de planilha industrial
st.markdown("""
    <style>
        .stDataFrame { font-size: 11px; }
        .css-1544g2n { padding-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

st.title("📋 Relatório de Auto Apontamento - PM/OTS")

# Tenta carregar o arquivo que você subiu no GitHub automaticamente
ARQUIVO_PADRAO = "03-Consultas_Apontamentos_rev02.xlsx"

@st.cache_data
def carregar_dados():
    try:
        return pd.read_excel(ARQUIVO_PADRAO, engine="openpyxl")
    except:
        return pd.DataFrame()

# Tenta carregar do GitHub, se não conseguir, abre o upload
df = carregar_dados()

if df.empty:
    st.sidebar.warning("Arquivo não encontrado no servidor. Faça upload:")
    uploaded_file = st.sidebar.file_uploader("Upload da planilha", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file, engine="openpyxl")

if not df.empty:
    # Filtros estilo Slicers acima da grade
    c1, c2, c3 = st.columns(3)
    with c1: f_desc = st.multiselect("Descrição CT", options=df["Descrição"].unique())
    with c2: f_maq = st.multiselect("Máquina", options=df["Máq."].unique())
    with c3: f_grupo = st.multiselect("Grupo", options=df["Grupo"].unique())

    df_f = df.copy()
    if f_desc: df_f = df_f[df_f["Descrição"].isin(f_desc)]
    if f_maq: df_f = df_f[df_f["Máq."].isin(f_maq)]
    if f_grupo: df_f = df_f[df_f["Grupo"].isin(f_grupo)]

    # Grade com cores condicional (o "pulo do gato" para ficar igual ao seu Excel)
    def colorir_linha(row):
        cor = '#d9ead3' if row['Grupo'] == 'PRODUÇÃO' else ''
        return [f'background-color: {cor}'] * len(row)

    st.dataframe(df_f.style.apply(colorir_linha, axis=1), use_container_width=True, hide_index=True)
else:
    st.info("Aguardando carregamento dos dados...")
