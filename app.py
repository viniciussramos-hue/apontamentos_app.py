import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Relatório Maxion", layout="wide")

st.markdown("""
    <style>
        .stDataFrame { font-size: 11px; }
    </style>
""", unsafe_allow_html=True)

st.title("📋 Relatório de Auto Apontamento - PM/OTS")

ARQUIVO_PADRAO = "03-Consultas_Apontamentos_rev02.xlsx"

@st.cache_data
def carregar_dados():
    if os.path.exists(ARQUIVO_PADRAO):
        try:
            return pd.read_excel(ARQUIVO_PADRAO, engine="openpyxl")
        except Exception as e:
            st.error(f"Erro ao abrir o Excel: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

df = carregar_dados()

# Se não achou na raiz, permite upload manual na barra lateral
if df.empty:
    st.sidebar.warning("Arquivo não encontrado no servidor. Faça o upload:")
    uploaded_file = st.sidebar.file_uploader("Upload da planilha (.xlsx)", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file, engine="openpyxl")

if not df.empty:
    # Padroniza os nomes das colunas removendo espaços extras
    df.columns = df.columns.astype(str).str.strip()

    # Identifica dinamicamente as colunas disponíveis para evitar KeyErrors
    col_desc = "Descrição" if "Descrição" in df.columns else df.columns[0]
    col_maq = "Máq." if "Máq." in df.columns else (df.columns[1] if len(df.columns) > 1 else df.columns[0])
    col_grupo = "Grupo" if "Grupo" in df.columns else (df.columns[2] if len(df.columns) > 2 else df.columns[0])

    # Filtros estilo Slicers acima da grade
    c1, c2, c3 = st.columns(3)
    with c1: 
        f_desc = st.multiselect("Descrição CT", options=df[col_desc].dropna().unique())
    with c2: 
        f_maq = st.multiselect("Máquina", options=df[col_maq].dropna().unique())
    with c3: 
        f_grupo = st.multiselect("Grupo", options=df[col_grupo].dropna().unique())

    df_f = df.copy()
    if f_desc: df_f = df_f[df_f[col_desc].isin(f_desc)]
    if f_maq: df_f = df_f[df_f[col_maq].isin(f_maq)]
    if f_grupo: df_f = df_f[df_f[col_grupo].isin(f_grupo)]

    # Grade com formatação condicional segura
    def colorir_linha(row):
        grupo_val = str(row.get(col_grupo, ""))
        cor = '#d9ead3' if 'PRODUÇÃO' in grupo_val.upper() else ''
        return [f'background-color: {cor}'] * len(row)

    try:
        st.dataframe(df_f.style.apply(colorir_linha, axis=1), use_container_width=True, hide_index=True)
    except Exception:
        st.dataframe(df_f, use_container_width=True, hide_index=True)
else:
    st.info("Aguardando o carregamento dos dados. Verifique se o arquivo `.xlsx` está na raiz do seu repositório no GitHub ou faça o upload ao lado.")
