import pandas as pd
import streamlit as st

# Configuração da página em modo expandido
st.set_page_config(
    page_title="Gerenciador de Apontamentos", page_icon="📊", layout="wide"
)

st.title("📊 Painel de Apontamentos e Indicadores")

CAMINHO_ARQUIVO = "03-Consultas_Apontamentos_rev02.xlsb"


@st.cache_data
def carregar_dados():
  try:
    df = pd.read_excel(
        CAMINHO_ARQUIVO, sheet_name="Apontamentos", engine="pyxlsb"
    )
    # Tratamento da coluna Data serial do Excel se existir
    if "Data" in df.columns:
      if pd.api.types.is_numeric_dtype(df["Data"]):
        df["Data"] = pd.to_datetime(df["Data"], unit="D", origin="1899-12-30")
      else:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    return df
  except Exception as e:
    st.error(
        f"Erro ao ler o arquivo Excel. Verifique se o pyxlsb está instalado:"
        f" {e}"
    )
    return pd.DataFrame()


df = carregar_dados()

if not df.empty:
  # ==========================================
  # PAINEL SUPERIOR DE FILTRAGEM (SLICERS)
  # ==========================================
  st.markdown("### 🎛️ Filtros Rápidos")

  # Identificar dinamicamente as colunas existentes para evitar erros
  col_desc = next(
      (
          c
          for c in ["Descrição de Atividade", "Descrição", "Descricao"]
          if c in df.columns
      ),
      None,
  )
  col_grupo = next(
      (c for c in ["Grupo de Paradas", "Grupo"] if c in df.columns), None
  )
  col_maq = next(
      (c for c in ["Máquina", "Máq.", "Maq"] if c in df.columns), None
  )
  col_turno = next((c for c in ["Turno", "T"] if c in df.columns), None)
  col_ct = "CT" if "CT" in df.columns else None

  top_col1, top_col2, top_col3 = st.columns([2, 2, 1])

  with top_col1:
    desc_opcoes = (
        df[col_desc].dropna().unique().tolist()
        if col_desc and col_desc in df.columns
        else []
    )
    filtro_desc_rapido = st.multiselect(
        "Filtrar por Descrição da Atividade", options=desc_opcoes
    )

  with top_col2:
    grupo_opcoes = (
        df[col_grupo].dropna().unique().tolist()
        if col_grupo and col_grupo in df.columns
        else []
    )
    filtro_grupo_rapido = st.multiselect(
        "Filtrar por Grupo", options=grupo_opcoes
    )

  with top_col3:
    turno_opcoes = (
        df[col_turno].dropna().unique().tolist()
        if col_turno and col_turno in df.columns
        else []
    )
    filtro_turno_rapido = st.multiselect("Turno", options=turno_opcoes)

  # Filtros complementares na barra lateral
  st.sidebar.header("🔍 Filtros Adicionais")

  if "Data" in df.columns and not df["Data"].dropna().empty:
    min_date = df["Data"].min().date()
    max_date = df["Data"].max().date()
    filtro_data = st.sidebar.date_input(
        "Período (Data)", value=(min_date, max_date), format="DD/MM/YYYY"
    )
  else:
    filtro_data = None

  maquinas_disponiveis = (
      df[col_maq].dropna().unique().tolist()
      if col_maq and col_maq in df.columns
      else []
  )
  filtro_maq = st.sidebar.multiselect("Máquinas", options=maquinas_disponiveis)

  ct_disponiveis = (
      df[col_ct].dropna().unique().tolist()
      if col_ct and col_ct in df.columns
      else []
  )
  filtro_ct = st.sidebar.multiselect(
      "Centro de Trabalho (CT)", options=ct_disponiveis
  )

  # ==========================================
  # APLICAÇÃO DOS FILTROS
  # ==========================================
  df_filtrado = df.copy()

  if filtro_data and len(filtro_data) == 2 and "Data" in df.columns:
    start_date, end_date = filtro_data
    df_filtrado = df_filtrado[
        (df_filtrado["Data"].dt.date >= start_date)
        & (df_filtrado["Data"].dt.date <= end_date)
    ]

  if filtro_desc_rapido and col_desc and col_desc in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado[col_desc].isin(filtro_desc_rapido)]

  if filtro_grupo_rapido and col_grupo and col_grupo in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado[col_grupo].isin(filtro_grupo_rapido)]

  if filtro_turno_rapido and col_turno and col_turno in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado[col_turno].isin(filtro_turno_rapido)]

  if filtro_maq and col_maq and col_maq in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado[col_maq].isin(filtro_maq)]

  if filtro_ct and col_ct and col_ct in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado[col_ct].isin(filtro_ct)]

  # ==========================================
  # EXIBIÇÃO DA TABELA DETALHADA
  # ==========================================
  st.markdown("---")
  st.subheader(
      f"📋 Apontamentos Detalhados (Exibindo {len(df_filtrado)} de"
      f" {len(df)} registros)"
  )

  st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

else:
  st.warning(
      "O arquivo de apontamentos não pôde ser carregado. Verifique se o nome"
      " do arquivo e o formato estão corretos."
  )
