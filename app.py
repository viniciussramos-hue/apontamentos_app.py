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
    # Nome oficial atualizado suportado pelas novas versões da API
    model = genai.GenerativeModel("gemini-flash")
except Exception as e:
    model = None

# ==================================
# BANCO DE DADOS
# ==================================

@st.cache_resource
def conectar_banco():
    conn = sqlite3.connect(
        "apontamentos.db",
        check_same_thread=False
    )

    conn.execute("""
    CREATE TABLE IF NOT EXISTS apontamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT,
        hora_inicio TEXT,
        hora_fim TEXT,
        duracao_esperada REAL,
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
    page_title="Leitor de Apontamento por IA",
    page_icon="📷",
    layout="wide"
)

st.title("📷 Leitor Automático de Apontamento & Eficiência")
st.write("Tire uma foto ou faça o upload da imagem da folha de apontamento. A IA fará a leitura, identificará o código (0 para produção) e calculará a eficiência automaticamente.")

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
        if st.button("🚀 Processar e Salvar Apontamento com IA", use_container_width=True):
            with st.spinner("Analisando imagem e calculando eficiência..."):
                try:
                    prompt = (
                        "Analise esta imagem de um Relatório de Auto Apontamento. "
                        "Identifique as informações da linha principal preenchida. "
                        "Procure pela coluna 'Código' (Atv / Cód Paradas) — lembre-se que o código '0' significa produção, "
                        "extraia o Código, a 'Hora de Início' (HH:MM) e a 'Hora de Fim' (HH:MM). "
                        "Estime também ou defina uma duracao_esperada padrão em minutos (ex: 60). "
                        "Retorne a resposta EXATAMENTE em formato JSON puro, contendo as chaves: "
                        "codigo, hora_inicio, hora_fim, duracao_esperada."
                    )
                    
                    resposta = model.generate_content([prompt, imagem_pil])
                    texto_resposta = resposta.text.strip()
                    
                    if "{" in texto_resposta and "}" in texto_resposta:
                        inicio_json = texto_resposta.find("{")
                        fim_json = texto_resposta.rfind("}") + 1
                        texto_resposta = texto_resposta[inicio_json:fim_json]

                    dados_ia = json.loads(texto_resposta)
                    
                    codigo = str(dados_ia.get("codigo", "0"))
                    h_ini_str = dados_ia.get("hora_inicio", "08:00")
                    h_fim_str = dados_ia.get("hora_fim", "09:00")
                    duracao_esperada = float(dados_ia.get("duracao_esperada", 60.0))
                    
                    partes_ini = h_ini_str.split(":")
                    partes_fim = h_fim_str.split(":")
                    
                    inicio_min = int(partes_ini[0]) * 60 + int(partes_ini[1])
                    fim_min = int(partes_fim[0]) * 60 + int(partes_fim[1])

                    if fim_min <= inicio_min:
                        fim_min += 1440

                    duracao_real = fim_min - inicio_min
                    
                    if duracao_real > 0:
                        eficiencia = (duracao_esperada / duracao_real) * 100
                        
                        conn.execute(
                            """
                            INSERT INTO apontamentos
                            (codigo, hora_inicio, hora_fim, duracao_esperada, duracao_real, eficiencia)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (codigo, h_ini_str, h_fim_str, duracao_esperada, duracao_real, eficiencia)
                        )
                        conn.commit()
                        
                        st.success(f"✅ Apontamento salvo com sucesso! Código: {codigo} | Início: {h_ini_str} | Fim: {h_fim_str} | Eficiência: {eficiencia:.2f}%")
                        st.rerun()
                    else:
                        st.error("A hora de término calculada é anterior ou igual à de início. Verifique a imagem.")

                except Exception as e:
                    st.error(f"Erro ao processar a imagem com a IA: {e}")
    else:
        st.warning("⚠️ Chave de API do Gemini não configurada corretamente nos Secrets do Streamlit.")

# ==================================
# HISTÓRICO & EXCLUSÃO
# ==================================

st.markdown("---")
st.subheader("📋 Histórico de Apontamentos Realizados")

df = pd.read_sql_query(
    "SELECT * FROM apontamentos ORDER BY id DESC",
    conn
)

st.dataframe(
    df,
    use_container_width=True
)

if not df.empty:
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Total de Registros",
            len(df)
        )

    with col2:
        st.metric(
            "Eficiência Média",
            f"{df['eficiencia'].mean():.2f}%"
        )

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
