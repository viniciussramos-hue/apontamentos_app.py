import pandas as pd
import streamlit as st

# Configuração da página para ocupar a largura total
st.set_page_config(
    page_title="Apontamentos Detalhados", page_icon="📊", layout="wide"
)

st.title("📊 Painel de Apontamentos Detalhados")


# Função fictícia para carregar os dados (substitua pelo seu carregamento real, ex: pd.read_excel ou conexão com banco)
@st.cache_data
def carregar_dados():
  # Exemplo de estrutura compatível com as colunas da imagem
  data = {
      "CT": ["PM02", "PM02", "PM02", "PM02"],
      "CT Item": ["PM02", "PM02", "PM02", "PM02"],
      "Data": pd.to_datetime(["2026-08-01", "2026-08-01", "2026-08-01", "2026-08-01"]),
      "Hora Início": ["05:10:00", "05:10:00", "05:15:00", "05:30:00"],
      "Hora Fim": ["05:30:00", "06:00:00", "05:45:00", "05:50:00"],
      "Duração": ["00:20:00", "00:50:00", "00:35:00", "00:20:00"],
      "Máq.": ["C2076", "C2079", "C2077", "C2076"],
      "T": [11, 11, 11, 11],
      "S/N": ["S", "N", "N", "N"],
      "Grupo": [
          "ATIVIDADES INTERATIVAS",
          "DIVERSOS",
          "DIVERSOS",
          "ATIVIDADES INTERATIVAS",
      ],
      "Descrição": ["PPRPS", "DESLOCAMENTO MOD", "SEGURANÇA", "PPRPS"],
      "Material": ["", "5087337463BLK", "30048290300", ""],
      "Descrição do PN": [
          "",
          "CONTRA REF LG DIANT INT LE GM ASW93003",
          "SUPORTE PM MAN 2T2701149D-2",
          "",
      ],
      "Conjugado": ["(vazio)", "(vazio)", "(vazio)", "(vazio)"],
      "Qtd.": [0, 0, 0, 0],
      "Std PN": [547, 859, 203, 547],
      "Tempo_Std.": ["0:00:00", "0:00:00", "0:00:00", "0:00:00"],
      "QtPrevista.": [182, 716, 118, 182],
      "Nº Operadores.": [3, 3, 2, 3],
      "Eficiência": ["", "", "", ""],
  }
  return pd.DataFrame(data)


df = carregar_dados()

# ==========================================
# BARRA LATERAL DE FILTROS
# ==========================================
st.sidebar.header("🔍 Filtros")

# 1. Filtro de Datas
if "Data" in df.columns and not df["Data"].empty:
  min_date = df["Data"].min().date()
  max_date = df["Data"].max().date()
  filtro_data = st.sidebar.date_input(
      "Período (Data)", value=(min_date, max_date), format="DD/MM/YYYY"
  )
else:
  filtro_data = None

# 2. Filtro de Máquinas
maquinas_disponiveis = (
    df["Máq."].dropna().unique().tolist() if "Máq." in df.columns else []
)
filtro_maq = st.sidebar.multiselect("Máquinas", options=maquinas_disponiveis)

# 3. Filtro de Turno (T)
turnos_disponiveis = df["T"].dropna().unique().tolist() if "T" in df.columns else []
filtro_turno = st.sidebar.multiselect("Turno (T)", options=turnos_disponiveis)

# 4. Filtro de Centro de Trabalho (CT)
ct_disponiveis = df["CT"].dropna().unique().tolist() if "CT" in df.columns else []
filtro_ct = st.sidebar.multiselect("Centro de Trabalho (CT)", options=ct_disponiveis)

# 5. Filtro de Descrição CT (Mapeado aqui para a coluna 'Descrição' ou equivalente do CT)
desc_ct_disponiveis = (
    df["Descrição"].dropna().unique().tolist()
    if "Descrição" in df.columns
    else []
)
filtro_desc_ct = st.sidebar.multiselect(
    "Descrição CT / Atividade", options=desc_ct_disponiveis
)

# 6. Filtro de Grupo
grupo_disponiveis = (
    df["Grupo"].dropna().unique().tolist() if "Grupo" in df.columns else []
)
filtro_grupo = st.sidebar.multiselect("Grupo", options=grupo_disponiveis)

# ==========================================
# APLICAÇÃO DOS FILTROS NO DATAFRAME
# ==========================================
df_filtrado = df.copy()

if filtro_data and len(filtro_data) == 2:
  start_date, end_date = filtro_data
  df_filtrado = df_filtrado[
      (df_filtrado["Data"].dt.date >= start_date)
      & (df_filtrado["Data"].dt.date <= end_date)
  ]

if filtro_maq:
  df_filtrado = df_filtrado[df_filtrado["Máq."].isin(filtro_maq)]

if filtro_turno:
  df_filtrado = df_filtrado[df_filtrado["T"].isin(filtro_turno)]

if filtro_ct:
  df_filtrado = df_filtrado[df_filtrado["CT"].isin(filtro_ct)]

if filtro_desc_ct:
  df_filtrado = df_filtrado[df_filtrado["Descrição"].isin(filtro_desc_ct)]

if filtro_grupo:
  df_filtrado = df_filtrado[df_filtrado["Grupo"].isin(filtro_grupo)]

# ==========================================
# EXIBIÇÃO DA TABELA NA TELA PRINCIPAL
# ==========================================
st.subheader(
    f"📋 Apontamentos Detalhados (Registros encontrados:"
    f" {len(df_filtrado)})"
)

# Exibição interativa com ajuste dinâmico de largura nas colunas
st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
