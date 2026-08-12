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

def popular_paradas_iniciais():
    count = c.execute("SELECT COUNT(*) FROM paradas_mestre").fetchone()[0]
    if count == 0:
        dados_iniciais = [
            (0, "Sem Parada / Produzindo Normal", "Processos"),
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
    st.subheader("Relatorio de Auto Apontamento - PM/OTS (Digital e Editavel)")
    st.write("Envie a foto do relatorio preenchido para carregar os dados no formato da planilha física, permitindo revisar, deletar e salvar.")

    if "linhas_temp" not in st.session_state:
        st.session_state.linhas_temp = []
    if "cab_turno" not in st.session_state:
        st.session_state.cab_turno = ""
    if "cab_maquina" not in st.session_state:
        st.session_state.cab_maquina = ""
    if "cab_data" not in st.session_state:
        st.session_state.cab_data = date.today()
    if "cab_resp" not in st.session_state:
        st.session_state.cab_resp = ""

    foto_apontamento = st.file_uploader("Enviar Foto do Relatorio Preenchido", type=["jpg", "jpeg", "png"])
    
    if foto_apontamento:
        st.image(foto_apontamento, caption="Foto do Apontamento Fisico Anexada", width=400)
        
        if st.button("🤖 Ler Relatorio com IA (Substituir Lote Atual)", use_container_width=True):
            with st.spinner("Analisando a foto e estruturando no formato da planilha..."):
                try:
                    bytes_imagem = foto_apontamento.getvalue()
                    base64_imagem = base64.b64encode(bytes_imagem).decode('utf-8')
                    
                    k1 = "sk-proj-R1CPgWpxfnwhtoLkz26rPst"
                    k2 = "Xqe5wWC5bUQMGiSVRwcXD6QzRCJM6zP4vYSssQNL0ClmQtlZUpwT3BlbkFJFoQDDPZy6sO2wCS2TcyT0KinVb7y-elxpgPTlABLKvNYBUTtzj_WvEhLj1i84R778SjmJ0IhwA"
                    client = openai.OpenAI(api_key=k1 + k2)
                    
                    prompt_sistema = """
                    Extraia dados de relatório de auto apontamento fabril.
                    Retorne estritamente um JSON com:
                    {
                      "turno": "",
                      "maquina": "",
                      "data": "AAAA-MM-DD",
                      "responsavel": "",
                      "linhas": [
                        {
                          "op": "", "qtd_op": 0.0, "codigo_desenho": "", "codigo_maxion": "",
                          "operacao": "", "codigo_parada": 0, "hora_inicio": "HH:MM", "hora_fim": "HH:MM",
                          "num_batidas": 0.0, "pcas_boas": 0.0, "sucata": 0.0, "num_etiqueta": "", "motivo": ""
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
                    
                    st.session_state.cab_turno = resultado.get("turno", "")
                    st.session_state.cab_maquina = resultado.get("maquina", "")
                    try:
                        st.session_state.cab_data = datetime.strptime(resultado.get("data", str(date.today())), "%Y-%m-%d").date()
                    except:
                        st.session_state.cab_data = date.today()
                    st.session_state.cab_resp = resultado.get("responsavel", "")
                    
                    # Substitui completamente o lote anterior para não acumular lixo
                    st.session_state.linhas_temp = resultado.get("linhas", [])
                    st.success("Leitura concluída! Dados carregados na tabela abaixo.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao processar imagem: {e}")

    # Cabeçalho da Planilha
    st.markdown("---")
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    with col_c1:
        st.session_state.cab_turno = st.text_input("Turno:", value=st.session_state.cab_turno)
    with col_c2:
        st.session_state.cab_maquina = st.text_input("Máquina:", value=st.session_state.cab_maquina)
    with col_c3:
        st.session_state.cab_data = st.date_input("Data:", value=st.session_state.cab_data)
    with col_c4:
        st.session_state.cab_resp = st.text_input("Nome do Resp. pelo Preenchimento:", value=st.session_state.cab_resp)

    st.markdown("### Linhas de Apontamento (Formato Planilha)")

    if st.button("➕ Adicionar Nova Linha em Branco"):
        st.session_state.linhas_temp.append({
            "op": "", "qtd_op": 0.0, "codigo_desenho": "", "codigo_maxion": "",
            "operacao": "", "codigo_parada": 0, "hora_inicio": "05:00", "hora_fim": "05:50",
            "num_batidas": 0.0, "pcas_boas": 0.0, "sucata": 0.0, "num_etiqueta": "", "motivo": ""
        })
        st.rerun()

    # Renderiza as linhas em formato de tabela editável / com opção de exclusão
    if len(st.session_state.linhas_temp) > 0:
        indices_para_remover = []
        
        for idx, linha in enumerate(st.session_state.linhas_temp):
            with st.container():
                st.markdown(f"**Linha {idx + 1}**")
                lc1, lc2, lc3, lc4, lc5, lc6, lc7, lc8, lc9, lc10, lc11, lc12, lc13 = st.columns([1.2, 1, 1.2, 1.2, 1, 1, 1, 1, 1, 1, 1, 1, 1.5])
                
                with lc1:
                    st.session_state.linhas_temp[idx]["op"] = st.text_input("O.P.", value=linha.get("op",""), key=f"op_{idx}")
                with lc2:
                    st.session_state.linhas_temp[idx]["qtd_op"] = st.number_input("Qtd O.P.", value=float(linha.get("qtd_op",0.0) or 0.0), step=1.0, key=f"qop_{idx}")
                with lc3:
                    st.session_state.linhas_temp[idx]["codigo_desenho"] = st.text_input("Cód. Desenho", value=linha.get("codigo_desenho",""), key=f"cdes_{idx}")
                with lc4:
                    st.session_state.linhas_temp[idx]["codigo_maxion"] = st.text_input("Cód. Maxion", value=linha.get("codigo_maxion",""), key=f"cmax_{idx}")
                with lc5:
                    st.session_state.linhas_temp[idx]["operacao"] = st.text_input("Operação", value=linha.get("operacao",""), key=f"oper_{idx}")
                with lc6:
                    st.session_state.linhas_temp[idx]["codigo_parada"] = st.number_input("Cód Parada", value=int(linha.get("codigo_parada",0) or 0), step=1, key=f"cpar_{idx}")
                with lc7:
                    st.session_state.linhas_temp[idx]["hora_inicio"] = st.text_input("Início", value=linha.get("hora_inicio","05:00"), key=f"hin_{idx}")
                with lc8:
                    st.session_state.linhas_temp[idx]["hora_fim"] = st.text_input("Fim", value=linha.get("hora_fim","05:50"), key=f"hfi_{idx}")
                with lc9:
                    st.session_state.linhas_temp[idx]["num_batidas"] = st.number_input("Nº Bat", value=float(linha.get("num_batidas",0.0) or 0.0), step=1.0, key=f"nbat_{idx}")
                with lc10:
                    st.session_state.linhas_temp[idx]["pcas_boas"] = st.number_input("Pçs Boas", value=float(linha.get("pcas_boas",0.0) or 0.0), step=1.0, key=f"pboa_{idx}")
                with lc11:
                    st.session_state.linhas_temp[idx]["sucata"] = st.number_input("Sucata", value=float(linha.get("sucata",0.0) or 0.0), step=1.0, key=f"psuc_{idx}")
                with lc12:
                    st.session_state.linhas_temp[idx]["num_etiqueta"] = st.text_input("Nº Etq", value=str(linha.get("num_etiqueta","")), key=f"netq_{idx}")
                with lc13:
                    st.session_state.linhas_temp[idx]["motivo"] = st.text_input("Motivo", value=linha.get("motivo",""), key=f"mot_{idx}")
                
                if st.button("🗑️ Deletar Linha", key=f"del_{idx}"):
                    indices_para_remover.append(idx)
                st.markdown("---")

        # Remove as linhas marcadas para exclusão
        if indices_para_remover:
            for i in sorted(indices_para_remover, reverse=True):
                st.session_state.linhas_temp.pop(i)
            st.rerun()

        if st.button("💾 Salvar Lote Definitivo no Banco de Dados", use_container_width=True, type="primary"):
            salvos = 0
            for item in st.session_state.linhas_temp:
                c.execute("""
                    INSERT INTO apontamentos (turno, maquina, data_apontamento, responsavel, op, qtd_op, codigo_desenho, codigo_maxion, operacao, codigo_parada, hora_inicio, hora_fim, num_batidas, pcas_boas, sucata, num_etiqueta, motivo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    st.session_state.cab_turno, st.session_state.cab_maquina, 
                    str(st.session_state.cab_data), st.session_state.cab_resp,
                    item.get("op", ""), float(item.get("qtd_op", 0.0) or 0.0),
                    item.get("codigo_desenho", ""), item.get("codigo_maxion", ""),
                    item.get("operacao", ""), int(item.get("codigo_parada", 0) or 0),
                    item.get("hora_inicio", "05:00"), item.get("hora_fim", "05:50"),
                    float(item.get("num_batidas", 0.0) or 0.0),
                    float(item.get("pcas_boas", 0.0) or 0.0),
                    float(item.get("sucata", 0.0) or 0.0),
                    str(item.get("num_etiqueta", "")), item.get("motivo", "")
                ))
                salvos += 1
            conn.commit()
            st.success(f"Lote salvo com sucesso! {salvos} registro(s) gravados.")
            st.session_state.linhas_temp = []
            st.rerun()
    else:
        st.info("Nenhuma linha carregada no momento. Envie uma foto ou clique em 'Adicionar Nova Linha em Branco'.")

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
                t1 = datetime.strptime(str(row["hora_inicio"]).strip(), "%H:%M")
                t2 = datetime.strptime(str(row["hora_fim"]).strip(), "%H:%M")
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
    st.write("Considera apenas operacoes finalizadas (ex: 20/20, 10/10).")

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
            st.warning("Nenhuma peca pronta identificada com operacao concluida nos registros atuais.")
    else:
        st.info("Nenhum dado disponivel para calculo de pecas.")
