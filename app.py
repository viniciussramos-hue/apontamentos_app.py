import streamlit as st
import pandas as pd
from datetime import date

# Configuração da página como Wide (Layout Largo)
st.set_page_config(page_title="Relatório de Apontamento - Maxion", layout="wide")

# Estilização CSS para o layout Maxion (Azul, Branco, Cinza)
st.markdown("""
    <style>
        .stApp { background-color: #f0f2f6; }
        .stMetric { background-color: #ffffff; border: 1px solid #e0e0e0; padding: 15px; border-radius: 5px; }
        h1 { color: #004a99; }
        .stDataFrame { border: 1px solid #004a99; }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho com logo e título
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    st.image("https://www.maxionwheels.com/en/assets/images/logo-maxion-wheels.png", width=200)
with col_titulo:
    st.title("Relatório de Auto Apontamento")
    st.caption("Maxion Structural Components - Gestão PM/OTS")

# Upload de dados
st.sidebar.header("📁 Fonte de Dados")
uploaded_file = st.sidebar.file_uploader("Upload da planilha (.xlsx)", type=["xlsx"])

# Função de carga
@st.cache_data
def carregar_dados(file):
    if file:
        return pd.read_excel(file, engine="openpyxl")
    return pd.DataFrame()

df = carregar_dados(uploaded_file)

if not df.empty:
    # Filtros superioress (Estilo Slicers)
    st.markdown("### Filtros de Seleção")
    c_f1, c_f2 = st.columns([3, 1])
    
    with c_f1:
        desc_ct = st.multiselect("Descrição CT", options=df["Descrição"].unique())
    with c_f2:
        grupos = st.multiselect("Grupo", options=df["Grupo"].unique())

    # Filtros laterais (Data e Máquina)
    st.sidebar.markdown("---")
    data_sel = st.sidebar.date_input("Filtrar Data", value=date.today())
    maq_sel = st.sidebar.multiselect("Máquina", options=sorted(df["Máq."].unique()))

    # Aplicação dos filtros
    df_f = df.copy()
    if desc_ct: df_f = df_f[df_f["Descrição"].isin(desc_ct)]
    if grupos: df_f = df_f[df_f["Grupo"].isin(grupos)]
    if maq_sel: df_f = df_f[df_f["Máq."].isin(maq_sel)]

    # Tabela principal com as colunas na ordem exata da sua imagem
    st.subheader("Grade de Apontamentos")
    cols_exibicao = [
        "CT", "CT Item", "Data", "Hora Início", "Hora Fim", "Duração", 
        "Máq.", "T", "S/N", "Grupo", "Descrição", "Material", 
        "Descrição do PN", "Conjugado", "Qtd.", "Std PN", 
        "Tempo_Std.", "QtPrevista.", "Nº Operadores.", "Eficiência"
    ]
    
    # Exibir apenas colunas existentes no seu arquivo
    st.dataframe(df_f[[c for c in cols_exibicao if c in df_f.columns]], use_container_width=True)

else:
    st.info("Por favor, faça o upload da sua planilha `.xlsx` para visualizar o layout de apontamentos.")
