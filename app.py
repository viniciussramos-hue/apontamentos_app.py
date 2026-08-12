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
st.write("Leitura automática do arquivo de consultas do repositório.")

# Criando as abas
aba1, aba2 = st.tabs(["📊 Apontamentos (Arquivo Automático)", "🤖 Interação com a I.A."])

# ==================================
# ABA 1: LEITURA AUTOMÁTICA DO .XLSB
# ==================================
with aba1:
    st.subheader("📁 Dados Carregados Automaticamente do Repositório")
    
    # Nome do arquivo que está na mesma pasta no GitHub
    nome_arquivo = "03-Consultas_Apontamentos_rev02.xlsb"

    if "df_apontamentos" not in st.session_state:
        st.session_state.df_apontamentos = pd.DataFrame()

    try:
        # Lê o arquivo automaticamente usando pyxlsb
        if st.session_state.df_apontamentos.empty:
            with st.spinner("Lendo arquivo do repositório..."):
                # Se houver abas específicas, você pode passar sheet_name="NomeDaAba"
                df_auto = pd.read_excel(nome_arquivo, engine="pyxlsb")
                st.session_state.df_apontamentos = df_auto
        
        df_excel = st.session_state.df_apontamentos
        
        st.success("✅ Arquivo carregado com sucesso do repositório!")
        
        # Métricas rápidas
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de Registros", len(df_excel))
        with col2:
            if 'Eficiência' in df_excel.columns:
                st.metric("Eficiência Média", f"{pd.to_numeric(df_excel['Eficiência'], errors='coerce').mean():.2f}%")
            elif 'eficiencia' in df_excel.columns:
                st.metric("Eficiência Média", f"{pd.to_numeric(df_excel['eficiencia'], errors='coerce').mean():.2f}%")
        
        # Exibe a tabela completa
        st.dataframe(df_excel, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro ao ler o arquivo automático '{nome_arquivo}': {e}")
        st.info("Dica: Certifique-se de que a biblioteca 'pyxlsb' está adicionada no seu arquivo requirements.txt.")

# ==================================
# ABA 2: INTERAÇÃO COM A I.A.
# ==================================
with aba2:
    st.subheader("🤖 Chat Interativo com a I.A.")
    st.write("Converse com o assistente inteligente para analisar os dados carregados do arquivo automático.")

    if "mensagens_chat" not in st.session_state:
        st.session_state.mensagens_chat = []

    for mensagem in st.session_state.mensagens_chat:
        with st.chat_message(mensagem["role"]):
            st.markdown(mensagem["content"])

    pergunta_usuario = st.chat_input("Ex: Qual máquina apresentou maior eficiência na planilha?")

    if pergunta_usuario:
        st.session_state.mensagens_chat.append({"role": "user", "content": pergunta_usuario})
        with st.chat_message("user"):
            st.markdown(pergunta_usuario)

        if model is not None:
            with st.chat_message("assistant"):
                with st.spinner("Analisando dados..."):
                    try:
                        df_atual = st.session_state.df_apontamentos
                        dados_contexto = df_atual.head(100).to_string() if not df_atual.empty else "Nenhum dado carregado."
                        
                        prompt_chat = (
                            f"Você é um assistente especialista em análise de processos industriais, linhas de produção e relatórios PM/OTS. "
                            f"Aqui estão os dados da planilha de apontamentos:\n{dados_contexto}\n\n"
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
            st.warning("⚠️ Chave de API do Gemini não configurada.")
