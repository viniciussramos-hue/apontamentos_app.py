from datetime import date, datetime
import pandas as pd
import streamlit as st
import sqlite3
import openai
import base64
import json

# --- CONFIGURACAO DA PAGINA ---
st.set_page_config(
    page_title="Gestao de Apontamentos PM/OTS",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONEXAO COM O BANCO DE DADOS ---
conn = sqlite3.connect("apontamentos_fabrica.db", check_same_thread=False)
c = conn.cursor()

# Criacao das tabelas essenciais com todos os campos de volume e horas
c.execute("""
    CREATE TABLE IF NOT EXISTS paradas_mestre (
        codigo INTEGER PRIMARY KEY,
        descricao TEXT,
        categoria TEXT
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS apontamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        turno TEXT,
        maquina TEXT,
        data_apontamento TEXT,
        responsavel TEXT,
        op TEXT,
        qtd_op REAL,
        codigo_desenho TEXT,
        codigo_maxion TEXT,
        operacao TEXT,
        codigo_parada INTEGER,
        hora_inicio TEXT,
        hora_fim TEXT,
        num_batidas REAL,
        pcas_boas REAL,
        sucata REAL,
        num_etiqueta TEXT,
        motivo TEXT
    )
""")
conn.commit()

# --- CARREGA DADOS MESTRES DE PARADA ---
def popular_paradas_iniciais():
    count = c.execute("SELECT COUNT(*) FROM paradas_mestre").fetchone()[0]
    if count == 0:
        dados_iniciais = [
            (7011, "Limpeza - (Sucatas, Batoques, Plasticos e Oleo)", "Processos"),
            (7016, "Inspecao por frequencia", "Processos"),
            (7091, "Lixando Pcs", "Processos"),
            (7182, "Falta Operacao Anterior", "Processos"),
            (7183, "Falta Operacao Posterior", "Processos"),
            (4002, "Quebra/Desg Punsao", "Ferramentaria"),
            (4003, "Quebra/Desg Matriz", "Ferramentaria"),
            (4010, "Limpeza de Batoque", "Ferramentaria"),
            (5001, "Falta AR Comprimido", "Manutencao"),
            (5002, "Ponte em Manutencao", "Manutencao"),
            (5024, "Manut Eletrica", "Manutencao"),
            (8001, "Setup", "Setup"),
            (8003, "Prep. Ferramenta", "Setup"),
            (8047, "Troca de Tipo", "Setup"),
            (2005, "Falta Operador", "Diversos"),
            (2011, "Cafe/Agua/Banheiro", "Diversos"),
            (2013, "Falta de Energia Geral", "Diversos"),
            (1500, "Reuniao", "Atividades Interativas"),
            (1503, "Treinamento", "Atividades Interativas")
        ]
        c.executemany("INSERT OR IGNORE INTO paradas_mestre (codigo, descricao, categoria) VALUES (?, ?, ?)", dados_iniciais)
        conn.commit()

popular_paradas_iniciais()

# --- MENU LATERAL ---
st.sidebar.title("Apontamento PM/OTS")
menu = st.sidebar.radio(
    "Navegacao",
    ["Registrar Apontamento", "Painel de Apontamentos & Horas", "Totais de Pecas Prontas"]
)

# --- SEÇÃO 1: REGISTRAR APONTAMENTO ---
if menu == "Registrar Apontamento":
    st.subheader("Novo Apontamento (Fisico / Digital com OCR Inteligente)")
    st.write("Envie a foto do relatório preenchido. A IA extrairá o cabeçalho e todas as linhas de apontamento com horários e volumes automaticamente.")

    foto_apontamento = st.file_uploader("Enviar Foto do Relatorio Preenchido", type=["jpg", "jpeg", "png"])
    
    if foto_apontamento:
        st.image(foto_apontamento, caption="Foto do Apontamento Fisico Anexada", width=400)
        
        if st.button("Ler Relatorio e Salvar Todas as Linhas Automaticamente", use_container_width=True):
            with st.spinner("Analisando a foto e extraindo todos os apontamentos..."):
                try:
                    bytes_imagem = foto_apontamento.getvalue()
                    base64_imagem = base64.b64encode(bytes_imagem).decode('utf-8')
                    
                    k1 = "sk-proj-R1CPgWpxfnwhtoLkz26rPst"
                    k2 = "Xqe5wWC5bUQMGiSVRwcXD6QzRCJM6zP4vYSssQNL0ClmQtlZUpwT3BlbkFJFoQDDPZy6sO2wCS2TcyT0KinVb7y-elxpgPTlABLKvNYBUTtzj_WvEhLj1i84R778SjmJ0IhwA"
                    client = openai.OpenAI(api_key=k1 + k2)
                    
                    prompt_sistema = """
                    Você é um especialista em extração de dados de relatórios fabris manuscritos.
                    Retorne estritamente um objeto JSON contendo o cabeçalho e uma lista de linhas (itens).
                    Estrutura exata do JSON:
                    {
                      "turno": "",
                      "maquina": "",
                      "data": "AAAA-MM-DD",
                      "responsavel": "",
                      "linhas": [
                        {
                          "op": "",
                          "qtd_op": 0.0,
                          "codigo_desenho": "",
                          "codigo_maxion": "",
                          "operacao": "",
                          "codigo_parada": 0,
                          "hora_inicio": "HH:MM",
                          "hora_fim": "HH:MM",
                          "num_batidas": 0.0,
                          "pcas_boas": 0.0,
                          "sucata": 0.0,
                          "num_etiqueta": "",
                          "motivo": ""
                        }
                      ]
                    }
                    """
                    
                    resposta = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": prompt_sistema},
                            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_imagem}"}}]}
                        ],
                        response_format={"type": "json_object"}
                    )
                    
                    resultado = json.loads(resposta.choices[0].message.content)
                    
                    cab_turno = resultado.get("turno", "")
                    cab_maquina = resultado.get("maquina", "")
                    cab_data = resultado.get("data", str(date.today()))
                    cab_resp = resultado.get("responsavel", "")
                    linhas = resultado.get("linhas", [])
                    
                    inseridos = 0
                    for item in linhas:
                        c.execute("""
                            INSERT INTO apontamentos (turno, maquina, data_apontamento, responsavel, op, qtd_op, codigo_desenho, codigo_maxion, operacao, codigo_parada, hora_inicio, hora_fim, num_batidas, pcas_boas, sucata, num_etiqueta, motivo)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            cab_turno, cab_maquina, cab_data, cab_resp,
                            item.get("op", ""), float(item.get("qtd_op", 0.0) or 0.0),
                            item.get("codigo_desenho", ""), item.get("codigo_maxion", ""),
                            item.get("operacao", ""), int(item.get("codigo_parada", 0) or 0),
                            item.get("hora_inicio", "05:00"), item.get("hora_fim", "05:50"),
                            float(item.get("num_batidas", 0.0) or 0.0),
                            float(item.get("pcas_boas", 0.0) or 0.0),
                            float(item.get("sucata", 0.0) or 0.0),
                            item.get("num_etiqueta", ""), item.get("motivo", "")
                        ))
                        inseridos += 1
                    
                    conn.commit()
                    st.success(f"Sucesso! {inseridos} linha(s) de apontamento extraída(s) e salva(s) com todas as horas e volumes.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao processar imagem com IA: {e}")

    # Formulário manual tradicional (caso queira preencher avulso)
    with st.form("form_apontamento"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            turno = st.text_input("Turno")
            op = st.text_input("O.P.")
        with col2:
            maquina = st.text_input("Maquina")
            qtd_op = st.number_input("Qtd O.P.", step=1.0)
        with col3:
            data_ap = st.date_input("Data", value=date.today())
            cod_desenho = st.text_input("Codigo Desenho")
        with col4:
            responsavel = st.text_input("Responsavel")
            cod_maxion = st.text_input("Codigo Maxion")

        col_op1, col_op2, col_op3, col_op4 = st.columns(4)
        with col_op1:
            operacao = st.text_input("Operacao (Ex: 20/20)")
        with col_op2:
            df_paradas = pd.read_sql("SELECT codigo, descricao FROM paradas_mestre", conn)
            lista_paradas = [f"{row.codigo} - {row.descricao}" for _, row in df_paradas.iterrows()]
            parada_sel = st.selectbox("Codigo Paradas", lista_paradas)
            cod_parada = int(parada_sel.split(" - ")[0])
        with col_op3:
            h_inicio = st.text_input("Inicio", value="05:00")
        with col_op4:
            h_fim = st.text_input("Fim", value="05:50")

        col_pr1, col_pr2, col_pr3, col_pr4 = st.columns(4)
        with col_pr1:
            n_batidas = st.number_input("N Batidas", step=1.0)
        with col_pr2:
            p_boas = st.number_input("Pcs Boas", step=1.0)
        with col_pr3:
            sucata = st.number_input("Sucata", step=1.0)
        with col_pr4:
            etiqueta = st.text_input("N Etiqueta")

        motivo = st.text_area("Motivo da Parada")

        btn_salvar = st.form_submit_button("Salvar Apontamento Manual", use_container_width=True)
        if btn_salvar:
            c.execute("""
                INSERT INTO apontamentos (turno, maquina, data_apontamento, responsavel, op, qtd_op, codigo_desenho, codigo_maxion, operacao, codigo_parada, hora_inicio, hora_fim, num_batidas, pcas_boas, sucata, num_etiqueta, motivo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (turno, maquina, data_ap.strftime("%Y-%m-%d"), responsavel, op, qtd_op, cod_desenho, cod_maxion, operacao, cod_parada, h_inicio, h_fim, n_batidas, p_boas, sucata, etiqueta, motivo))
            conn.commit()
            st.success("Apontamento manual salvo com sucesso!")

# --- SEÇÃO 2: PAINEL DE APONTAMENTOS & HORAS ---
elif menu == "Painel de Apontamentos & Horas":
    st.subheader("Painel de Controle de Apontamentos e Verificacao de Horas")
    
    query = """
        SELECT a.*, p.descricao as desc_parada 
        FROM apontamentos a 
        LEFT JOIN paradas_mestre p ON a.codigo_parada = p.codigo 
        ORDER BY a.id DESC
    """
    df_apont = pd.read_sql(query, conn)

    if not df_apont.empty:
        def calcular_horas(row):
            try:
                t1 = datetime.strptime(row["hora_inicio"], "%H:%M")
                t2 = datetime.strptime(row["hora_fim"], "%H:%M")
                diff = (t2 - t1).total_seconds() / 3600
                return round(diff, 2)
            except:
                return 0.0

        df_apont["Horas_Apontadas"] = df_apont.apply(calcular_horas, axis=1)
        st.dataframe(df_apont, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum apontamento cadastrado ate o momento.")

# --- SEÇÃO 3: TOTAIS DE PEÇAS PRONTAS ---
elif menu == "Totais de Pecas Prontas":
    st.subheader("Somatorio e Controle de Pecas Prontas")
    st.write("Considera apenas operacoes finalizadas (onde o numerador e igual ao denominador, ex: 20/20, 10/10).")

    df_pecas = pd.read_sql("SELECT * FROM apontamentos", conn)

    if not df_pecas.empty:
        def e_peca_pronta(op_str):
            try:
                if "/" in str(op_str):
                    partes = str(op_str).split("/")
                    p1 = float(partes[0].strip())
                    p2 = float(partes[1].strip())
                    return p1 == p2 and p1 > 0
            except:
                return False
            return False

        df_pecas["Pronta"] = df_pecas["operacao"].apply(e_peca_pronta)
        df_prontas_filtradas = df_pecas[df_pecas["Pronta"] == True]

        if not df_prontas_filtradas.empty:
            total_geral_boas = df_prontas_filtradas["pcas_boas"].sum()
            total_geral_sucata = df_prontas_filtradas["sucata"].sum()

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric("Total de Pecas Boas (Prontas)", f"{total_geral_boas:,.0f}")
            with col_m2:
                st.metric("Total de Sucatas (Prontas)", f"{total_geral_sucata:,.0f}")

            st.markdown("### Detalhamento por Codigo Maxion / Desenho")
            df_agrupado = df_prontas_filtradas.groupby(["codigo_maxion", "codigo_desenho", "operacao"])[["pcas_boas", "sucata"]].sum().reset_index()
            st.dataframe(df_agrupado, use_container_width=True, hide_index=True)
        else:
            st.warning("Nenhuma peca pronta identificada com operacao concluida (ex: 20/20) nos registros atuais.")
    else:
        st.info("Nenhum dado disponivel para calculo de pecas.")
