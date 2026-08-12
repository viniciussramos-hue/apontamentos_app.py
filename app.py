import pandas as pd
import streamlit as st

# Configuração da página para ocupar a largura total
st.set_page_config(
    page_title="Gerenciador de Apontamentos", page_icon="📊", layout="wide"
)

st.title("📊 Painel de Apontamentos e Indicadores")

# ==========================================
# UPLOAD E CARREGAMENTO DO ARQUIVO EXCEL
# ==========================================
uploaded_file = st.sidebar.file_uploader(
    "Carregar Planilha Excel (.xlsx)", type=["xlsx"]
)

if uploaded_file is not None:
  # Lendo as abas disponíveis no arquivo para garantir que pegamos a aba certa
  excel_file = pd.ExcelFile(uploaded_file)
  abas_disponiveis = excel_file.sheet_names

  # Seleção da aba (com foco padrão na aba 'Apontamentos' ou 'Apontamentos_Detalhado')
  aba_selecionada = st.sidebar.selectbox(
      "Selecione a Aba",
      options=abas_disponiveis,
      index=(
          abas_disponiveis.index("Apontamentos")
          if "Apontamentos" in abas_disponiveis
          else 0
      ),
  )


  @st.cache_data
  def carregar_dados_excel(file, sheet_name):
    return pd.read_excel(file, sheet_name=sheet_name)


  df = carregar_dados_excel(uploaded_file, aba_selecionada)

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
  filtro_ct = st.sidebar.multiselect("Centro de Trabalho (CT)", options=ct_ct_disponiveis)

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
      f"📋 Dados da Aba: `{aba_selecionada}` (Registros exibidos:"
      f" {len(df_filtrado)} de {len(df)})"
  )

  st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

else:
  st.info(
      "📂 Por favor, faça o upload da planilha Excel na barra lateral para"
      " carregar os dados da aba de apontamentos."
  )
