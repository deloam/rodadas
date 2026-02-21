
import pandas as pd
from itertools import combinations
from collections import Counter, defaultdict
import streamlit as st
from core.utils import calcular_metricas_dna


def analisar_recorrencias(df):
    """
    Analisa duplas e trios frequentes e calcula estatísticas de intervalo (gaps).
    """
    pares_ocorrencias = defaultdict(list)
    trios_ocorrencias = defaultdict(list)
    
    max_rodada = df['rodada'].max() if not df.empty else 0
    
    # Mapear ocorrências
    for rodada_id, numeros in zip(df['rodada'], df['numeros']):
        numeros_sorted = sorted(numeros)
        
        for par in combinations(numeros_sorted, 2):
            pares_ocorrencias[par].append(rodada_id)
            
        for trio in combinations(numeros_sorted, 3):
            trios_ocorrencias[trio].append(rodada_id)
            
    def processar_dados(ocorrencias_dict, format_func):
        data = []
        for combo, lista_rodadas in ocorrencias_dict.items():
            qtd = len(lista_rodadas)
            lista_rodadas.sort()
            
            # Cálculo de Gaps
            if qtd > 1:
                gaps = [lista_rodadas[i] - lista_rodadas[i-1] for i in range(1, qtd)]
                media_gap = sum(gaps) / len(gaps)
            else:
                media_gap = 0
                
            atraso = max_rodada - lista_rodadas[-1]
            
            data.append({
                'Numeros': format_func(combo),
                'Frequencia': qtd,
                'Média Gap': round(media_gap, 1),
                'Atraso': atraso
            })
            
        df_out = pd.DataFrame(data)
        if not df_out.empty:
            df_out = df_out.sort_values(by='Frequencia', ascending=False)
        else:
             df_out = pd.DataFrame(columns=['Numeros', 'Frequencia', 'Média Gap', 'Atraso'])
             
        return df_out[['Numeros', 'Frequencia', 'Média Gap', 'Atraso']]

    df_pares = processar_dados(pares_ocorrencias, lambda x: f"{x[0]} - {x[1]}")
    df_trios = processar_dados(trios_ocorrencias, lambda x: f"{x[0]} - {x[1]} - {x[2]}")
    
    return df_pares, df_trios

def renderizar_analise_padroes(df):
    st.markdown("## 📊 Análise de Padrões Recorrentes")
    
    # Filtros de Data Específicos para a Análise
    st.markdown("### 📅 Configurar Período de Análise")
    col_d1, col_d2 = st.columns(2)
    
    # Garantir que temos datas válidas
    if not df.empty:
        min_global = df['data'].min().date()
        max_global = df['data'].max().date()
    else:
        from datetime import date
        min_global = date(2000, 1, 1)
        max_global = date.today()

    with col_d1: # Default para últimos 2 anos ou todo periodo
        dt_ini = st.date_input("Data Inicial", value=min_global, min_value=min_global, max_value=max_global, key="ana_dt_ini")
    with col_d2:
        dt_fim = st.date_input("Data Final", value=max_global, min_value=min_global, max_value=max_global, key="ana_dt_fim")
        
    # Filtra o DF com base nas datas selecionadas localmente
    mask = (df['data'].dt.date >= dt_ini) & (df['data'].dt.date <= dt_fim)
    df_filtrado = df.loc[mask]
    
    if df_filtrado.empty:
        st.warning("Sem dados para analisar no período selecionado.")
        return

    st.caption(f"Analisando **{len(df_filtrado)}** concuros encontrados neste intervalo.")

    # --- Seção de Análise Específica (NOVO) ---
    st.markdown("---")
    st.markdown("### 🔍 Consultar Combinação Específica")
    st.markdown("Escolha números (duplas, trios, etc.) para ver quantas vezes eles saíram juntos neste período.")
    
    # Botões de Seleção Tipo Volante (5x5)
    if 'numeros_selecionados' not in st.session_state:
        st.session_state.numeros_selecionados = set()

    def toggle_numero(n):
        if n in st.session_state.numeros_selecionados:
            st.session_state.numeros_selecionados.remove(n)
        else:
            st.session_state.numeros_selecionados.add(n)

    st.markdown("##### Selecione os números no volante:")
    
    # Criar grid 5x5
    for i in range(0, 25, 5):
        cols = st.columns(5)
        for j in range(5):
            num = i + j + 1
            with cols[j]:
                # Define cor se selecionado
                label = f"✅ {num}" if num in st.session_state.numeros_selecionados else f"{num}"
                type_btn = "primary" if num in st.session_state.numeros_selecionados else "secondary"
                
                if st.button(label, key=f"btn_volante_{num}", width='stretch', type=type_btn):
                    toggle_numero(num)
                    st.rerun()

    nums_selecionados = list(st.session_state.numeros_selecionados)
    
    if nums_selecionados:
        st.markdown(f"**Selecionados:** {sorted(nums_selecionados)}")
        nums_set = set(nums_selecionados)
        rodadas_encontradas = []
        
        # Iterar sobre o DF filtrado
        for _, row in df_filtrado.iterrows():
            if nums_set.issubset(set(row['numeros'])):
                rodadas_encontradas.append(row)
        
        count = len(rodadas_encontradas)
        porcentagem = (count / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
        
        st.success(f"A combinação **{sorted(nums_selecionados)}** apareceu **{count}** vezes ({porcentagem:.2f}%) neste período.")
        
        # --- Cálculo de Estatísticas de Intervalo (Gaps) ---
        if count > 1:
            rodadas_ids = [r['rodada'] for r in rodadas_encontradas]
            rodadas_ids.sort()
            
            # Calcular intervalos (diferença entre rodadas consecutivas onde houve acerto)
            gaps = [rodadas_ids[i] - rodadas_ids[i-1] for i in range(1, len(rodadas_ids))]
            
            media_gap = sum(gaps) / len(gaps)
            min_gap = min(gaps)
            max_gap = max(gaps)
            
            # Atraso atual (considerando a última rodada do PERÍODO analisado)
            ultimo_hit = rodadas_ids[-1]
            max_rodada_periodo = df_filtrado['rodada'].max()
            atraso_atual = max_rodada_periodo - ultimo_hit
            
            # Estimativa simples (Último Hit + Média)
            proxima_estimada = ultimo_hit + media_gap
            
            # Status
            status_delta = atraso_atual - media_gap
            if status_delta > 0:
                texto_status = "🔥 ATRASADO"
                cor_delta = "inverse" # Vermelho/Destaque
            else:
                texto_status = "❄️ ADIANTADO/NA MÉDIA"
                cor_delta = "normal" 

            probabilidade_gap = (1 / media_gap * 100) if media_gap > 0 else 0

            st.markdown(f"#### ⏱️ Estatísticas de Intervalo (Gaps)")
            m1, m2, m3, m4 = st.columns(4)
            
            m1.metric("Média de Intervalo", f"{media_gap:.1f} rods")
            m2.metric("Mín/Máx Intervalo", f"{min_gap} / {max_gap}")
            m3.metric("Atraso Atual", f"{atraso_atual} rods", delta=f"{status_delta:.1f}", delta_color=cor_delta)
            m4.metric("Próx. Estimada", f"Rodada ~{int(proxima_estimada)}", f"Prob. Teórica: {probabilidade_gap:.1f}%")

            st.caption(f"*O 'Atraso Atual' é contado a partir da última aparição ({ultimo_hit}) até a última rodada do período selecionado ({max_rodada_periodo}).*")

        elif count == 1:
            st.info("A combinação saiu apenas uma vez neste período. Impossível calcular média de intervalos.")
        else:
            st.warning("A combinação não saiu nenhuma vez neste período.")

        if count > 0:
            with st.expander("Ver detalhes dos concursos"):
                df_detalhe = pd.DataFrame(rodadas_encontradas)[['rodada', 'data', 'numeros']]
                df_detalhe['data'] = df_detalhe['data'].dt.strftime('%d/%m/%Y')
                st.dataframe(df_detalhe, hide_index=True, width='stretch')


    # --- Seção de Métricas de Equilíbrio (NOVO) ---
    st.markdown("---")
    st.markdown("### ⚖️ Métricas de Equilíbrio (DNA do Jogo)")
    st.caption("Distribuição estatística dos resultados no período selecionado. Jogos equilibrados tendem a seguir estas médias.")

    # Processamento dos Dados
    dados_equilibrio = []
    for numeros in df_filtrado['numeros']:
        metricas = calcular_metricas_dna(numeros)
        dados_equilibrio.append({
            'Impares': metricas['impares'],
            'Primos': metricas['primos'],
            'Soma': metricas['soma']
        })
    
    df_eq = pd.DataFrame(dados_equilibrio)
    
    col_eq1, col_eq2, col_eq3 = st.columns(3)
    
    import altair as alt

    with col_eq1:
        st.markdown("##### Ímpares vs Pares")
        count_impares = df_eq['Impares'].value_counts().reset_index()
        count_impares.columns = ['Qtd', 'Ocorrências']
        
        c1 = alt.Chart(count_impares).mark_bar(color='#FF6F61').encode(
            x=alt.X('Qtd:O', title='Qtd. Ímpares', sort='ascending'),
            y='Ocorrências:Q',
            tooltip=['Qtd', 'Ocorrências']
        )
        st.altair_chart(c1, width='stretch')
        st.caption("Faixa ideal: 7 a 9 ímpares.")

    with col_eq2:
        st.markdown("##### Números Primos")
        count_primos = df_eq['Primos'].value_counts().reset_index()
        count_primos.columns = ['Qtd', 'Ocorrências']
        
        c2 = alt.Chart(count_primos).mark_bar(color='#6B5B95').encode(
            x=alt.X('Qtd:O', title='Qtd. Primos', sort='ascending'),
            y='Ocorrências:Q',
            tooltip=['Qtd', 'Ocorrências']
        )
        st.altair_chart(c2, width='stretch')
        st.caption("Faixa ideal: 4 a 6 primos.")

    with col_eq3:
        st.markdown("##### Soma Total")
        # Histograma para Soma
        c3 = alt.Chart(df_eq).mark_bar(color='#88B04B').encode(
            x=alt.X('Soma:Q', bin=alt.Bin(maxbins=20)),
            y='count()',
            tooltip=['count()']
        )
        st.altair_chart(c3, width='stretch')
        st.caption(f"Média do período: {df_eq['Soma'].mean():.1f}")

    st.markdown("---")
    st.markdown("### 📉 Estatísticas Gerais do Período")
    
    df_pares, df_trios = analisar_recorrencias(df_filtrado)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔥 Top 20 Duplas")
        try:
            st.dataframe(
                df_pares.head(20).style.background_gradient(cmap="Reds"),
                width='stretch',
                hide_index=True
            )
        except ImportError:
            st.dataframe(
                df_pares.head(20),
                width='stretch',
                hide_index=True
            )

    with col2:
        st.markdown("#### 🔥 Top 20 Trios")
        try:
            st.dataframe(
                df_trios.head(20).style.background_gradient(cmap="Reds"),
                width='stretch',
                hide_index=True
            )
        except ImportError:
            st.dataframe(
                df_trios.head(20),
                width='stretch',
                hide_index=True
            )

def renderizar_ciclos(df):
    """
    Analisa o Ciclo das Dezenas (tempo para sair todos os 25 números).
    Usa lógica Forward para precisão e detecta início de novos ciclos.
    """
    st.markdown("---")
    st.markdown("## 🔄 Monitor de Ciclos")
    
    # Garantir ordenação
    df = df.sort_values('rodada')
    
    # Lógica Forward (Do início ao fim) para determinar estado atual
    numeros_no_ciclo = set()
    ultimo_fechamento = -1
    
    # Percorrer todo o histórico para simular os ciclos reais
    for i, row in df.iterrows():
        numeros = set(row['numeros'])
        numeros_no_ciclo.update(numeros)
        
        if len(numeros_no_ciclo) == 25:
            # Ciclo fechou nesta rodada
            numeros_no_ciclo.clear()
            ultimo_fechamento = row['rodada']
            
    # Estado Atual
    # Se numeros_no_ciclo estiver vazio, significa que o ultimo sorteio fechou o ciclo.
    # Logo, estamos iniciando um NOVO ciclo.
    
    todos = set(range(1, 26))
    sairam = numeros_no_ciclo
    faltam_sair = sorted(list(todos - sairam))
    
    # Determinar se ciclo fechou no último (novo ciclo iniciando agora)
    # Se len(sairam) == 0, então o ciclo fechou no último processado.
    ciclo_fechado_ultimo = (len(sairam) == 0)
    
    c1, c2 = st.columns([1, 2])
    
    if ciclo_fechado_ultimo:
        # Calcular tamanho do ciclo que ACABOU de fechar (apenas para info)
        # Mas o foco é o NOVO.
        with c1:
             st.metric("Ciclo Atual", "INICIANDO (0)")
        with c2:
             st.success("✅ O Ciclo FECHOU no último concurso! Um NOVO CICLO se inicia na próxima rodada.")
             st.info("ℹ️ Dica de Início: Em aberturas de ciclo, é comum haver repetição de 8 a 10 números do sorteio anterior e um equilíbrio renovado.")
             
        st.markdown("### 🔥 Dica para Novo Ciclo")
        st.caption("Como o ciclo reiniciou, todos os 25 números estão disponíveis. Não há 'faltantes' para forçar.")
        
    else:
        # Calcular tamanho do ciclo atual em andamento
        # Filtra rodadas APÓS o ultimo fechamento
        if ultimo_fechamento == -1:
            tamanho = len(df)
        else:
            tamanho = len(df[df['rodada'] > ultimo_fechamento])

        with c1:
            st.metric("Ciclo Atual (Andamento)", f"{tamanho} rodadas")
        with c2:
            st.warning(f"⚠️ Faltam {len(faltam_sair)} números para fechar o ciclo.")
            
        st.markdown("### 🔥 Palpite Quente (Para Fechar Ciclo):")
        st.markdown(
            ' '.join([f"<span style='color: white; background-color: #e67e22; padding: 5px 10px; margin: 3px; border-radius: 5px; font-weight: bold; font-size: 18px; display: inline-block'>{num}</span>" for num in faltam_sair]),
            unsafe_allow_html=True
        )
        st.caption("Estatisticamente, apostar nestes números é muito forte para os próximos sorteios.")

    # Análise extra: Números mais frequentes sozinhos
    numeros_isolados = Counter()
    for rodada in df['numeros']:
        numeros_isolados.update(rodada)
        
    df_isolados = pd.DataFrame(numeros_isolados.most_common(), columns=['Número', 'Frequência'])
    df_isolados = df_isolados.sort_values(by='Frequência', ascending=False)
    
    import altair as alt

    st.markdown("---")
    st.markdown("#### 🏆 Frequência Individual dos Números (Geral)")
    
    chart = alt.Chart(df_isolados).mark_bar().encode(
        x=alt.X('Número:O', axis=alt.Axis(labelAngle=0), sort='-y'),
        y='Frequência:Q',
        tooltip=['Número', 'Frequência']
    )
    
    st.altair_chart(chart, width='stretch')
