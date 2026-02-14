import streamlit as st
import pandas as pd
import json
from datetime import datetime
from lstm import preparar_dados, treinar_modelo, prever_proxima_rodada
from analise_padroes import renderizar_analise_padroes, renderizar_ciclos
import numpy as np
import os
from keras.models import load_model, save_model
from collections import Counter
from desdobramento import renderizar_tab_desdobramento
from backtest import renderizar_tab_lab
import altair as alt
from atualizador import atualizar_dados
import random
from ensemble import treinar_ensemble, prever_ensemble # Segundo Cérebro
from analise_temporal import renderizar_analise_temporal
from montador import renderizar_montador_manual
from analise_conexoes import renderizar_mapa_conexoes
from historico_previsoes import salvar_previsoes_detalhadas, renderizar_historico_previsoes_tab, executar_retro_analise, sincronizar_resultados
from dashboard_resumo import renderizar_dashboard_resumo
from analise_tendencias import renderizar_detector_tendencias 
from ia_critica import analisar_riscos_jogo
from visualizacao import plotar_radar_equilibrio
from smart_clustering import renderizar_clusters
from manual import renderizar_manual_instrucoes
from caos_exogeno import renderizar_caos_exogeno
from engine import AIEngine


# ... (rest of imports/functions) ...

# Função para carregar e filtrar os dados por intervalo de datas
def carregar_dados():
    caminho = "rodadas.json"
    with open(caminho, 'r') as f:
        dados = json.load(f)
    df = pd.DataFrame(dados)
    df['data'] = pd.to_datetime(df['data'])
    return df

# Frequência de números nos últimos N dias
def contar_frequencias(df, idx, n):
    start = max(0, idx - n)
    subset = df.iloc[start:idx]['numeros'].explode()
    freq = subset.value_counts().to_dict()
    return freq

# Preenche colunas freq_1 a freq_25 de forma ULTRA RÁPIDA
def preencher_frequencias(df, n_dias):
    # Otimização: Criar matriz binária uma única vez
    X = np.zeros((len(df), 25))
    for i, nums in enumerate(df['numeros']):
        for n in nums:
            if 1 <= n <= 25:
                X[i, n-1] = 1
    
    # Usar soma móvel (rolling sum) para calcular frequencias em massa
    df_bins = pd.DataFrame(X, columns=[f'freq_{i}' for i in range(1, 26)])
    df_rolling = df_bins.rolling(window=n_dias, min_periods=1).sum().shift(1).fillna(0)
    
    # Adicionar de volta ao dataframe
    for col in df_rolling.columns:
        df[col] = df_rolling[col]
    return df

# Função para extrair features adicionais
def extrair_features(df, n_dias):
    df = df.copy()
    df['dia_par'] = df['data'].dt.day % 2 == 0
    df['fim_de_semana'] = df['data'].dt.dayofweek >= 5
    df['mes'] = df['data'].dt.month
    df['consecutivos'] = df['numeros'].apply(lambda x: sum(1 for i in range(len(x)-1) if x[i]+1 == x[i+1]))
    df = preencher_frequencias(df, n_dias)
    return df

st.set_page_config(layout="wide", page_title="IA Lotofácil Pro") #tamanho da tela
st.title("IA - Previsão de Rodada")

# Carregar dados inicialmente GLOBALMENTE
df = carregar_dados()

st.sidebar.header("Parâmetros")

if st.sidebar.button("🔄 Atualizar Base de Dados"):
    if atualizar_dados("rodadas.json"):
        st.cache_data.clear() # Limpa cache se houver
        st.rerun()

# Datas Limites da Base
min_db = df['data'].min().date()
max_db = df['data'].max().date()

data_inicial = st.sidebar.date_input("Data Inicial", value=datetime(2022, 1, 1), min_value=min_db, max_value=max_db)
data_final = st.sidebar.date_input("Data Final", value=max_db, min_value=min_db, max_value=max_db)
qtd_numeros = st.sidebar.slider("Qtd. de Números", 15, 20, 15)
qtd_sequencias = st.sidebar.number_input("Qtd. de Sequências Geradas", min_value=1, value=1)
n_dias = st.sidebar.number_input("Janela de Análise (dias)", min_value=1, value=30, help="Quantos dias para trás a IA deve analisar para identificar tendências recentes.")

st.sidebar.markdown("---")

# Filtros em Expander para limpar visual
with st.sidebar.expander("🎯 Filtros Avançados (Fixar/Excluir)", expanded=False):
    st.caption("Use para **forçar** ou **proibir** números na previsão.")
    nums_fixos_str = st.text_input("Fixar Números (OBRIGATÓRIOS)", placeholder="Ex: 1, 13, 25")
    nums_excluidos_str = st.text_input("Excluir Números (PROIBIDOS)", placeholder="Ex: 4, 8")

# Conferência em Expander
with st.sidebar.expander("✅ Conferir Resultado & Treinar", expanded=False):
    st.caption("Selecione um concurso passado para **comparar** com a previsão e **re-treinar**.")
    
    # Montar lista de opções (ex: "Concurso 3000 - 20/05/2024")
    opcoes_concursos = df.sort_values("rodada", ascending=False).apply(
        lambda x: f"{x['rodada']} - {x['data'].strftime('%d/%m/%Y')}", axis=1
    )
    
    concurso_str = st.selectbox("Escolher Concurso para Validar", ["(Nenhum)"] + list(opcoes_concursos))
    
    sequencia_correta_auto = None
    if concurso_str != "(Nenhum)":
        num_concurso = int(concurso_str.split(" - ")[0])
        # Pegar os números desse concurso
        row_sel = df[df['rodada'] == num_concurso].iloc[0]
        sequencia_correta_auto = row_sel['numeros']
        st.info(f"Gabarito carregado: {sequencia_correta_auto}")


usar_aprendizado = st.sidebar.checkbox("Usar aprendizado persistente", value=False)
salvar_aprendizado = st.sidebar.checkbox("Salvar aprendizado após execução", value=False)

tab_manual, tab_previsao, tab_analise, tab_montador, tab_desdobra, tab_lab, tab_caos = st.tabs(["📘 Manual", "🔮 Previsão", "📊 Análise", "🏗️ Montador", "🔢 Desdobrador", "🧪 Laboratório", "🌌 Caos Exógeno"])

# Filtrar dados para análise baseado no sidebar definido acima
df_filtrado_analise = df[(df['data'] >= pd.to_datetime(data_inicial)) & (df['data'] <= pd.to_datetime(data_final))].reset_index(drop=True)

with tab_manual:
    renderizar_manual_instrucoes()

with tab_analise:
    # Passamos o DF completo para a função, pois ela agora tem filtros próprios
    renderizar_detector_tendencias(df) # Nova Feature
    renderizar_clusters(df)
    renderizar_analise_padroes(df)
    renderizar_ciclos(df)
    renderizar_analise_temporal(df)
    renderizar_mapa_conexoes(df)

with tab_montador:
    renderizar_montador_manual(df)

with tab_desdobra:
    renderizar_tab_desdobramento()

with tab_lab:
    renderizar_tab_lab(df, int(n_dias))

with tab_caos:
    renderizar_caos_exogeno(df)

with tab_previsao:
    # --- Feedback do Sistema (Persistente após Rerun) ---
    if 'feedback_msg' in st.session_state:
        msg = st.session_state.feedback_msg
        if msg['type'] == 'success':
            st.success(msg['msg'])
            st.toast(msg['msg'])
        elif msg['type'] == 'warning':
            st.warning(msg['msg'])
            st.toast("⚠️ " + msg['msg'])
        elif msg['type'] == 'error':
            st.error(msg['msg'])
        # Limpar após exibir
        del st.session_state.feedback_msg

    renderizar_dashboard_resumo(df)
    
    # 2. Status da Retro-Análise (Auto-Aprendizado)
    try:
        retro_status = executar_retro_analise(df)
        if isinstance(retro_status, dict):
            # Relatório Completo
            with st.expander(f"🤖 Auto-Calibragem da IA ({retro_status['msg']})", expanded=False):
                st.success(retro_status['vies_descoberto'])
                st.metric("Média de Acertos (IA)", f"{retro_status['media_global']:.2f}")
                st.caption(retro_status['detalhe'])
        elif retro_status:
            # Status de Progresso
            st.caption(f"🧠 {retro_status}")
    except Exception as e:
        pass # Silenciar erros
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    btn_ia = c1.button("🔮 Previsão IA")
    btn_random = c2.button("🎲 Gerar 100% Aleatório")

    if btn_random:
        st.markdown("### 🎲 Surpresinha (Aleatória)")
        resultados = []
        # --- CONSTANTES MATEMÁTICAS ---
        PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}
        MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
        FIBONACCI = {1, 2, 3, 5, 8, 13, 21}
        
        ultima_rodada = set(df.iloc[-1]['numeros'])

        for _ in range(qtd_sequencias):
             # Geração puramente aleatória
             seq = sorted(random.sample(range(1, 26), qtd_numeros))
             
             # Métricas
             impares = sum(1 for x in seq if x % 2 != 0)
             primos = sum(1 for x in seq if x in PRIMOS)
             moldura = sum(1 for x in seq if x in MOLDURA)
             fibo = sum(1 for x in seq if x in FIBONACCI)
             soma = sum(seq)
             repetentes = len(set(seq).intersection(ultima_rodada))
             
             resultados.append({
                'seq': seq,
                'score': 0, 
                'metrics': {
                    'impares': impares, 'primos': primos, 
                    'moldura': moldura, 'fibo': fibo,
                    'repetentes': repetentes, 'soma': soma
                }
             })
        
        # --- VISUALIZAÇÃO COM ORDENAÇÃO ---
        correta_set = set(sequencia_correta_auto) if sequencia_correta_auto else None
        
        # Calcular acertos e ordenar se houver gabarito
        if correta_set:
            for item in resultados:
                item['acertos'] = len(set(item['seq']).intersection(correta_set))
            
            # Ordenar: Mais acertos primeiro.
            resultados.sort(key=lambda x: x['acertos'], reverse=True)
            
            st.markdown(f"### 📝 Comparando com Concurso {concurso_str}")
            st.caption(f"Gabarito Oficial: {sorted(sequencia_correta_auto)}")

        for i, item in enumerate(resultados):
            r = item['seq']
            m = item['metrics']
            
            # Label de acertos
            acertos_label = ""
            if correta_set:
                acertos = item.get('acertos', 0)
                acertos_label = f" | 🎯 Acertos: {acertos}/15"
            
            st.markdown(f"### Jogo Aleatório {i+1} <small>{acertos_label}</small>", unsafe_allow_html=True)
            
            # HTML das Bolinhas
            html_bolas = ""
            for num in r:
                if correta_set:
                    style = "color: white; background-color: #2ecc71; border: 1px solid #27ae60" if num in correta_set else "color: white; background-color: #e74c3c; border: 1px solid #c0392b"
                else:
                    style = "color: black; background-color: #f0f2f6; border: 1px solid #d0d0d0"
                
                html_bolas += f"<span style='{style}; width: 40px; height: 40px; line-height: 40px; text-align: center; margin: 4px; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block'>{num}</span>"
            
            st.markdown(html_bolas, unsafe_allow_html=True)
            st.caption(f"🧬 **DNA:** {m['impares']} Ímpares | {m['primos']} Primos | 🖼️ **{m['moldura']} Moldura** | 🌀 **{m['fibo']} Fibonacci** | ♻️ {m['repetentes']} Repetidas | Σ {m['soma']}")
            st.markdown("---")

        # Salvar para desdobrador
        if resultados:
            st.session_state.ultima_previsao = resultados[0]['seq']

    if btn_ia:
        try:
            df_filtrado = df_filtrado_analise
            if df_filtrado.empty:
                st.error("Nenhuma rodada no intervalo selecionado.")
            else:
                with st.status("🧠 IA Processando: Simulando Futuros...", expanded=True) as status_ia:
                    engine = AIEngine(df, n_dias=int(n_dias))
                    
                    st.write("📡 Escaneando padrões históricos...")
                    # O Engine agora cuida de extrair features, treinar LSTM e Ensemble
                    
                    st.write("🧠 Sincronizando Redes Neurais (LSTM & RF)...")
                    probabilidades = engine.calcular_probabilidades(
                        df_filtrado, 
                        usar_aprendizado=usar_aprendizado, 
                        salvar_aprendizado=salvar_aprendizado
                    )
                    st.session_state.probabilidades_ia = probabilidades

                    st.write(f"🎲 Simulando {max(qtd_sequencias * 50, 500)} jogos equilibrados...")
                    
                    # Tratar Filtros
                    nums_fixos, nums_excluidos = set(), set()
                    if nums_fixos_str:
                        nums_fixos = {int(x.strip()) for x in nums_fixos_str.split(',') if x.strip().isdigit()}
                    if nums_excluidos_str:
                        nums_excluidos = {int(x.strip()) for x in nums_excluidos_str.split(',') if x.strip().isdigit()}
                    
                    ultima_rodada = set(df_filtrado.iloc[-1]['numeros'])
                    
                    resultados = engine.simular_jogos(
                        probabilidades, 
                        qtd_sequencias=qtd_sequencias, 
                        qtd_numeros=qtd_numeros, 
                        nums_fixos=nums_fixos, 
                        nums_excluidos=nums_excluidos, 
                        ultima_rodada=ultima_rodada
                    )

                    # Salvar Palpites
                    if len(resultados) <= 100:
                        salvar_previsoes_detalhadas(resultados, df)
                        st.session_state.feedback_msg = {"type": "success", "msg": f"✅ {len(resultados)} palpites gravados na memória!"}
                    
                    st.session_state.resultados_ia = resultados
                    st.session_state.pagina_atual = 1
                    if resultados: st.session_state.ultima_previsao = resultados[0]['seq']
                    
                    status_ia.update(label="✨ Previsão Concluída com Sucesso!", state="complete", expanded=False)
                st.rerun()

        except Exception as e:
            st.error(f"Ocorreu um erro na IA: {str(e)}")

    # Carregar dados
    try:
        df = carregar_dados()
        
        # --- Espelhamento para SQLite ---
        f_sync = sincronizar_resultados(df)
        if f_sync > 0:
            st.toast(f"🔄 Banco de Dados: {f_sync} novos resultados sincronizados!", icon="💾")
            
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.stop()

    # --- ÁREA DE VISUALIZAÇÃO DE RESULTADOS (PAGINADA) ---
    st.markdown("---")

    # --- HEATMAP PERSISTENTE ---
    if 'probabilidades_ia' in st.session_state:
        st.markdown("### 🌡️ Mapa de Calor (Previsão da IA)")
        probs = st.session_state.probabilidades_ia
        
        # Montar Grid 5x5
        heatmap_data = []
        for i in range(5):
            for j in range(5):
                num = i * 5 + j + 1
                prob = probs[num-1]
                heatmap_data.append({'x': j, 'y': i, 'Número': num, 'Probabilidade': prob})
        
        df_heat = pd.DataFrame(heatmap_data)
        
        chart_heat = alt.Chart(df_heat).mark_rect().encode(
            x=alt.X('x:O', axis=None, scale=alt.Scale(padding=0.05)),
            y=alt.Y('y:O', axis=None, scale=alt.Scale(padding=0.05)),
            color=alt.Color('Probabilidade:Q', scale=alt.Scale(scheme='turbo'), legend=None),
            tooltip=['Número', alt.Tooltip('Probabilidade', format='.2%')]
        ).properties(width=300, height=300)
        
        text_heat = chart_heat.mark_text().encode(
            text='Número:O',
            color=alt.value('black')
        )
        
        st.altair_chart(chart_heat + text_heat, use_container_width=True)
    
    # Verifica se existem resultados na sessão (Memória Persistente)
    if 'resultados_ia' in st.session_state and st.session_state.resultados_ia:
        results = st.session_state.resultados_ia
        
        # 1. Conferência (Se houver gabarito selecionado)
        if sequencia_correta_auto is not None:
             correta_set = set(sequencia_correta_auto)
             # Calcular acertos e atualizar score
             for item in results:
                 acertos = len(set(item['seq']).intersection(correta_set))
                 item['acertos_check'] = acertos
             
             # Re-ordenar por ACERTOS (Top) -> Score
             results.sort(key=lambda x: (x.get('acertos_check', 0), x['score']), reverse=True)
             
             st.info(f"🔎 Resultados reordenados por acertos no Concurso {concurso_str}")

        # 2. Paginação
        total_items = len(results)
        page_size = 10
        total_pages = (total_items - 1) // page_size + 1
        
        col_pag1, col_pag2, col_pag3 = st.columns([2, 1, 2])
        with col_pag2:
            st.session_state.pagina_atual = st.number_input(
                f"Página (Total {total_pages})", 
                min_value=1, max_value=total_pages, 
                value=st.session_state.get('pagina_atual', 1)
            )
        
        start_idx = (st.session_state.pagina_atual - 1) * page_size
        end_idx = start_idx + page_size
        subset = results[start_idx:end_idx]
        
        st.markdown(f"**Mostrando {start_idx+1} a {min(end_idx, total_items)} de {total_items} previsões**")
        
        # 3. Renderizar Lista
        for i, item in enumerate(subset):
            real_index = start_idx + i + 1
            r = item['seq']
            m = item['metrics']
            score = item['score']
            conf = item.get('confianca', 0)
            
            # Badges Logic
            def badge(label, val, ideal_min, ideal_max):
                cor = "#2ecc71" if ideal_min <= val <= ideal_max else "#e74c3c" # Green or Red
                icone = "✅" if ideal_min <= val <= ideal_max else "⚠️"
                return f"<span style='background-color:{cor}20; color:{cor}; border:1px solid {cor}; padding:2px 6px; border-radius:4px; font-size:12px; margin-right:5px'>{icone} <b>{label}: {val}</b></span>"

            badges_html = ""
            badges_html += badge("Ímpares", m['impares'], 7, 9)
            badges_html += badge("Primos", m['primos'], 4, 6)
            badges_html += badge("Moldura", m['moldura'], 8, 11)
            badges_html += badge("Fibo", m['fibo'], 3, 5)
            badges_html += badge("Repetentes", m['repetentes'], 8, 10)
            badges_html += f"<span style='color:#666; font-size:12px'> | Σ {m['soma']}</span>"

            # Confiança Bar (Visual)
            cor_conf = "#f1c40f" if conf < 70 else "#27ae60"
            conf_html = f"""
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:5px">
                <span style="font-size:12px; color:#555">🤖 Confiança IA:</span>
                <div style="flex-grow:1; background:#eee; height:8px; border-radius:4px; max-width:100px;">
                    <div style="width:{min(conf, 100)}%; background:{cor_conf}; height:100%; border-radius:4px;"></div>
                </div>
            </div>
            """
            
            acertos_label = ""
            correta_set = set(sequencia_correta_auto) if sequencia_correta_auto is not None else None
            
            html_numeros = ""
            if correta_set:
                matches = set(r).intersection(correta_set)
                acertos_cnt = len(matches)
                cor_badge = "green" if acertos_cnt >= 11 else "#666"
                acertos_label = f" <span style='background-color:{cor_badge}; color:white; padding:2px 6px; border-radius:4px; font-size:14px; margin-left:10px'>{acertos_cnt} ACERTOS</span>"
                
                html_numeros = ' '.join([
                    f"<span style='color: white; background-color: {'#27ae60' if num in correta_set else '#c0392b'}; padding: 4px; margin: 2px; border-radius: 5px; display:inline-block; width:28px; text-align:center'>{num}</span>"
                    for num in r
                ])
            else:
                html_numeros = ' '.join([f"<span style='color: white; background-color: #2980b9; padding: 4px; margin: 2px; border-radius: 5px; display:inline-block; width:28px; text-align:center'>{num}</span>" for num in r])

            st.markdown(f"### #{real_index} <small>(Score Equilíbrio: {score}/12)</small> {acertos_label}", unsafe_allow_html=True)
            st.markdown(conf_html, unsafe_allow_html=True)
            st.markdown(html_numeros, unsafe_allow_html=True)
            st.markdown(f"<div style='margin-top:5px'>{badges_html}</div>", unsafe_allow_html=True)
            
            # --- INTEGRAÇÃO: ADVOGADO DO DIABO (IA CRÍTICA) ---
            alerts = analisar_riscos_jogo(r)
            if alerts:
                # Mostrar alertas críticos
                for alert in alerts:
                    st.markdown(f"<small style='color:#c0392b'>{alert}</small>", unsafe_allow_html=True)
            
            # --- INTEGRAÇÃO: RADAR VISUAL ---
            with st.expander("🧐 Ver Análise Visual (Radar)", expanded=False):
                c_radar, c_info = st.columns([1,2])
                with c_radar:
                    plotar_radar_equilibrio(m)
                with c_info:
                    st.caption("Este gráfico mostra o quão perto o jogo está da 'perfeição matemática' em cada critério. Barras verdes indicam equilíbrio total.")
            
            st.markdown("---")
