import streamlit as st
import pandas as pd
import altair as alt
import random
from ui.dashboard_resumo import renderizar_dashboard_resumo
from data.historico_previsoes import executar_retro_analise, salvar_previsoes_detalhadas, sincronizar_resultados
from ui.visualizacao import plotar_radar_equilibrio
from ai.ia_critica import analisar_riscos_jogo
from ai.engine import AIEngine

def renderizar_tab_previsao(
    df, df_filtrado_analise, 
    sequencia_correta_auto, concurso_str, 
    usar_aprendizado, salvar_aprendizado, 
    qtd_sequencias, qtd_numeros, n_dias, 
    nums_fixos_str, nums_excluidos_str
):
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
        
        ultima_rodada = set(df.iloc[-1]['numeros'])

        for _ in range(qtd_sequencias):
             # Geração puramente aleatória
             seq = sorted(random.sample(range(1, 26), qtd_numeros))
             
             # Métricas
             from core.utils import calcular_metricas_dna
             m = calcular_metricas_dna(seq)
             m['repetentes'] = len(set(seq).intersection(ultima_rodada))
             
             resultados.append({
                'seq': seq,
                'score': 0, 
                'metrics': m
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

    # Carregar dados e espelhar SQlite - Pode ser feito global mas aqui assegura update antes de renderizar heatmap
    try:
        # --- Espelhamento para SQLite ---
        f_sync = sincronizar_resultados(df)
        if f_sync > 0:
            st.toast(f"🔄 Banco de Dados: {f_sync} novos resultados sincronizados!", icon="💾")
    except Exception as e:
        st.error(f"Erro ao carregar dados SQLite Sync: {e}")

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
        
        st.altair_chart(chart_heat + text_heat, width='stretch')
    
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
