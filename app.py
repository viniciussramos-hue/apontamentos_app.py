from datetime import date, datetime
import pandas as pd
import plotly.express as px
import streamlit as st
import sqlite3

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gestão de Apontamentos PM/OTS",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONEXÃO COM O BANCO DE DADOS ---
conn = sqlite3.connect("apontamentos_fabrica.db", check_same_thread=False)
c = conn.cursor()

# Criação das tabelas essenciais
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

# --- CARREGA DADOS MESTRES DE PARADA (Baseados no seu print) ---
def popular_paradas_iniciais():
    count = c.execute("SELECT COUNT(*) FROM paradas_mestre").fetchone()[0]
    if count == 0:
        dados_iniciais = [
            (7011, "Limpeza - (Sucatas, Batoques, Plasticos e Óleo)", "Processos"),
            (7016, "Inspeção por frequência", "Processos"),
            (7091, "Lixando Pçs", "Processos"),
            (7182, "Falta Operação Anterior", "Processos"),
            (7183, "Falta Operação Posterior", "Processos"),
            (4002, "Quebra/Desg Punção", "Ferramentaria"),
            (4003, "Quebra/Desg Matriz", "Ferramentaria"),
            (4010, "Limpeza de Batoque", "Ferramentaria"),
            (5001, "Falta AR Comprimido", "Manutenção"),
            (5002, "Ponte em Manutenção", "Manutenção"),
            (5024, "Manut Elétrica", "Manutenção"),
            (8001, "Setup", "Setup"),
            (8003, "Prep. Ferramenta", "Setup"),
            (8047, "Troca de Tipo", "Setup"),
            (2005, "Falta Operador", "Diversos"),
            (2011, "Café/Água/Banheiro", "Diversos"),
            (2013, "Falta de Energia Geral", "Diversos"),
            (1500, "Reunião", "Atividades Interativas"),
            (1503, "Treinamento", "Atividades Interativas")
        ]
        c.executemany("INSERT OR IGNORE INTO paradas_mestre (codigo, descricao, categoria) VALUES (?, ?, ?)", dados_iniciais)
        conn.commit()

popular_paradas_iniciais()

# --- MENU LATERAL ---
st.sidebar.title("🏭 Apontamento PM/OTS")
menu = st.sidebar.radio(
    "Navegação",
    ["📝 Registrar Apontamento", "📋 Painel de Apontamentos & Horas", "📦 Totais de Peças Prontas"]
)

# --- SEÇÃO 1: REGISTRAR APONTAMENTO ---
if menu == "📝 Registrar Apontamento":
    st.subheader("📝 Novo Apontamento (Físico / Digital)")
    st.write("Preencha os dados do relatório ou faça o upload/foto do documento preenchido.")

    # Upload da foto do apontamento físico
    foto_apontamento = st.file_uploader("Enviar Foto do Relatório Preenchido (Opcional)", type=["jpg", "jpeg", "png"])
    if foto_apontamento:
        st.image(foto_apontamento, caption="Foto do Apontamento Físico Anexada", width=400)

    with st.form("form_apontamento"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            turno = st.text_input("Turno")
            op = st.text_input("O.P.")
        with col2:
            maquina = st.text_input("Máquina")
            qtd_op = st.number_input("Qtd O.P.", min_value=0.0, step=1.0)
        with col3:
            data_ap = st.date_input("Data", value=date.today())
            cod_desenho = st.text_input("Código Desenho")
        with col4:
            responsável = st.text_input("Responsável Preenchimento")
            cod_maxion = st.text_input("Código Maxion")

        st.markdown("---")
        col_op1, col_op2, col_op3, col_op4 = st.columns(4)
        with col_op1:
            operacao = st.text_input("Operação (Ex: 20/20, 10/20)")
        with col_op2:
            # Busca as paradas cadastradas no banco para seleção com descrição
            df_paradas = pd.read_sql("SELECT codigo, descricao FROM paradas_mestre", conn)
            lista_paradas = [f"{row.codigo} - {row.descricao}" for _, row in df_paradas.iterrows()]
            parada_escolhida = st.selectbox("Código Paradas", lista_paradas)
            codigo_parada_val = int(parada_escolhida.split(" - ")[0])
        with col_op3:
            hora_inicio = st.text_input("Início (HH:MM)", value="05:00")
        with col_op4:
            hora_fim = st.text_input("Fim (HH:MM)", value="05:50")

        col_pr1, col_pr2, col_pr3, col_pr4 = st.columns(4)
        with col_pr1:
            num_batidas = st.number_input("Nº Batidas", min_value=0.0, step=1.0)
        with col_pr2:
            pcas_boas = st.number_input("Pçs Boas", min_value=0.0, step=1.0)
        with col_pr3:
            sucata = st.number_input("Sucata", min_value=0.0, step=1.0)
        with col_pr4:
            num_etiqueta = st.text_input("Nº Etiqueta")

        motivo = st.text_area("Problemas ocorridos / Motivo da Parada")

        btn_salvar = st.form_submit_button("Salvar Apontamento", use_container_width=True)
        if btn_salvar:
            c.execute("""
                INSERT INTO apontamentos (turno, maquina, data_apontamento, responsavel, op, qtd_op, codigo_desenho, codigo_maxion, operacao, codigo_parada, hora_inicio, hora_fim, num_batidas, pcas_boas, sucata, num_etiqueta, motivo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (turno, maquina, data_ap.strftime("%Y-%m-%d"), responsável, op, qtd_op, cod_desenho, cod_maxion, operacao, codigo_parada_val, hora_inicio, hora_fim, num_batidas, pcas_boas, sucata, num_etiqueta, motivo))
            conn.commit()
            st.success("Apontamento registrado com sucesso!")

# --- SEÇÃO 2: PAINEL DE APONTAMENTOS & HORAS ---
elif menu == "📋 Painel de Apontamentos & Horas":
    st.subheader("📋 Painel de Controle de Apontamentos e Verificação de Horas")
    
    query = """
        SELECT a.*, p.descricao as desc_parada 
        FROM apontamentos a 
        LEFT JOIN paradas_mestre p ON a.codigo_parada = p.codigo 
        ORDER BY a.id DESC
    """
    df_apont = pd.read_sql(query, conn)

    if not df_apont.empty:
        # Função para calcular o total de horas apontadas entre Início e Fim
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
        st.info("Nenhum apontamento cadastrado até o momento.")

# --- SEÇÃO 3: TOTAIS DE PEÇAS PRONTAS ---
elif menu == "📦 Totais de Peças Prontas":
    st.subheader("📦 Somatório e Controle de Peças Prontas")
    st.write("Considera apenas operações finalizadas (onde o numerador é igual ao denominador, ex: 20/20, 10/10, desconsiderando parciais como 10/20).")

    df_pecas = pd.read_sql("SELECT * FROM apontamentos", conn)

    if not df_pecas.empty:
        # Lógica para filtrar operações prontas (ex: 20/20 onde parte 1 == parte 2 e ambas > 0)
        def é_peca_pronta(op_str):
            try:
                if "/" in str(op_str):
                    partes = op_str.split("/")
                    p1 = float(partes[0].strip())
                    p2 = float(partes[1].strip())
                    return p1 == p2 and p1 > 0
            except:
                return False
            return False

        df_pecas["Pronta"] = df_pecas["operacao"].apply(é_peca_pronta)
        
        # Filtra apenas as prontas
        df_prontas_filtradas = df_pecas[df_pecas["Pronta"] == True]

        if not df_prontas_filtradas.empty:
            total_geral_boas = df_prontas_filtradas["pcas_boas"].sum()
            total_geral_sucata = df_prontas_filtradas["sucata"].sum()

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric("Total de Peças Boas (Prontas)", f"{total_geral_boas:,.0f}")
            with col_m2:
                st.metric("Total de Sucatas (Prontas)", f"{total_geral_sucata:,.0f}")

            st.markdown("### Detalhamento por Código Maxion / Desenho")
            df_agrupado = df_prontas_filtradas.groupby(["codigo_maxion", "codigo_desenho", "operacao"])[["pcas_boas", "sucata"]].sum().reset_index()
            st.dataframe(df_agrupado, use_container_width=True, hide_index=True)
        else:
            st.warning("Nenhuma peça pronta identificada com operação concluída (ex: 20/20) nos registros atuais.")
    else:
        st.info("Nenhum dado disponível para cálculo de peças.")
