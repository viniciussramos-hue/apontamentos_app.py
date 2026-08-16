from datetime import date
import pandas as pd
import streamlit as st
import os

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

CAMINHO_ARQUIVO = "03-Consultas_Apontamentos_rev02.xlsx"

st.title("📋 Relatório de Auto Apontamento - PM/OTS")
st.markdown("---")

st.sidebar.header("📂 Fonte de Dados")
arquivo_carregado = st.sidebar.file_uploader("Substituir planilha (.xlsx)", type=["xlsx"])

@st.cache_data
def carregar_dados(uploaded_file):
    if uploaded_file is not None:
        return pd.read_excel(uploaded_file, engine="openpyxl")
    elif os.path.exists(CAMINHO_ARQUIVO):
        return pd.read_excel(CAMINHO_ARQUIVO, engine="openpyxl")
    else:
        # Retorna dados falsos de exemplo para o app abrir caso o arquivo não esteja na pasta ainda
        return pd.DataFrame({
            "CT": ["PM05", "PM05"],
            "CT Item": ["PM04", "PM05"],
            "Data": [pd.Timestamp.today(), pd.Timestamp.today()],
            "Hora Início": ["00:00:00", "00:10:00"],
            "Hora Fim": ["00:10:00", "02:10:00"],
            "Duração": ["-00:10:00", "-02:00:00"],
            "Máq.": ["C2635", "C2635"],
            "T": ["3", "3"],
            "S/N": ["S", "N"],
            "Grupo": ["ATIVIDADES INTERATIVAS", "PRODUÇÃO"],
            "Descrição": ["REUNIÃO DDS", "PRODUZINDO"],
            "Material": ["5087140600EST", "5087140600EST"],
            "Descrição do PN": ["CHAPA MBB 9793130046", "CHAPA MBB 9793130046"],
            "Conjugado": ["(vazio)", "(vazio)"],
            "Qtd.": [0, 630],
            "Std PN": [240, 240],
            "Tempo_Std.": ["0:00:00", "2:37:30"],
            "QtPrevista.": [40, 480],
            "Nº Operadores.": [4, 4],
            "Eficiência": ["", "131,3%"]
        })

try:
    df = carregar_dados(arquivo_carregado)

    if df.empty:
        st.warning("⚠️ O arquivo carregado está vazio.")
    else:
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
    st.error(f"❌ Erro detectado ao executar o aplicativo: {e}")
    st.info("💡 Dica: Verifique se o arquivo `03-Consultas_Apontamentos_rev02.xlsx` está na raiz do seu repositório no GitHub.")
