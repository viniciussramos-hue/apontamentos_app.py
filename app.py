import streamlit as st

# DEVE ser a primeira instrução absoluta do script
st.set_page_config(
    page_title="Relatório de Auto Apontamento - PM/OTS",
    page_icon="📋",
    layout="wide",
)

from datetime import date
import pandas as pd

st.markdown(
    """
    <style>
        .main { background-color: #0e1117; }
        .stMetric { background-color: #161b22; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.3); border-left: 4px solid #2563eb; }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("📋 Relatório de Auto Apontamento - PM/OTS")
st.markdown("---")

st.sidebar.header("📂 Fonte de Dados")
arquivo_carregado = st.sidebar.file_uploader("Envie sua planilha (.xlsx)", type=["xlsx"])

@st.cache_data
def carregar_dados(uploaded_file):
    if uploaded_file is not None:
        try:
            xl = pd.ExcelFile(uploaded_file, engine="openpyxl")
            abas = xl.sheet_names
            # Procura pela aba de Apontamentos ou pega a primeira
            aba_alvo = "Apontamentos" if "Apontamentos" in abas else abas[0]
            df = xl.parse(aba_alvo)
            return df
        except Exception as e:
            st.error(f"Erro interno ao processar o arquivo Excel: {e}")
            return pd.DataFrame()
    else:
        return pd.DataFrame()

df = carregar_dados(arquivo_carregado)

if df.empty:
    st.info("👋 **Bem-vindo!** Por favor, envie o seu arquivo de consulta `.xlsx` utilizando o botão na **barra lateral à esquerda** para carregar o painel.")
else:
    try:
        # Padroniza os nomes das colunas (remove espaços extras)
        df.columns = df.columns.astype(str).str.strip()

        if "Máq." in df.columns:
            df["Máq."] = df["Máq."].astype(str).str.strip()

        # ==========================================
        # CABEÇALHO DO RELATÓRIO
        # ==========================================
        col_h1, col_h2, col_h3, col_h4 = st.columns(4)

        with col_h1:
            turnos_disp = sorted(df["T"].dropna().astype(str).unique().tolist()) if "T" in df.columns else ["1", "2", "3"]
            filtro_turno = st.selectbox("Turno (T):", options=turnos_disp)

        with col_h2:
            maqs_disp = sorted(df["Máq."].dropna().unique().tolist()) if "Máq." in df.columns else []
            filtro_maq = st.selectbox("Máquina (Máq.):", options=maqs_disp) if maqs_disp else "Nenhuma"

        with col_h3:
            filtro_data_cab = st.date_input("Data de Referência:", value=date.today())

        with col_h4:
            resp_preenchimento = st.text_input("Responsável pelo Preenchimento:", value="Operador Turno")

        st.markdown("---")

        # ==========================================
        # FILTROS AVANÇADOS (BARRA LATERAL)
        # ==========================================
        st.sidebar.header("🔍 Filtros da Planilha")
        
        filtro_desc_sidebar = (
            st.sidebar.multiselect("Descrição CT", options=df["Descrição"].dropna().astype(str).unique().tolist())
            if "Descrição" in df.columns
            else []
        )
        
        filtro_grupo_sidebar = (
            st.sidebar.multiselect("Grupo", options=df["Grupo"].dropna().astype(str).unique().tolist())
            if "Grupo" in df.columns
            else []
        )

        # ==========================================
        # APLICAÇÃO DOS FILTROS
        # ==========================================
        df_filtrado = df.copy()

        if filtro_turno and "T" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["T"].astype(str) == str(filtro_turno)]

        if filtro_maq and filtro_maq != "Nenhuma" and "Máq." in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["Máq."] == str(filtro_maq)]

        if filtro_desc_sidebar and "Descrição" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["Descrição"].astype(str).isin(filtro_desc_sidebar)]

        if filtro_grupo_sidebar and "Grupo" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["Grupo"].astype(str).isin(filtro_grupo_sidebar)]

        # ==========================================
        # ABAS DO PAINEL
        # ==========================================
        aba1, aba2 = st.tabs(["📝 Grade de Apontamento", "📋 Painel de Horas & Status"])

        with aba1:
            st.subheader("Registros no Formato Padrão Maxion PM/OTS")
            st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

        with aba2:
            st.subheader("Painel de Controle e Validação de Horas")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric(label="Total de Registros", value=f"{len(df_filtrado):,}")
            with c2:
                st.metric(label="Linhas Filtradas", value=f"{len(df_filtrado):,}")
            with c3:
                total_pecas = df_filtrado['Qtd.'].sum() if 'Qtd.' in df_filtrado.columns else 0
                st.metric(label="Volumes Totais (Qtd)", value=f"{total_pecas:,.0f}")
            with c4:
                st.metric(label="Status do Turno", value="Ativo")

            st.markdown("---")
            st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"❌ Erro ao renderizar os dados da planilha: {e}")
        st.warning("Verifique se as colunas da planilha correspondem exatamente ao esperado pelo layout (ex: 'T', 'Máq.', 'Descrição', 'Grupo', 'Qtd.').")
