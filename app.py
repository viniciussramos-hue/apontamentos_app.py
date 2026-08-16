import streamlit as st
import pandas as pd

st.set_page_config(page_title="Relatório Maxion", layout="wide")

st.markdown("""
    <style>
        .stDataFrame { font-size: 11px; }
    </style>
""", unsafe_allow_html=True)

st.title("📋 Relatório de Auto Apontamento - PM/OTS")

# Barra lateral para upload seguro do arquivo
st.sidebar.header("📂 Fonte de Dados")
uploaded_file = st.sidebar.file_uploader("Envie sua planilha (.xlsx)", type=["xlsx"])

df = pd.DataFrame()

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}")

if df.empty:
    st.info("👋 **Bem-vindo!** Para começar, envie o seu arquivo de consulta `.xlsx` utilizando o botão de upload na **barra lateral à esquerda**.")
else:
    try:
        # Padroniza os nomes das colunas
        df.columns = df.columns.astype(str).str.strip()

        col_desc = "Descrição" if "Descrição" in df.columns else df.columns[0]
        col_maq = "Máq." if "Máq." in df.columns else df.columns[0]
        col_grupo = "Grupo" if "Grupo" in df.columns else df.columns[0]

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

        def colorir_linha(row):
            grupo_val = str(row.get(col_grupo, ""))
            cor = '#d9ead3' if 'PRODUÇÃO' in grupo_val.upper() else ''
            return [f'background-color: {cor}'] * len(row)

        st.dataframe(df_f.style.apply(colorir_linha, axis=1), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Erro ao processar os dados da tabela: {e}")
