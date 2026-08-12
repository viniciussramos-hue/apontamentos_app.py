import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
from PIL import Image
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
# BANCO DE DADOS (ESTRUTURA ORIGINAL PM/OTS)
# ==================================

@st.cache_resource
def conectar_banco():
    conn = sqlite3.connect(
        "apontamentos_pm_ots.db",
        check_same_thread=False
    )

    conn.execute("""
    CREATE TABLE IF NOT EXISTS apontamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        op TEXT,
        qtd_op TEXT,
        codigo_desenho TEXT,
        codigo_maxion TEXT,
        operacao TEXT,
        codigo_paradas TEXT,
        hora_inicio TEXT,
        hora_fim TEXT,
        n_bat TEXT,
        pcs_boas TEXT,
        sucata TEXT,
        n_etiqueta TEXT,
        motivo TEXT,
        duracao_real REAL,
        eficiencia REAL
    )
    """)

    conn.commit()
    return conn

conn = conectar_banco()

# ==================================
# PÁGINA
# ==================================

st.set_page_config(
    page_title="Leitor PM/OTS - Apontamento & IA",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Leitor Automático - Relatório de Auto Apontamento (PM/OTS)")
st.write("Envie a foto ou arquivo do relatório. A IA fará a leitura exata de todos os campos do formulário original.")

# ==================================
# ESCOLHA: CÂMERA OU UPLOAD DE ARQUIVO
# ==================================

modo_entrada = st.radio("Escolha o método para enviar a imagem:", ["📸 Tirar Foto (Câmera)", "📁 Enviar Arquivo de Imagem"])

imagem_pil = None

if modo_entrada == "📸 Tirar Foto (Câmera)":
    foto = st.camera_input("Tire uma foto clara da folha de apontamento")
    if foto is not None:
        imagem_pil = Image.open(foto)
else:
    arquivo_up = st.file_uploader("Escolha a imagem do apontamento", type=["jpg", "jpeg", "png"])
    if arquivo_up is not None:
        imagem_pil = Image.open(arquivo_up)

# Se houver uma imagem
if imagem_pil is not None:
    st.image(imagem_pil, caption="Imagem selecionada", use_container_width=True)

    if model is not None:
        if st.button("🚀 Processar e Salvar Linhas do Apontamento com IA", use_container_width=True):
            with st.spinner("Lendo a folha de apontamento PM/OTS..."):
                try:
                    prompt = (
                        "Analise esta imagem do 'Relatório de Auto Apontamento - PM/OTS'. "
                        "Extraia todas as linhas preenchidas do relatório. "
                        "Para cada linha, extraia os seguintes campos: "
                        "\"op\", \"qtd_op\", \"codigo_desenho\", \"codigo_maxion\", \"operacao\", "
                        "\"codigo_paradas\", \"hora_inicio\", \"hora_fim\", \"n_bat\", \"pcs_boas\", "
                        "\"sucata\", \"n_etiqueta\", \"motivo\". "
                        "Retorne a resposta EXATAMENTE em formato JSON puro contendo uma lista de objetos chamada 'apontamentos' (ex: {\"apontamentos\": [...]}). "
                        "Se algum campo estiver vazio na imagem, retorne string vazia \"\"."
                    )
                    
                    resposta = model.generate_content([prompt, imagem_pil])
                    texto_resposta = resposta.text.strip()
                    
                    if "{" in texto_resposta and "}" in texto_resposta:
                        inicio_json = texto_resposta.find("{")
                        fim_json = texto_resposta.rfind("}") + 1
                        texto_resposta = texto_resposta[inicio_json:fim_json]

                    dados_ia = json.loads(texto_resposta)
                    lista_linhas = dados_ia.get("apontamentos", [])
                    
                    if lista_linhas:
                        salvos = 0
                        for item in lista_linhas:
                            op = str(item.get("op", ""))
                            if not op: # Ignora linhas vazias
                                continue
                                
                            qtd_op = str(item.get("qtd_op", ""))
                            codigo_desenho = str(item.get("codigo_desenho", ""))
                            codigo_maxion = str(item.get("codigo_maxion", ""))
                            operacao = str(item.get("operacao", ""))
                            codigo_paradas = str(item.get("codigo_paradas", "0"))
                            h_ini_str = str(item.get("hora_inicio", "00:00"))
                            h_fim_str = str(item.get("hora_fim", "00:00"))
                            n_bat = str(item.get("n_bat", ""))
                            pcs_boas = str(item.get("pcs_boas", ""))
                            sucata = str(item.get("sucata", ""))
                            n_etiqueta = str(item.get("n_etiqueta", ""))
                            motivo = str(item.get("motivo", ""))
                            
                            # Cálculo de duração real se houver horários válidos
                            duracao_real = 0.0
                            eficiencia = 0.0
                            try:
                                partes_ini = h_ini_str.split(":")
                                partes_fim = h_fim_str.split(":")
                                inicio_min = int(partes_ini[0]) * 60 + int(partes_ini[1])
                                fim_min = int(partes_fim[0]) * 60 + int(partes_fim[1])
                                if fim_min <= inicio_min:
                                    fim_min += 1440
                                duracao_real = float(fim_min - inicio_min)
                                
                                # Estimativa baseada em padrão de 60 min se necessário
                                duracao_esperada = 60.0
                                if duracao_real > 0:
                                    eficiencia = (duracao_esperada / duracao_real) * 100
                            except:
                                pass

                            conn.execute(
                                """
                                INSERT INTO apontamentos
                                (op, qtd_op, codigo_desenho, codigo_maxion, operacao, codigo_paradas, 
                                hora_inicio, hora_fim, n_bat, pcs_boas, sucata, n_etiqueta, motivo, duracao_real, eficiencia)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (op, qtd_op, codigo_desenho, codigo_maxion, operacao, codigo_paradas, 
                                h_ini_str, h_fim_str, n_bat, pcs_boas, sucata, n_etiqueta, motivo, duracao_real, eficiencia)
                            )
                            salvos += 1
                            
                        conn.commit()
                        st.success(f"✅ {salvos} linha(s) de apontamento extraídas e salvas com sucesso!")
                        st.rerun()
                    else:
                        st.warning("A IA não encontrou linhas preenchidas na imagem.")

                except Exception as e:
                    st.error(f"Erro ao processar a imagem com a IA: {e}")
    else:
        st.warning("⚠️ Chave de API do Gemini não configurada corretamente nos Secrets do Streamlit.")

# ==================================
# HISTÓRICO & EXCLUSÃO
# ==================================

st.markdown("---")
st.subheader("📋 Histórico de Apontamentos (PM/OTS)")

df = pd.read_sql_query(
    "SELECT * FROM apontamentos ORDER BY id DESC",
    conn
)

st.dataframe(
    df,
    use_container_width=True
)

if not df.empty:
    col_met1, col_met2 = st.columns(2)
    with col_met1:
        st.metric("Total de Registros", len(df))
    with col_met2:
        valid_eff = df[df['eficiencia'] > 0]['eficiencia']
        if not valid_eff.empty:
            st.metric("Eficiência Média", f"{valid_eff.mean():.2f}%")

    st.markdown("---")
    st.subheader("🗑️ Gerenciar Registros")
    
    col_del1, col_del2 = st.columns([2, 1])
    
    with col_del1:
        id_para_excluir = st.selectbox("Selecione o ID do apontamento para excluir:", df["id"].tolist())
    
    with col_del2:
        st.write("") 
        st.write("")
        if st.button("🗑️ Deletar Registro Selecionado", use_container_width=True):
            conn.execute("DELETE FROM apontamentos WHERE id = ?", (id_para_excluir,))
            conn.commit()
            st.success(f"Registro ID {id_para_excluir} excluído com sucesso!")
            st.rerun()

# ==================================
# BOTÃO / CHAT DE INTERAÇÃO COM A I.A.
# ==================================

st.markdown("---")
st.subheader("🤖 Chat Interativo com a I.A. sobre os Apontamentos")
st.write("Tire dúvidas, peça análises de produção ou pergunte sobre os registros salvos no banco de dados.")

# Inicializa o histórico de chat na sessão do Streamlit
if "mensagens_chat" not in st.session_state:
    st.session_state.mensagens_chat = []

# Exibe as mensagens anteriores do chat
for mensagem in st.session_state.mensagens_chat:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

# Caixa de entrada de texto do chat
pergunta_usuario = st.chat_input("Ex: Qual foi a operação com maior quantidade de peças boas?")

if pergunta_usuario:
    # Adiciona a mensagem do usuário ao histórico
    st.session_state.mensagens_chat.append({"role": "user", "content": pergunta_usuario})
    with st.chat_message("user"):
        st.markdown(pergunta_usuario)

    if model is not None:
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                try:
                    # Converte os dados atuais do banco em formato texto para a IA consultar
                
                    dados_contexto = df.to_string() if not df.empty else "Nenhum registro no banco ainda."
                    
                    prompt_chat = (
                        f"Você é um assistente especialista em produção industrial e análise de relatórios PM/OTS. "
                        f"Aqui estão os dados atuais salvos no banco de dados do sistema:\n{dados_contexto}\n\n"
                        f"Responda à seguinte pergunta do usuário de forma clara, prestativa e objetiva: {pergunta_usuario}"
                    )
                    
                    resposta_chat = model.generate_content(prompt_chat)
                    texto_resposta_chat = resposta_chat.text
                    
                    st.markdown(texto_resposta_chat)
                    st.session_state.mensagens_chat.append({"role": "assistant", "content": texto_resposta_chat})
                except Exception as e:
                    erro_msg = f"Erro ao consultar a IA: {e}"
                    st.error(erro_msg)
                    st.session_state.mensagens_chat.append({"role": "assistant", "content": erro_msg})
    else:
        st.warning("⚠️ IA não configurada.")
