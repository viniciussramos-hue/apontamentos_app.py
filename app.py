import streamlit as st
import pandas as pd
import google.generativeai as genai

# ==================================
# CONFIGURAÇÃO DA IA (GEMINI)
# ==================================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-3.5-flash")
except Exception as e:
    model = None

# ==================================
# PÁGINA
# ==================================

st.set_page_config(
    page_title="Sistema de Apontamentos & IA",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Sistema de Gestão de Apontamentos & Inteligência Artificial")

# Criando as abas principais
aba1, aba2 = st.tabs(["📊 Painel de Apontamentos", "🤖 Interação com a I.A."])

# Nome do arquivo automático no repositório
NOME_ARQUIVO = "03-Consultas_Apontamentos_rev02.xlsb"

# Carrega os dados na sessão
if "df_apontamentos" not in st.session_state:
    st.session_state.df_apontamentos = pd.DataFrame()

if st.session_state.df_apontamentos.empty:
    try:
        with st.spinner("Carregando base de dados do repositório..."):
            st.session_state.df_apontamentos = pd.read_excel(NOME_ARQUIVO, engine="pyxlsb")
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo automático '{NOME_ARQUIVO}': {e}")

df_global = st.session_state.df_apontamentos

# ==================================
# ABA 1: PAINEL DE APONTAMENTOS (Com Filtros Lado Esquerdo)
# ==================================
with aba1:
    if not df_global.empty:
        # Layout dividido em colunas (Esquerda: Filtros tipo Excel / Direita: Tabela de Dados)
        col_filtros, col_tabela = st.columns([1, 4])
        
        with col_filtros:
            st.markdown("### 🎛️ Filtros")
            st.markdown("---")
            
            # Filtro por Máquina (se a coluna existir)
            col_maq = next((c for c in df_global.columns if 'máq' in c.lower() or 'maq' in c.lower() or 'c7' in str(df_global[c].values).lower()), None)
            maquinas_selecionadas = []
            if col_maq:
                lista_maquinas = sorted(df_global[col_maq].dropna().unique().astype(str))
                maquinas_selecionadas = st.multiselect("Máquina", lista_maquinas)

            # Filtro por Turno (se a coluna existir)
            col_turno = next((c for c in df_global.columns if 't' == c.lower() or 'turno' in c.lower()), None)
            turnos_selecionados = []
            if col_turno:
                lista_turnos = sorted(df_global[col_turno].dropna().unique().astype(str))
                turnos_selecionados = st.multiselect("Turno", lista_turnos)

            # Filtro por Centro de Trabalho / CT (se a coluna existir)
            col_ct = next((c for c in df_global.columns if c.upper() == 'CT' or 'centro' in c.lower()), None)
            cts_selecionados = []
            if col_ct:
                lista_cts = sorted(df_global[col_ct].dropna().unique().astype(str))
                cts_selecionados = st.multiselect("Centro de Trabalho (CT)", lista_cts)
                
            st.markdown("---")
            if st.button("🔄 Limpar Filtros"):
                st.rerun()

        with col_tabela:
            # Aplicação dos filtros dinâmicos
            df_filtrado = df_global.copy()
            if maquinas_selecionadas and col_maq:
                df_filtrado = df_filtrado[df_filtrado[col_maq].astype(str).isin(maquinas_selecionadas)]
            if turnos_selecionados and col_turno:
                df_filtrado = df_filtrado[df_filtrado[col_turno].astype(str).isin(turnos_selecionados)]
            if cts_selecionados and col_ct:
                df_filtrado = df_filtrado[df_filtrado[col_ct].astype(str).isin(cts_selecionados)]

            # Cabeçalho de Métricas do topo
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Registros Exibidos", len(df_filtrado))
            with m2:
                col_ef = next((c for c in df_global.columns if 'eficiência' in c.lower() or 'eficiencia' in c.lower()), None)
                if col_ef:
                    eff_media = pd.to_numeric(df_filtrado[col_ef], errors='coerce').mean()
                    st.metric("Eficiência Média", f"{eff_media:.2f}%")
            with m3:
                col_hr = next((c for c in df_global.columns if 'horas' in c.lower() or 'duração' in c.lower()), None)
                st.metric("Status da Base", "Sincronizado ✅")

            st.markdown("---")
            # Exibe a tabela principal com layout limpo e interativo
            st.dataframe(df_filtrado, use_container_width=True, height=600)
    else:
        st.info("Aguardando carregamento da planilha do repositório...")

# ==================================
# ABA 2: INTERAÇÃO COM A I.A.
# ==================================
with aba2:
    st.subheader("🤖 Chat Interativo com a I.A.")
    st.write("Converse com o assistente inteligente para analisar os dados filtrados ou extrair insights operacionais.")

    if "mensagens_chat" not in st.session_state:
        st.session_state.mensagens_chat = []

    for mensagem in st.session_state.mensagens_chat:
        with st.chat_message(mensagem["role"]):
            st.markdown(mensagem["content"])

    pergunta_usuario = st.chat_input("Ex: Qual máquina teve menor eficiência nesta seleção?")

    if pergunta_usuario:
        st.session_state.mensagens_chat.append({"role": "user", "content":pergunta_usuario})
        with st.chat_message("user"):
            st.markdown(pergunta_usuario)

        if model is not None:
            with st.chat_message("assistant"):
                with st.spinner("Analisando dados com a IA..."):
                    try:
                        # Pega uma amostra dos dados atuais para alimentar a IA com contexto preciso
                        contexto_dados = df_global.head(150).to_string() if not df_global.empty else "Sem dados."
                        
                        prompt_chat = (
                            f"Você é um assistente especialista em manufatura industrial, chapas de chassis de ônibus/caminhões e relatórios PM/OTS. "
                            f"Aqui estão os dados recentes da planilha de apontamentos:\n{contexto_dados}\n\n"
                            f"Responda à pergunta do usuário de forma técnica, clara e direta: {pergunta_usuario}"
                        )
                        
                        resposta_chat = model.generate_content(prompt_chat)
                        texto_resposta = resposta_chat.text
                        
                        st.markdown(texto_resposta)
                        st.session_state.mensagens_chat.append({"role": "assistant", "content": texto_resposta})
                    except Exception as e:
                        erro_msg = f"Erro na IA: {e}"
                        st.error(erro_msg)
                        st.session_state.mensagens_chat.append({"role": "assistant", "content": erro_msg})
        else:
            st.warning("⚠️ Chave de API do Gemini não configurada.")
