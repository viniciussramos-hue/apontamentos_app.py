import streamlit as st
import pandas as pd
from datetime import datetime, time
import sqlite3
import google.generativeai as genai

# Configuração da IA (substitua pela sua chave)
genai.configure(api_key="SUA_CHAVE_API_AQUI")
model = genai.GenerativeModel("gemini-2.5-flash")

# Conexão com o banco de dados
conn = sqlite3.connect("apontamentos.db")
c = conn.cursor()

c.execute("""
    CREATE TABLE IF NOT EXISTS apontamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT,
        hora_inicio TEXT,
        hora_fim TEXT,
        duracao_esperada REAL,
        eficiencia REAL
    )
""")
conn.commit()

st.title("Calculadora de Eficiência com IA")

# Opção de tirar a foto
foto = st.camera_input("Tire uma foto do seu apontamento")

if foto is not None:
    # Envia a imagem para a IA analisar
    with st.spinner("Analisando imagem com IA..."):
        resposta = model.generate_content([
            "Analise esta imagem de um apontamento e extraia: a hora de início, "
            "a hora de término e identifique se é o código zero (código de produção). "
            "Retorne o resultado de forma que eu possa identificar cada campo.",
            foto
        ])
        
    st.write("Resposta da IA:")
    st.write(resposta.text)

# Formulário para registro manual
with st.form("form_apontamento_eficiencia", clear_on_submit=True):
    codigo_item = st.text_input("Código do Apontamento:")
    
    col1, col2 = st.columns(2)
    with col1:
        inicio = st.time_input("Hora de Início:", value=time(8, 0))
    with col2:
        fim = st.time_input("Hora de Término:", value=time(9, 0))
        
    duracao_padrao = st.number_input("Duração Esperada (em minutos):", min_value=1.0, step=5.0)

    btn_calcular = st.form_submit_button("Registrar e Calcular Eficiência")

    if btn_calcular:
        inicio_min = inicio.hour * 60 + inicio.minute
        fim_min = fim.hour * 60 + fim.minute
        duracao_real = fim_min - inicio_min
        
        if duracao_real > 0:
            eficiencia = (duracao_padrao / duracao_real) * 100
            
            c.execute("""
                INSERT INTO apontamentos (codigo, hora_inicio, hora_fim, duracao_esperada, eficiencia) 
                VALUES (?, ?, ?, ?, ?)
            """, (codigo_item, str(inicio), str(fim), duracao_padrao, eficiencia))
            conn.commit()
            
            st.success(f"Eficiência calculada: {eficiencia:.2f}%")
        else:
            st.error("A hora de término deve ser posterior à hora de início.")

st.subheader("Histórico de Apontamentos")
dados = pd.read_sql("SELECT * FROM apontamentos", conn)
st.dataframe(dados)
