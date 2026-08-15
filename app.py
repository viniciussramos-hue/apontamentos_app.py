from datetime import date, datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Relatório de Auto Apontamento - PM/OTS",
    page_icon="📋",
    layout="wide",
)

st.markdown(
    """
    <style>
        .main { background-color: #0e1117; }
        .stMetric { background-color: #161b22; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.3); border-left: 4px solid #2563eb; }
    </style>
""",
    unsafe_allow_html=True,
)

CAMINHO_ARQUIVO = "03-Consultas_Apontamentos_rev02.xlsb"


@st.cache_data
def carregar_dados():
    xl = pd.ExcelFile(CAMINHO_ARQUIVO, engine="pyxlsb")
    abas = xl.sheet_names
    aba_alvo = "Apontamentos" if "Apontamentos" in abas else abas[0]
    df = xl.parse(aba_alvo)

    df.columns = df.columns.astype(str).str.strip()

    if "Data" in df.columns:
        if pd.api.types.is_numeric_dtype(df["Data"]):
            df["Data"] = pd.to_datetime(df["Data"], unit="D", origin="1899-12-30")
        else:
            df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

    return df


try:
    df = carregar_dados()

    st.title("📋 Relatório de Auto Apontamento - PM/OTS")
    st.markdown("---")

    # ==========================================
    # CABEÇALHO DO RELATÓRIO (Layout Físico)
    # ==========================================
    col_h1, col_h2, col_h3, col_h4 = st.columns(4)

    with col_h1:
        turnos_disp = df["T"].dropna().unique().tolist() if "T" in df.columns else ["1º", "2º", "3º"]
        filtro_turno = st.selectbox("Turno:", options=turnos_disp)

    with col_h2:
        maqs_disp = df["Máq."].dropna().unique().tolist() if "Máq." in df.columns else []
        filtro_maq = st.selectbox("Máquina:", options=maqs_disp)

    with col_h3:
        filtro_data_cab = st.date_input("Data:", value=date.today())

    with col_h4:
        resp_preenchimento = st.text_input("Nome do Resp. pelo Preenchimento:", value="Operador Turno")

    st.markdown("---")

    # ==========================================
    # BARRA LATERAL DE FILTROS GLOBAIS
    # ==========================================
    st.sidebar.header("🔍 Filtros Avançados")
    
    filtro_desc_sidebar = (
        st.sidebar.multiselect("Descrição CT", options=df["Descrição"].dropna().unique().tolist())
        if "Descrição" in df.columns
        else []
    )
    filtro_grupo_sidebar = (
        st.sidebar.multiselect("Grupo", options=df["Grupo"].dropna().unique().tolist())
        if "Grupo" in df.columns
        else []
    )

    # ==========================================
    # APLICAÇÃO DOS FILTROS NA TABELA
    # ==========================================
    df_filtrado = df.copy()

    if filtro_turno and "T" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["T"] == filtro_turno]

    if filtro_maq and "Máq." in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Máq."] == filtro_maq]

    if filtro_desc_sidebar and "Descrição" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Descrição"].isin(filtro_desc_sidebar)]

    if filtro_grupo_sidebar and "Grupo" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Grupo"].isin(filtro_grupo_sidebar)]

    # Mapeamento para a grade no formato do relatório físico
    df_exibicao = pd.DataFrame()
    df_exibicao["O.P."] = df_filtrado["CT Item"] if "CT Item" in df_filtrado.columns else ""
    df_exibicao["Qtd O.P."] = df_filtrado["Qtd."] if "Qtd." in df_filtrado.columns else 0
    df_exibicao["Código Desenho"] = df_filtrado["Material"] if "Material" in df_filtrado.columns else ""
    df_exibicao["Código Maxion"] = df_filtrado["Descrição do PN"] if "Descrição do PN" in df_filtrado.columns else ""
    df_exibicao["Operação"] = df_filtrado["S/N"] if "S/N" in df_filtrado.columns else ""
    df_exibicao["Código Paradas"] = df_filtrado["Grupo"] if "Grupo" in df_filtrado.columns else ""
    df_exibicao["Início"] = df_filtrado["Hora Início"] if "Hora Início" in df_filtrado.columns else ""
    df_exibicao["Fim"] = df_filtrado["Hora Fim"] if "Hora Fim" in df_filtrado.columns else ""
    df_exibicao["Nº Bat"] = df_filtrado["Conjugado"] if "Conjugado" in df_filtrado.columns else 0
    df_exibicao["Pçs Boas"] = df_filtrado["Qtd."] if "Qtd." in df_filtrado.columns else 0
    df_exibicao["Sucata"] = 0
    df_exibicao["Nº Etiqueta"] = ""
    df_exibicao["Motivo / Problemas"] = df_filtrado["Descrição"] if "Descrição" in df_filtrado.columns else ""

    # ==========================================
    # ABAS DO PAINEL (Apenas Grade e Painel de Horas)
    # ==========================================
    aba1, aba2 = st.tabs(["📝 Grade de Apontamento", "📋 Painel de Horas & Status"])

    with aba1:
        st.subheader("Registros e Lançamentos no Formato PM/OTS")
        st.dataframe(df_exibicao, use_container_width=True, hide_index=True)

    with aba2:
        st.subheader("Painel de Controle e Validação de Horas")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric(label="Total de Registros", value=f"{len(df_filtrado):,}")
        with c2:
            st.metric(label="Linhas Apontadas", value=f"{len(df_exibicao):,}")
        with c3:
            total_pecas = df_exibicao['Pçs Boas'].sum() if 'Pçs Boas' in df_exibicao.columns else 0
            st.metric(label="Volumes Totais", value=f"{total_pecas:,.0f}")
        with c4:
            st.metric(label="Status Turno", value="Ativo")

        st.markdown("---")
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ Erro crítico ao processar o arquivo de apontamentos: {e}")
