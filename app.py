import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gerenciador de Apontamentos", page_icon="📊", layout="wide"
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
    # ==========================================
    # BARRA LATERAL COM FILTROS PARA TODAS AS COLUNAS
    # ==========================================
    st.sidebar.header("🔍 Filtros por Coluna")

    filtros = {}

    # 1. Filtro de Data (Especial por período)
    if "Data" in df.columns and not df["Data"].dropna().empty:
      min_date = df["Data"].min().date()
      max_date = df["Data"].max().date()
      filtro_data = st.sidebar.date_input(
          "Data", value=(min_date, max_date), format="DD/MM/YYYY"
      )
    else:
      filtro_data = None

    # 2. Filtros Multiselect para todas as demais colunas presentes na aba
    colunas_excluir = ["Data"]
    for col in df.columns:
      if col not in colunas_excluir:
        opcoes = df[col].dropna().unique().tolist()
        # Limita visualmente a quantidade de opções se forem muitas, mas mantém funcional
        filtros[col] = st.sidebar.multiselect(f"{col}", options=opcoes)

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

    for col, selecao in filtros.items():
      if selecao:
        df_filtrado = df_filtrado[df_filtrado[col].isin(selecao)]

    # ==========================================
    # EXIBIÇÃO DA TABELA COM OS TÍTULOS EXATOS
    # ==========================================
    st.markdown("---")
    st.subheader(
        f"📋 Apontamentos Detalhados (Exibindo {len(df_filtrado)} de"
        f" {len(df)} registros)"
    )

    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

except Exception as e:
  st.error(f"❌ Erro ao processar os dados: {e}")
