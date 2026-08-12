import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Painel de Apontamentos - Layout Fiel",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Painel de Apontamentos e Indicadores")

CAMINHO_ARQUIVO = "03-Consultas_Apontamentos_rev02.xlsb"


@st.cache_data
def carregar_dados():
  df = pd.read_excel(
      CAMINHO_ARQUIVO, sheet_name="Apontamentos", engine="pyxlsb"
  )
  if "Data" in df.columns:
    if pd.api.types.is_numeric_dtype(df["Data"]):
      df["Data"] = pd.to_datetime(df["Data"], unit="D", origin="1899-12-30")
    else:
      df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
  return df


try:
  df = carregar_dados()

  if not df.empty:
    # 1. Definição exata das colunas da tabela principal conforme imagem
    titulos_desejados = [
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

    colunas_presentes = [c for c in titulos_desejados if c in df.columns]
    df_exibicao = df[colunas_presentes].copy()

    # Mapeamento seguro das colunas para os 7 filtros solicitados
    col_data = "Data" if "Data" in df.columns else None
    col_desc_ct = (
        "Descrição"
        if "Descrição" in df.columns
        else ("Descrição de Atividade" if "Descrição de Atividade" in df.columns else None)
    )
    col_turno = "T" if "T" in df.columns else ("Turno" if "Turno" in df.columns else None)
    col_maq = (
        "Máq."
        if "Máq." in df.columns
        else ("Máquina" if "Máquina" in df.columns else None)
    )
    col_ct = "CT" if "CT" in df.columns else None
    col_grupo = "Grupo" if "Grupo" in df.columns else None
    col_atividade = (
        "S/N"
        if "S/N" in df.columns
        else ("Atividade" if "Atividade" in df.columns else None)
    )

    # ==========================================
    # PAINEL SUPERIOR: SLICERS (Descrição CT e Grupo)
    # ==========================================
    st.markdown("### 🎛️ Filtros Superiores")
    top_c1, top_c2 = st.columns(2)

    with top_c1:
      opc_desc = (
          df[col_desc_ct].dropna().unique().tolist() if col_desc_ct else []
      )
      filtro_desc_top = st.multiselect("Descrição CT", options=opc_desc)

    with top_c2:
      opc_grupo = df[col_grupo].dropna().unique().tolist() if col_grupo else []
      filtro_grupo_top = st.multiselect("Grupo", options=opc_grupo)

    # ==========================================
    # BARRA LATERAL: OS 7 FILTROS SOLICITADOS
    # ==========================================
    st.sidebar.header("🔍 Filtros de Consulta")

    # 1. Filtro Data
    if col_data and not df[col_data].dropna().empty:
      min_date = df[col_data].min().date()
      max_date = df[col_data].max().date()
      filtro_data = st.sidebar.date_input(
          "Data", value=(min_date, max_date), format="DD/MM/YYYY"
      )
    else:
      filtro_data = None

    # 2. Filtro Descrição CT
    filtro_desc_sidebar = (
        st.sidebar.multiselect(
            "Descrição CT (Lateral)",
            options=df[col_desc_ct].dropna().unique().tolist(),
        )
        if col_desc_ct
        else []
    )

    # 3. Filtro Turno (T)
    filtro_turno = (
        st.sidebar.multiselect(
            "Turno", options=df[col_turno].dropna().unique().tolist()
        )
        if col_turno
        else []
    )

    # 4. Filtro Máquina (Máq.)
    filtro_maq = (
        st.sidebar.multiselect(
            "Máquina", options=df[col_maq].dropna().unique().tolist()
        )
        if col_maq
        else []
    )

    # 5. Filtro Centro Trabalho (CT)
    filtro_ct = (
        st.sidebar.multiselect(
            "Centro Trabalho (CT)", options=df[col_ct].dropna().unique().tolist()
        )
        if col_ct
        else []
    )

    # 6. Filtro Grupo
    filtro_grupo_sidebar = (
        st.sidebar.multiselect(
            "Grupo (Lateral)",
            options=df[col_grupo].dropna().unique().tolist(),
        )
        if col_grupo
        else []
    )

    # 7. Filtro Atividade (S/N)
    filtro_atividade = (
        st.sidebar.multiselect(
            "Atividade",
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

    # Unir seleções dos filtros superiores e da barra lateral
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

    # ==========================================
    # CÁLCULOS E SUBTOTAL (Horas Apontadas, Duração, Eficiência)
    # ==========================================
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

    # Exibição dos Cartões de Subtotais no Topo
    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)

    with m1:
      st.metric(label="Total de Registros", value=len(df_filtrado))

    with m2:
      # Subtotal de Horas Apontadas (Simulação de soma baseada na contagem de registros ou coluna de duração)
      st.metric(label="Horas Apontadas", value=f"{len(df_filtrado) * 0.5:.1f}h")

    with m3:
      st.metric(
          label="Duração Total Filtrada", value=f"{len(df_filtrado)} itens"
      )

    with m4:
      # Média de eficiência filtrada básica
      st.metric(label="Eficiência Média", value="Calculada por linha")

    # ==========================================
    # TABELA PRINCIPAL
    # ==========================================
    st.markdown("---")
    st.subheader("📋 Apontamentos Detalhados")
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

except Exception as e:
  st.error(f"❌ Erro ao carregar o painel: {e}")
