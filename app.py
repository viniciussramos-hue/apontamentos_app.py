import streamlit as st
import pandas as pd
import google.generativeai as genai
import json

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
st.write("Acompanhe os apontamentos carregados da sua planilha e interaja com a IA na aba dedicada.")

# Criando as abas conforme solicitado
aba1, aba2 = st.tabs(["📊 Apontamentos (Planilha Excel)", "🤖 Interação com a I.A."])

# ==================================
# ABA 1: APONTAMENTOS / PLANILHA EXCEL
# ==================================
with aba1:
    st.subheader("📁 Carregar Planilha de Apontamentos")
    st.write("Faça o upload do seu arquivo Excel (`.xlsx` ou `.xls`) contendo os dados detalhados de produção, horários, máquinas e eficiência.")
    
    arquivo_excel = st.file_uploader("Escolha o arquivo Excel", type=["xlsx", "xls"])
    
    # Armazena os dados no session_state para a IA conseguir ler na outra aba
    if "df_apontamentos" not in st.session_state:
        st.session_state.df_apontamentos = pd.DataFrame()

    if arquivo_excel is not None:
        try:
            # Lê a planilha do Excel enviada
            df_excel = pd.read_excel(arquivo_excel)
            st.session_state.df_apontamentos = df_excel
            
            st.success("✅ Planilha carregada com sucesso!")
            
            # Filtros rápidos ou visualização idêntica ao layout da imagem
            st.markdown("---")
            st.subheader("📋 Dados Carregados do Apontamento")
            
            # Exibe métricas rápidas no topo se houver colunas comuns
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Registros", len(df_excel))
            with col2:
                if 'Eficiência' in df_excel.columns:
                    st.metric("Eficiência Média", f"{pd.to_numeric(df_excel['Eficiência'], errors='coerce').mean():.2f}%")
                elif 'eficiencia' in df_excel.columns:
                    st.metric("Eficiência Média", f"{pd.to_numeric(df_excel['eficiencia'], errors='coerce').mean():.2f}%")
            
            # Exibe a tabela completa com o layout da planilha
            st.dataframe(df_excel, use_container_width=True)
            
        except Exception as e:
            st.error(f"Erro ao ler o arquivo Excel: {e}")
    else:
        if not st.session_state.df_apontamentos.empty:
            st.dataframe(st.session_state.df_apontamentos, use_container_width=True)
        else:
            st.info("ℹ️ Nenhuma planilha carregada no momento. Faça o upload acima para visualizar os dados.")

# ==================================
# ABA 2: INTERAÇÃO COM A I.A.
# ==================================
with aba2:
    st.subheader("🤖 Chat Interativo com a I.A.")
    st.write("Aqui você pode conversar diretamente com o assistente inteligente para analisar os dados carregados na planilha, verificar desvios de eficiência, paradas ou estatísticas.")

    # Inicializa o histórico de chat na sessão do Streamlit
    if "mensagens_chat" not in st.session_state:
        st.session_state.mensagens_chat = []

    # Exibe as mensagens anteriores do chat
    for mensagem in st.session_state.mensagens_chat:
        with st.chat_message(mensagem["role"]):
            st.markdown(mensagem["content"])

    # Caixa de entrada de texto do chat
    pergunta_usuario = st.chat_input("Ex: Quais foram os principais motivos de parada registrados na planilha?")

    if pergunta_usuario:
        st.session_state.mensagens_chat.append({"role": "user", "content": pergunta_usuario})
        with st.chat_message("user"):
            st.markdown(pergunta_usuario)

        if model is not None:
            with st.chat_message("assistant"):
                with st.spinner("Analisando dados da planilha..."):
                    try:
                        df_atual = st.session_state.df_apontamentos
                        dados_contexto = df_atual.to_string() if not df_atual.empty else "Nenhuma planilha foi carregada ainda pelo usuário."
                        
                        prompt_chat = (
                            f"Você é um assistente especialista em análise de processos industriais, linhas de produção e relatórios PM/OTS. "
                            f"Aqui estão os dados da planilha de apontamentos enviada pelo usuário:\n{dados_contexto}\n\n"
                            f"Responda à pergunta do usuário de forma clara, técnica e objetiva: {pergunta_usuario}"
                        )
                        
                        resposta_chat = model.generate_content(prompt_chat)
                        texto_resposta_chat = resposta_chat.text
                        
                        st.markdown(texto_resposta_chat)
                        st.session_state.mensagens_chat.append({"role": "assistant", "content": texto_resposta_chat})
                    except Exception as e:
                        erro_msg = f"Erro ao processar a resposta com a IA: {e}"
                        st.error(erro_msg)
                        st.session_state.mensagens_chat.append({"role": "assistant", "content": erro_msg})
        else:
            st.warning("⚠️ Chave de API do Gemini não configurada corretamente.")
