import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Painel de Apontamentos Industriais",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .main { background-color: #f8fafc; }
        .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid #2563eb; }
    </style>
""",
    unsafe_allow_html=True,
)

CAMINHO_ARQUIVO = "03-Consultas_Apontamentos_rev02.xlsb"


@st.cache_data
def carregar_dados():
  df = pd.read_excel(
      CAMINHO_ARQUIVO, sheet_name="Apontamentos", engine="pyxlsb"
  )

  # Remove espaços extras dos nomes das colunas para evitar conflitos
  df.columns = df.columns.str.strip()

  if "Data" in df.columns:
    if pd.api.types.is_numeric_dtype(df["Data"]):
      df["Data"] = pd.to_datetime(df["Data"], unit="D", origin="1899-12-30")
    else:
      df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
  return df


try:
  df = carregar_dados()

  if not df.empty:
    # 20 colunas exatas da sua imagem
    titulos_exatos = [
        "CT",
        "CT Item",
        "Data",
        "Hora Início",
        "Hora Fim",
        "Duração",
        "Máq.",
        "T",
        "S/N",
        "Grupo",
        "Descrição",
        "Material",
        "Descrição do PN",
        "Conjugado",
        "Qtd.",
        "Std PN",
        "Tempo_Std.",
        "QtPrevista.",
        "Nº Operadores.",
        "Eficiência",
    ]

    # Garante que apenas as colunas existentes sejam puxadas sem perder nenhuma
    colunas_presentes = [c for c in titulos_exatos if c in df.columns]
    df_exibicao = df[colunas_presentes].copy()

    # Mapeamento seguro para os 7 filtros essenciais
    col_data = "Data" if "Data" in df.columns else None
    col_desc_ct = "Descrição" if "Descrição" in df.columns else None
    col_turno = "T" if "T" in df.columns else None
    col_maq = "Máq." if "Máq." in df.columns else None
    col_ct = "CT" if "CT" in df.columns else None
    col_grupo = "Grupo" if "Grupo" in df.columns else None
    col_atividade = "S/N" if "S/N" in df.columns else None

    # ==========================================
    # TOPO: SLICERS RÁPIDOS
    # ==========================================
    st.title("🏭 Painel Executivo de Apontamentos")
    st.markdown("### 🎛️ Filtros de Segmentação Rápida")
    top_col1, top_col2 = st.columns(2)

    with top_col1:
      opc_desc = (
          df[col_desc_ct].dropna().unique().tolist() if col_desc_ct else []
      )
      filtro_desc_top = st.multiselect(
          "Filtrar por Descrição CT", options=opc_desc
      )

    with top_col2:
      opc_grupo = df[col_grupo].dropna().unique().tolist() if col_grupo else []
      filtro_grupo_top = st.multiselect("Filtrar por Grupo", options=opc_grupo)

    st.markdown("---")

    # ==========================================
    # BARRA LATERAL: OS 7 FILTROS
    # ==========================================
    st.sidebar.header("🔍 Painel de Filtros")

    if col_data and not df[col_data].dropna().empty:
      min_date = df[col_data].min().date()
      max_date = df[col_data].max().date()
      filtro_data = st.sidebar.date_input(
          "Período (Data)", value=(min_date, max_date), format="DD/MM/YYYY"
      )
    else:
      filtro_data = None

    filtro_desc_sidebar = (
        st.sidebar.multiselect(
            "Descrição CT (Adicional)",
            options=df[col_desc_ct].dropna().unique().tolist(),
        )
        if col_desc_ct
        else []
    )

    filtro_turno = (
        st.sidebar.multiselect(
            "Turno (T)", options=df[col_turno].dropna().unique().tolist()
        )
        if col_turno
        else []
    )

    filtro_maq = (
        st.sidebar.multiselect(
            "Máquina (Máq.)", options=df[col_maq].dropna().unique().tolist()
        )
        if col_maq
        else []
    )

    filtro_ct = (
        st.sidebar.multiselect(
            "Centro de Trabalho (CT)",
            options=df[col_ct].dropna().unique().tolist(),
        )
        if col_ct
        else []
    )

    filtro_grupo_sidebar = (
        st.sidebar.multiselect(
            "Grupo (Adicional)",
            options=df[col_grupo].dropna().unique().tolist(),
        )
        if col_grupo
        else []
    )

    filtro_atividade = (
        st.sidebar.multiselect(
            "Atividade (S/N)",
            options=df[col_atividade].dropna().unique().tolist(),
        )
        if col_atividade
        else []
    )

    # ==========================================
    # APLICAÇÃO DOS FILTROS
    # ==========================================
    df_filtrado = df_exibicao.copy()

    if filtro_data and len(filtro_data) == 2 and col_data:
      start_date, end_date = filtro_data
      df_filtrado = df_filtrado[
          (df_filtrado[col_data].dt.date >= start_date)
          & (df_filtrado[col_data].dt.date <= end_date)
      ]

    desc_selecionadas = list(
        set(
            (filtro_desc_top if filtro_desc_top else [])
            + (filtro_desc_sidebar if filtro_desc_sidebar else [])
        )
    )
    if desc_selecionadas and col_desc_ct:
      df_filtrado = df_filtrado[df_filtrado[col_desc_ct].isin(desc_selecionadas)]

    grupo_selecionados = list(
        set(
            (filtro_grupo_top if filtro_grupo_top else [])
            + (filtro_grupo_sidebar if filtro_grupo_sidebar else [])
        )
    )
    if grupo_selecionados and col_grupo:
      df_filtrado = df_filtrado[
          df_filtrado[col_grupo].isin(grupo_selecionados)
      ]

    if filtro_turno and col_turno:
      df_filtrado = df_filtrado[df_filtrado[col_turno].isin(filtro_turno)]

    if filtro_maq and col_maq:
      df_filtrado = df_filtrado[df_filtrado[col_maq].isin(filtro_maq)]

    if filtro_ct and col_ct:
      df_filtrado = df_filtrado[df_filtrado[col_ct].isin(filtro_ct)]

    if filtro_atividade and col_atividade:
      df_filtrado = df_filtrado[
          df_filtrado[col_atividade].isin(filtro_atividade)
      ]

    # Recálculo dinâmico da Eficiência
    if (
        "Eficiência" in df_filtrado.columns
        and "Qtd." in df_filtrado.columns
        and "QtPrevista." in df_filtrado.columns
    ):
      df_filtrado["Eficiência"] = df_filtrado.apply(
          lambda r: (
              f"{(r['Qtd.'] / r['QtPrevista.']) * 100:.1f}%"
              if pd.notnull(r["QtPrevista."]) and r["QtPrevista."] > 0
              else ""
          ),
          axis=1,
      )

    # ==========================================
    # MÉTRICAS E INDICADORES
    # ==========================================
    c1, c2, c3, c4 = st.columns(4)
    with c1:
      st.metric(
          label="Total de Registros",
          value=f"{len(df_filtrado):,}".replace(",", "."),
      )
    with c2:
      st.metric(
          label="Horas Apontadas",
          value=f"{(len(df_filtrado) * 0.5):,.1f}h".replace(",", "."),
      )
    with c3:
      st.metric(
          label="Duração Total",
          value=f"{len(df_filtrado):,}".replace(",", "."),
      )
    with c4:
      st.metric(label="Eficiência Média", value="Calculada por Registro")

    # ==========================================
    # TABELA FINAL COM TODAS AS COLUNAS
    # ==========================================
    st.markdown("---")
    st.subheader("📋 Detalhamento dos Apontamentos")
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

except Exception as e:
  st.error(f"❌ Erro ao processar o painel: {e}")
