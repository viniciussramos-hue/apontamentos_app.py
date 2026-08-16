import streamlit as st
import pandas as pd
import traceback

# 1. Configuração da página (DEVE ser a primeira linha executável)
st.set_page_config(
    page_title="Relatório de Auto Apontamento - PM/OTS",
    page_icon="📋",
    layout="wide",
)

# 2. CSS para manter a grade compacta e profissional
st.markdown("""
    <style>
        .stDataFrame { font-size: 11px; }
        .main { background-color: #f8f9fa; }
    </style>
""", unsafe_allow_html=True)

# 3. Título e Barra Lateral
st.title("📋 Relatório de Auto Apontamento - PM/OTS")
st.sidebar.header("📂 Fonte de Dados")
uploaded_file = st.sidebar.file_uploader("Envie sua planilha (.xlsx)", type=["xlsx"])

# 4. Bloco de processamento protegido
try:
    if uploaded_file is not None:
        # Carregamento do DataFrame
        df = pd.read_excel(uploaded_file, engine="openpyxl")
        
        # Limpeza básica de colunas
        df.columns = df.columns.astype(str).str.strip()
        
        # Filtros básicos (Slicers no topo)
        st.subheader("Filtros de Dados")
        cols = st.columns(3)
        
        # Identificação dinâmica de colunas
        col_desc = "Descrição" if "Descrição" in df.columns else df.columns[0]
        col_maq = "Máq." if "Máq." in df.columns else df.columns[0]
        col_grupo = "Grupo" if "Grupo" in df.columns else df.columns[0]
        
        with cols[0]:
            f_desc = st.multiselect("Descrição CT", options=df[col_desc].dropna().unique())
        with cols[1]:
            f_maq = st.multiselect("Máquina", options=df[col_maq].dropna().unique())
        with cols[2]:
            f_grupo = st.multiselect("Grupo", options=df[col_grupo].dropna().unique())
            
        # Filtragem
        df_f = df.copy()
        if f_desc: df_f = df_f[df_f[col_desc].isin(f_desc)]
        if f_maq: df_f = df_f[df_f[col_maq].isin(f_maq)]
        if f_grupo: df_f = df_f[df_f[col_grupo].isin(f_grupo)]
        
        # Exibição da grade
        st.subheader("Grade de Apontamentos")
        st.dataframe(df_f, use_container_width=True, hide_index=True)
        
    else:
        st.info("👋 **Aguardando envio:** Por favor, carregue sua planilha `.xlsx` na barra lateral para visualizar o painel.")

except Exception as e:
    st.error("❌ Erro ao processar os dados:")
    st.code(traceback.format_exc())
