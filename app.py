# --- MENU LATERAL ---
st.sidebar.title("🏭 Apontamento PM/OTS")
menu = st.sidebar.radio(
    "Navegação",
    ["Registrar Apontamento", "Painel de Apontamentos & Horas", "Totais de Peças Prontas"]
)

# --- SEÇÃO 1: REGISTRAR APONTAMENTO ---
if menu == "Registrar Apontamento":
    st.subheader("📝 Novo Apontamento (Físico / Digital com OCR Inteligente)")
    st.write("Faça o upload ou tire a foto do relatório preenchido para o preenchimento automático.")

    # Inicializa variáveis de estado para os campos se não existirem
    if "form_data" not in st.session_state:
        st.session_state.form_data = {
            "turno": "",
            "maquina": "",
            "responsavel": "",
            "op": "",
            "qtd_op": 0.0,
            "cod_desenho": "",
            "cod_maxion": "",
            "operacao": "",
            "inicio": "05:00",
            "fim": "05:50",
            "batidas": 0.0,
            "pcas_boas": 0.0,
            "sucata": 0.0,
            "etiqueta": "",
            "motivo": ""
        }

    # Upload da foto do apontamento físico
    foto_apontamento = st.file_uploader("Enviar Foto do Relatório Preenchido", type=["jpg", "jpeg", "png"])
    
    if foto_apontamento:
        st.image(foto_apontamento, caption="Foto do Apontamento Físico Anexada", width=400)
        
        if st.button("🤖 Ler Relatório Automaticamente com IA", use_container_width=True):
            with st.spinner("Analisando a foto e extraindo os dados manuscritos..."):
                try:
                    import openai
                    import base64
                    import json
                    
                    bytes_imagem = foto_apontamento.getvalue()
                    base64_imagem = base64.b64encode(bytes_imagem).decode('utf-8')
                    
                    client = openai.OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", "SUA_CHAVE_AQUI"))
                    
                    resposta = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "system",
                                "content": "Você é um assistente especializado em extrair dados de formulários de apontamento de produção fabril manuscritos. Retorne estritamente um JSON com as chaves: turno, maquina, responsavel, op, qtd_op, codigo_desenho, codigo_maxion, operacao, hora_inicio, hora_fim, num_batidas, pcas_boas, sucata, num_etiqueta, motivo."
                            },
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "Extraia os dados preenchidos neste relatório de auto apontamento."},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_imagem}"}}
                                ]
                            }
                        ],
                        response_format={"type": "json_object"}
                    )
                    
                    dados_extraidos = json.loads(resposta.choices[0].message.content)
                    
                    st.session_state.form_data = {
                        "turno": dados_extraidos.get("turno", ""),
                        "maquina": dados_extraidos.get("maquina", ""),
                        "responsavel": dados_extraidos.get("responsavel", ""),
                        "op": dados_extraidos.get("op", ""),
                        "qtd_op": float(dados_extraidos.get("qtd_op", 0.0) or 0.0),
                        "cod_desenho": dados_extraidos.get("codigo_desenho", ""),
                        "cod_maxion": dados_extraidos.get("codigo_maxion", ""),
                        "operacao": dados_extraidos.get("operacao", ""),
                        "inicio": dados_extraidos.get("hora_inicio", "05:00"),
                        "fim": dados_extraidos.get("hora_fim", "05:50"),
                        "batidas": float(dados_extraidos.get("num_batidas", 0.0) or 0.0),
                        "pcas_boas": float(dados_extraidos.get("pcas_boas", 0.0) or 0.0),
                        "sucata": float(dados_extraidos.get("sucata", 0.0) or 0.0),
                        "etiqueta": dados_extraidos.get("num_etiqueta", ""),
                        "motivo": dados_extraidos.get("motivo", "")
                    }
                    st.success("✨ Dados extraídos e preenchidos automaticamente com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao processar a imagem com IA: {e}.")

    # Formulário preenchido com os dados (automáticos ou manuais)
    d = st.session_state.form_data
    with st.form("form_apontamento"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            turno = st.text_input("Turno", value=d["turno"])
            op = st.text_input("O.P.", value=d["op"])
        with col2:
            maquina = st.text_input("Máquina", value=d["maquina"])
            qtd_op = st.number_input("Qtd O.P.", value=d["qtd_op"], min_value=0.0, step=1.0)
        with col3:
            data_ap = st.date_input("Data", value=date.today())
            cod_desenho = st.text_input("Código Desenho", value=d["cod_desenho"])
        with col4:
            responsável = st.text_input("Responsável Preenchimento", value=d["responsavel"])
            cod_maxion = st.text_input("Código Maxion", value=d["cod_maxion"])

        st.markdown("---")
        col_op1, col_op2, col_op3, col_op4 = st.columns(4)
        with col_op1:
            operacao = st.text_input("Operação (Ex: 20/20, 10/20)", value=d["operacao"])
        with col_op2:
            df_paradas = pd.read_sql("SELECT codigo, descricao FROM paradas_mestre", conn)
            lista_paradas = [f"{row.codigo} - {row.descricao}" for _, row in df_paradas.iterrows()]
            parada_escolhida = st.selectbox("Código Paradas", lista_paradas)
            codigo_parada_val = int(parada_escolhida.split(" - ")[0])
        with col_op3:
            hora_inicio = st.text_input("Início (HH:MM)", value=d["inicio"])
        with col_op4:
            hora_fim = st.text_input("Fim (HH:MM)", value=d["fim"])

        col_pr1, col_pr2, col_pr3, col_pr4 = st.columns(4)
        with col_pr1:
            num_batidas = st.number_input("Nº Batidas", value=d["batidas"], min_value=0.0, step=1.0)
        with col_pr2:
            pcas_boas = st.number_input("Pçs Boas", value=d["pcas_boas"], min_value=0.0, step=1.0)
        with col_pr3:
            sucata = st.number_input("Sucata", value=d["sucata"], min_value=0.0, step=1.0)
        with col_pr4:
            num_etiqueta = st.text_input("Nº Etiqueta", value=d["etiqueta"])

        motivo = st.text_area("Problemas ocorridos / Motivo da Parada", value=d["motivo"])

        btn_salvar = st.form_submit_button("Salvar Apontamento", use_container_width=True)
        if btn_salvar:
            c.execute("""
                INSERT INTO apontamentos (turno, maquina, data_apontamento, responsavel, op, qtd_op, codigo_desenho, codigo_maxion, operacao, codigo_parada, hora_inicio, hora_fim, num_batidas, pcas_boas, sucata, num_etiqueta, motivo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (turno, maquina, data_ap.strftime("%Y-%m-%d"), responsável, op, qtd_op, cod_desenho, cod_maxion, operacao, codigo_parada_val, hora_inicio, hora_fim, num_batidas, pcas_boas, sucata, num_etiqueta, motivo))
            conn.commit()
            st.success("Apontamento registrado com sucesso!")

# --- SEÇÃO 2: PAINEL DE APONTAMENTOS & HORAS ---
elif menu == "Painel de Apontamentos & Horas":
    st.subheader("📋 Painel de Controle de Apontamentos e Verificação de Horas")
    
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
        st.info("Nenhum apontamento cadastrado até o momento.")

# --- SEÇÃO 3: TOTAIS DE PEÇAS PRONTAS ---
elif menu == "Totais de Peças Prontas":
    st.subheader("📦 Somatório e Controle de Peças Prontas")
    st.write("Considera apenas operações finalizadas (onde o numerador é igual ao denominador, ex: 20/20, 10/10).")

    df_pecas = pd.read_sql("SELECT * FROM apontamentos", conn)

    if not df_pecas.empty:
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
