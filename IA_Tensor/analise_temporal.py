import streamlit as st
import pandas as pd
import altair as alt
from collections import Counter

def renderizar_analise_temporal(df):
    st.markdown("---")
    st.markdown("## 📅 Análise Temporal e Sazonal")
    st.markdown("Descubra padrões ocultos baseados em **datas, dias da semana e períodos do ano**. Alguns números gostam mais de dias ímpares?")

    # 1. Preparar dados locais para não alterar o original permanentemente
    df_temp = df.copy()
    # Garantir datetime
    if not pd.api.types.is_datetime64_any_dtype(df_temp['data']):
         df_temp['data'] = pd.to_datetime(df_temp['data'])

    df_temp['dia'] = df_temp['data'].dt.day
    df_temp['mes'] = df_temp['data'].dt.month
    df_temp['ano'] = df_temp['data'].dt.year
    df_temp['dia_semana'] = df_temp['data'].dt.day_name()
    df_temp['trimestre'] = df_temp['data'].dt.quarter
    
    # --- UI DE FILTROS ---
    with st.expander("🔎 Configurar Filtros de Data", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            anos = sorted(df_temp['ano'].unique(), reverse=True)
            filtro_anos = st.multiselect("📅 Ano(s)", anos, default=[])
            st.caption("Vazio = Todos")

        with c2:
            filtro_dia_tipo = st.selectbox("📅 Tipo de Dia (Número)", 
                                         ["Todos", "Dias Ímpares (1, 3, 5...)", "Dias Pares (2, 4, 6...)"])
        
        with c3:
            # Dicionário de tradução
            mapa_dias = {
                "Monday": "Segunda-feira", "Tuesday": "Terça-feira", "Wednesday": "Quarta-feira",
                "Thursday": "Quinta-feira", "Friday": "Sexta-feira", "Saturday": "Sábado"
            }
            # Opções reversas para o multiselect
            opcoes_rev = {v: k for k, v in mapa_dias.items()}
            
            filtro_dia_semana_label = st.multiselect("📆 Dias da Semana", list(mapa_dias.values()), default=[])
            # Converter labels de volta para inglês para filtrar
            filtro_dia_semana_en = [opcoes_rev[d] for d in filtro_dia_semana_label]
        
        with c4:
            filtro_periodo = st.selectbox("🗓️ Período do Ano", 
                                        ["Todo o Ano", 
                                         "1º Semestre (Jan-Jun)", "2º Semestre (Jul-Dez)",
                                         "1º Trimestre (Jan-Mar)", "2º Trimestre (Abr-Jun)",
                                         "3º Trimestre (Jul-Set)", "4º Trimestre (Out-Dez)"])

    # --- APLICAR FILTROS LÓGICOS ---
    df_filtered = df_temp.copy()
    
    # 0. Filtro Ano
    if filtro_anos:
        df_filtered = df_filtered[df_filtered['ano'].isin(filtro_anos)]
    
    # 1. Filtro Dia ímpar/par
    if filtro_dia_tipo == "Dias Ímpares (1, 3, 5...)":
        df_filtered = df_filtered[df_filtered['dia'] % 2 != 0]
    elif filtro_dia_tipo == "Dias Pares (2, 4, 6...)":
        df_filtered = df_filtered[df_filtered['dia'] % 2 == 0]
        
    # 2. Filtro Dia Semana
    if filtro_dia_semana_en:
        df_filtered = df_filtered[df_filtered['dia_semana'].isin(filtro_dia_semana_en)]
        
    # 3. Filtro Periodo
    if filtro_periodo == "1º Semestre (Jan-Jun)":
        df_filtered = df_filtered[df_filtered['mes'] <= 6]
    elif filtro_periodo == "2º Semestre (Jul-Dez)":
        df_filtered = df_filtered[df_filtered['mes'] > 6]
    elif "Trimestre" in filtro_periodo:
        tri_map = {"1º Trimestre": 1, "2º Trimestre": 2, "3º Trimestre": 3, "4º Trimestre": 4}
        key = filtro_periodo.split(" (")[0]
        target_tri = tri_map.get(key, 0)
        if target_tri:
            df_filtered = df_filtered[df_filtered['trimestre'] == target_tri]

    # --- RESULTADOS ---
    if df_filtered.empty:
        st.warning("⚠️ Nenhum concurso encontrado com esta combinação específica de filtros.")
        return

    st.info(f"🔎 Analisando **{len(df_filtered)}** concursos encontrados com estes critérios.")
    
    # Calcular Frequências no Subset
    total_draws = len(df_filtered)
    counts = Counter()
    for nums in df_filtered['numeros']:
        counts.update(nums)
        
    data_freq = []
    # Probabilidade base teórica da Lotofácil (15/25 = 0.60)
    FREQ_TEORICA = 0.60
    
    for num in range(1, 26):
        qtd = counts[num]
        freq = qtd / total_draws
        diff = freq - FREQ_TEORICA # Diferença da média estatistica
        data_freq.append({
            'Número': num,
            'Ocorrências': qtd,
            'Frequência': freq,
            'Desvio': diff
        })
        
    df_res = pd.DataFrame(data_freq)
    
    # Ordenar
    df_res_sorted = df_res.sort_values('Frequência', ascending=False)
    
    # --- DASHBOARD VISUAL ---
    
    # Top 3 Quentes e Frios
    top = df_res_sorted.head(3)
    bot = df_res_sorted.tail(3)
    
    c_res1, c_res2 = st.columns(2)
    with c_res1:
        st.markdown("### 🔥 Mais Sorteados (Neste Padrão)")
        for i, row in top.iterrows():
            st.markdown(f"**{int(row['Número']):02d}** <small>({row['Frequência']:.1%})</small>", unsafe_allow_html=True)

    with c_res2:
        st.markdown("### ❄️ Menos Sorteados (Neste Padrão)")
        for i, row in bot.iloc[::-1].iterrows(): 
            st.markdown(f"**{int(row['Número']):02d}** <small>({row['Frequência']:.1%})</small>", unsafe_allow_html=True)

    # Gráfico de Desvio da Média
    st.markdown("#### 📊 Desvio da Média (vs 60%)")
    st.caption("Barras **verdes**: O número gosta dessa data. Barras **vermelhas**: O número evita essa data.")
    
    chart = alt.Chart(df_res).mark_bar().encode(
        x=alt.X('Número:O', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Desvio:Q', axis=alt.Axis(format='%', title='Desvio da Média (60%)')),
        color=alt.condition(
            alt.datum.Desvio > 0,
            alt.value("#27ae60"),  # Positivo
            alt.value("#e74c3c")   # Negativo
        ),
        tooltip=['Número', alt.Tooltip('Frequência', format='.1%'), alt.Tooltip('Desvio', format='.1%'), 'Ocorrências']
    ).properties(height=300)
    
    st.altair_chart(chart, use_container_width=True)

    # --- INSIGHTS AUTOMÁTICOS (NA SELEÇÃO ATUAL) ---
    st.markdown("---")
    st.markdown("### 🤖 IA Detective: Insights da Seleção Atual")
    st.caption("A IA analisa **os dados filtrados acima** para descobrir o que torna esse período/dia especial em relação ao todo.")
    
    if st.button("✨ Gerar Insights (Baseado nos Filtros)"):
        if len(df_filtered) < 20:
             st.warning("⚠️ Poucos dados filtrados para uma análise estatística confiável (menos de 20 concursos). Tente ampliar o período.")
        else:
            with st.spinner(f"🕵️‍♂️ Comparando os {len(df_filtered)} jogos filtrados com a média histórica..."):
                insights = []
                
                # Helper para calcular frequencia
                def get_freqs(dframe):
                    total = len(dframe)
                    if total == 0: return {}
                    c = Counter()
                    for nums in dframe['numeros']: c.update(nums)
                    return {k: v/total for k,v in c.items()}

                # Média Global (Baseline - O "Normal" da Loteria)
                global_freqs = get_freqs(df_temp)
                
                # Média do Filtro (O comportamento neste cenário específico)
                filter_freqs = get_freqs(df_filtered)
                
                # 1. Análise Direta: Quem brilha neste filtro?
                for num in range(1, 26):
                    freq_filtro = filter_freqs.get(num, 0)
                    freq_global = global_freqs.get(num, 0)
                    
                    diff = freq_filtro - freq_global
                    
                    # Se desvio for significativo (positivo ou negativo)
                    if diff > 0.10: # 10% acima do normal
                        insights.append({
                            "num": num,
                            "msg": f"O número **{num}** fica **MUITO MAIS FORTE** neste cenário! (Sobe de {freq_global:.0%} para **{freq_filtro:.0%}**)",
                            "score": diff
                        })
                    elif diff > 0.05: # 5% acima
                         insights.append({
                            "num": num,
                            "msg": f"O número **{num}** melhora neste cenário. (Sobe de {freq_global:.0%} para {freq_filtro:.0%})",
                            "score": diff
                        })
                    elif diff < -0.10: # 10% abaixo
                        insights.append({
                            "num": num,
                            "msg": f"O número **{num}** **DESAPARECE** neste cenário! (Cai de {freq_global:.0%} para **{freq_filtro:.0%}**)",
                            "score": abs(diff)
                        })

                # 2. Padrões de Pares/Ímpares neste filtro
                # (Ex: Se o filtro for 'Sexta-feira', será que nas sextas saem mais Impares?)
                impares_filtro = []
                for nums in df_filtered['numeros']:
                    impares_filtro.append(sum(1 for n in nums if n % 2 != 0))
                
                media_impares = sum(impares_filtro) / len(impares_filtro) if impares_filtro else 7.5
                if media_impares > 8:
                     insights.append({
                            "num": 99,
                            "msg": f"⚠️ Neste cenário, a tendência é saírem **MAIS ÍMPARES** do que o normal (Média: {media_impares:.1f})",
                            "score": 0.5 # Prioridade alta
                        })
                elif media_impares < 7:
                     insights.append({
                            "num": 99,
                            "msg": f"⚠️ Neste cenário, a tendência é saírem **MAIS PARES** do que o normal (Média de ímpares cai para {media_impares:.1f})",
                            "score": 0.5
                        })

                # Ordenar insights
                insights.sort(key=lambda x: x['score'], reverse=True)
                
                # Exibir
                if not insights:
                    st.info("O comportamento estatístico deste filtro é muito parecido com a média geral. Nenhuma anomalia detectada.")
                else:
                    for ins in insights: 
                        st.success(f"💎 {ins['msg']}")
