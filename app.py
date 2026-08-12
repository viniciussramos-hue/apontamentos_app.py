import pandas as pd
import streamlit as st

# Configuração da página para ocupar a largura total
st.set_page_config(
    page_title="Gerenciador de Apontamentos", page_icon="📊", layout="wide"
)

st.title("📊 Painel de Apontamentos e Indicadores")

# Caminho fixo do arquivo no repositório local
CAMINHO_ARQUIVO = "03-Consultas_Apontamentos_rev02.xlsb"


@st.cache_data
def carregar_dados():
  # Utiliza o motor 'pyxlsb' para ler arquivos binários do Excel (.xlsb)
  # Lê diretamente a aba 'Apontamentos'
  df = pd.read_excel(
      CAMINHO_ARQUIVO, sheet_name="Apontamentos", engine="pyxlsb"
  )
  return df


try:
  df = carregar_dados()

  # Garantir formato de data se a coluna existir
  if "Data" in df.columns:
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

  # ==========================================
  # BARRA LATERAL DE FILTROS
  # ==========================================
  st.sidebar.header("🔍 Filtros de Consulta")

  # 1. Filtro de Datas
  if "Data" in df.columns and not df["Data"].dropna().empty:
    min_date = df["Data"].min().date()
    max_date = df["Data"].max().date()
    filtro_data = st.sidebar.date_input(
        "Período (Data)", value=(min_date, max_date), format="DD/MM/YYYY"
    )
  else:
    filtro_data = None

  # 2. Filtro de Máquinas
  col_maq = (
      "Máq." if "Máq." in df.columns else ("Maq" if "Maq" in df.columns else None)
  )
  maquinas_disponiveis = (
      df[col_maq].dropna().unique().tolist() if col_maq else []
  )
  filtro_maq = st.sidebar.multiselect("Máquinas", options=maquinas_disponiveis)

  # 3. Filtro de Turno (T)
  col_turno = "T" if "T" in df.columns else None
  turnos_disponiveis = (
      df[col_turno].dropna().unique().tolist() if col_turno else []
  )
  filtro_turno = st.sidebar.multiselect("Turno (T)", options=turnos_disponiveis)

  # 4. Filtro de Centro de Trabalho (CT)
  col_ct = "CT" if "CT" in df.columns else None
  ct_disponiveis = df[col_ct].dropna().unique().tolist() if col_ct else []
  filtro_ct = st.sidebar.multiselect("Centro de Trabalho (CT)", options=ct_disponiveis)

  # 5. Filtro de Descrição CT / Descrição
  col_desc = (
      "Descrição"
      if "Descrição" in df.columns
      else ("Descricao" if "Descricao" in df.columns else None)
  )
  desc_disponiveis = df[col_desc].dropna().unique().tolist() if col_desc else []
  filtro_desc = st.sidebar.multiselect(
      "Descrição / Descrição CT", options=desc_disponiveis
  )

  # 6. Filtro de Grupo
  col_grupo = "Grupo" if "Grupo" in df.columns else None
  grupo_disponiveis = (
      df[col_grupo].dropna().unique().tolist() if col_grupo else []
  )
  filtro_grupo = st.sidebar.multiselect("Grupo", options=grupo_disponiveis)

  # ==========================================
  # APLICAÇÃO DOS FILTROS NO DATAFRAME
  # ==========================================
  df_filtrado = df.copy()

  if filtro_data and len(filtro_data) == 2 and "Data" in df.columns:
    start_date, end_date = filtro_data
    df_filtrado = df_filtrado[
        (df_filtrado["Data"].dt.date >= start_date)
        & (df_filtrado["Data"].dt.date <= end_date)
    ]

  if filtro_maq and col_maq:
    df_filtrado = df_filtrado[df_filtrado[col_maq].isin(filtro_maq)]

  if filtro_turno and col_turno:
    df_filtrado = df_filtrado[df_filtrado[col_turno].isin(filtro_turno)]

  if filtro_ct and col_ct:
    df_filtrado = df_filtrado[df_filtrado[col_ct].isin(filtro_ct)]

  if filtro_desc and col_desc:
    df_filtrado = df_filtrado[df_filtrado[col_desc].isin(filtro_desc)]

  if filtro_grupo and col_grupo:
    df_filtrado = df_filtrado[df_filtrado[col_grupo].isin(filtro_grupo)]

  # ==========================================
  # EXIBIÇÃO DA TABELA NA TELA PRINCIPAL
  # ==========================================
  st.subheader(
      f"📋 Dados da Aba: `Apontamentos` (Registros exibidos:"
      f" {len(df_filtrado)} de {len(df)})"
  )

  st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

except Exception as e:
  st.error(f"Erro ao carregar o arquivo local: {e}")
