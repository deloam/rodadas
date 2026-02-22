import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import random
import altair as alt

def calcular_premio(acertos):
    # Prêmios fixos base (valores aproximados)
    if acertos == 11: return 7.00
    if acertos == 12: return 14.00
    if acertos == 13: return 35.00
    if acertos == 14: return 1500.00 # Estimativa conservadora
    if acertos == 15: return 2000000.00 # Estimativa
    return 0.00

def executar_simulacao(df, n_dias, qtd_testes=5):
    """
    Simula os últimos testes usando uma heurística otimizada (Modo Rápido).
    Nota: Não re-treina a Rede Neural profunda a cada passo para performance.
    Usa um modelo estatístico avançado como proxy.
    """
    resultados_sim = []
    
    if len(df) < n_dias + qtd_testes:
        return pd.DataFrame()
        
    prog_bar = st.progress(0)
    
    for i in range(qtd_testes):
        prog_bar.progress((i + 1) / qtd_testes)
        
        idx_alvo = len(df) - qtd_testes + i
        row_alvo = df.iloc[idx_alvo]
        
        target_rodada = row_alvo['rodada']
        target_numeros = set(row_alvo['numeros'])
        
        # --- MODELO PROXY (Simulação Rápida) ---
        df_treino = df.iloc[:idx_alvo].copy()
        
        # 1. Frequência Dinâmica nos últimos 15 jogos (Peso 60%)
        ultimos_15 = df_treino.tail(15)
        freq_contador = Counter()
        for nums in ultimos_15['numeros']:
            freq_contador.update(nums)
        
        prob_freq = np.zeros(25)
        for num in range(1, 26):
            prob_freq[num-1] = freq_contador.get(num, 0) / 15
            
        # 2. Atraso Inteligente (Peso 40%)
        # Penaliza números muito atrasados (>10) pois tendem a continuar frios em tendências curtas
        # Mas bonifica atrasos médios (reversão à média)
        prob_atraso = np.zeros(25)
        ultima_rodada_abs = df_treino['rodada'].max()
        for num in range(1, 26):
            ocorrencias = df_treino[df_treino['numeros'].apply(lambda x: num in x)]
            if not ocorrencias.empty:
                atraso = ultima_rodada_abs - ocorrencias['rodada'].max()
                if atraso <= 2:
                    val = 0.3 # Repetição recente (Hot)
                elif 3 <= atraso <= 8:
                    val = 0.5 # Zona de retorno provavel
                else: 
                    val = 0.2 # Muito frio
                prob_atraso[num-1] = val
            else:
                prob_atraso[num-1] = 0.1 # Never seen
        
        # Fusão
        prob_final = (prob_freq * 0.6) + (prob_atraso * 0.4)
        
        # Adiciona ruído estocástico para simular variância da IA Generativa
        ruido = np.random.normal(0, 0.05, 25)
        prob_final += ruido
        
        top_indices = prob_final.argsort()[::-1][:15]
        palpite_ia = set(top_indices + 1)
        acertos_ia = len(palpite_ia.intersection(target_numeros))
        premio_ia = calcular_premio(acertos_ia)
        
        # --- MODELO ALEATÓRIO ---
        palpite_random = set(random.sample(range(1, 26), 15))
        acertos_random = len(palpite_random.intersection(target_numeros))
        
        resultados_sim.append({
            "Concurso": target_rodada,
            "Real": sorted(list(target_numeros)),
            "IA_Palpite": sorted(list(palpite_ia)),
            "IA_Acertos": acertos_ia,
            "IA_Premio": premio_ia,
            "Random_Acertos": acertos_random
        })
        
    prog_bar.empty()
    return pd.DataFrame(resultados_sim)

def renderizar_tab_lab(df, n_dias):
    st.markdown("## 🧪 Laboratório de Backtest & Financeiro")
    st.markdown("Bem-vindo ao centro de pesquisa. Aqui você pode testar a eficácia da Inteligência Artificial contra Aleatoriedade, ou simular estratégias puras contra todo o histórico da Lotofácil.")
    
    t1, t2 = st.tabs(["⚔️ Batalha: IA vs Sorte", "📈 Simulador de Estratégias Genéricas"])
    
    with t1:
        st.markdown("### 🤖 Batalha Híbrida: Inteligência contra o Azar")
        qtd_sim = st.slider("Quantos concursos passados simular?", 3, 50, 10, key="slider_batalha") 
        custo_aposta = 3.50
        
        if st.button("Iniciar Simulação Militar (Backtest)", key="btn_batalha"):
            with st.spinner(f"Simulando {qtd_sim} jogos ($$). isso pode levar alguns segundos..."):
                df_res = executar_simulacao(df, n_dias, qtd_sim)
                
                if not df_res.empty:
                    # Financeiro IA
                    custo_total = qtd_sim * custo_aposta
                    ganho_total_ia = df_res['IA_Premio'].sum()
                    lucro_ia = ganho_total_ia - custo_total
                    
                    st.markdown("### 💵 Resultado Financeiro (IA)")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Investido", f"R$ {custo_total:,.2f}")
                    c2.metric("Retorno (Prêmios)", f"R$ {ganho_total_ia:,.2f}")
                    c3.metric("Lucro Líquido", f"R$ {lucro_ia:,.2f}", delta=f"{lucro_ia:,.2f}")
                    c4.metric("Média Acertos IA", f"{df_res['IA_Acertos'].mean():.1f}")
                    
                    st.markdown("---")
                    
                    st.markdown("### 🆚 Histórico Concurso a Concurso")
                    df_long = df_res.melt(id_vars=['Concurso'], value_vars=['IA_Acertos', 'Random_Acertos'], 
                                          var_name='Jogador', value_name='Acertos')
                    df_long['Jogador'] = df_long['Jogador'].replace({'IA_Acertos': '🤖 IA', 'Random_Acertos': '🎲 Aleatório'})
    
                    chart = alt.Chart(df_long).mark_bar().encode(
                        x=alt.X('Concurso:O', axis=alt.Axis(labelAngle=0)),
                        y='Acertos:Q',
                        color=alt.Color('Jogador', scale=alt.Scale(domain=['🤖 IA', '🎲 Aleatório'], range=['#2E86C1', '#BDC3C7'])),
                        xOffset='Jogador:N',
                        tooltip=['Concurso', 'Jogador', 'Acertos']
                    )
                    
                    rule = alt.Chart(pd.DataFrame({'y': [11]})).mark_rule(color='red', strokeDash=[5, 5]).encode(y='y')
                    st.altair_chart(chart + rule, width='stretch')
                    st.caption("A linha vermelha indica a zona de premiação (11 acertos).")
    
                    with st.expander("Ver detalhes dos jogos simulados"):
                        st.dataframe(df_res[['Concurso', 'IA_Acertos', 'Random_Acertos', 'IA_Premio', 'IA_Palpite']], width='stretch')
                else:
                    st.error("Dados insuficientes para simulação.")

    with t2:
        st.markdown("### 🔬 Teste de Estresse de Estratégias no Longo Prazo")
        st.write("Dúvida clássica: 'O que aconteceria se eu tivesse repetido a exata mesma Teoria Mágica ao longo de centenas de sorteios? A matemática quebra?'")
        
        estrategias = {
            "Teimosinha (Linha do Tempo Completa)": "Um bilhete fixo jogado contra todo o banco de dados.",
            "Apenas as 15 Mais Frequentes": "Recalcula a cada sorteio o top 15 de números que mais saíram antes dele e os joga.",
            "Apenas as Zebras Frias": "Recalcula a cada sorteio as 15 dezenas mais atrasadas e as marca no volante.",
            "Aleatório Absoluto": "Joga no modo 'Surpresinha', diferente a cada concurso."
        }
        
        estrategia_escolhida = st.selectbox("Escolha uma Teoria para testar:", list(estrategias.keys()), format_func=lambda x: f"{x} - {estrategias[x]}")
        
        default_nums = ""
        if 'ultima_previsao' in st.session_state and st.session_state.ultima_previsao:
            default_nums = ", ".join(map(str, sorted(st.session_state.ultima_previsao)))
            
        numeros_teimosia = st.text_input("Se escolheu Teimosinha, digite os 15 números (separados por vírgula):", value=default_nums)
        
        max_limit = len(df)
        periodo_teste = st.slider("Rodar a simulação contra os últimos X sorteios:", 50, max_limit, min(500, max_limit))
        custo_aposta = 3.50
        
        if st.button("Executar Simulação de Estratégia", key="btn_estrategia"):
            df_teste = df.tail(periodo_teste).copy()
            df_historico_base = df.head(len(df) - periodo_teste).copy() # Para o caso das mais frequentes (sem viagem no tempo)
            
            resultados_estrategia = []
            ganho_financeiro = 0.0
            
            with st.spinner("Varrendo a linha do tempo..."):
                prog_bar = st.progress(0)
                
                # Validação prévia de Teimosinha
                teimosinha_set = set()
                if "Teimosinha" in estrategia_escolhida:
                    try:
                         teimosinha_set = {int(x.strip()) for x in numeros_teimosia.replace(';', ',').replace(' ', ',').split(',') if x.strip()}
                         if len(teimosinha_set) != 15:
                             st.error(f"Sua teimosinha precisa ter EXATOS 15 números. Você indicou {len(teimosinha_set)}.")
                             st.stop()
                    except:
                         st.error("Formato inválido de números. Use vírgulas.")
                         st.stop()
                         
                curr_history = df_historico_base.copy()
                
                for idx, (_, row) in enumerate(df_teste.iterrows()):
                    prog_bar.progress((idx + 1) / periodo_teste)
                    alvo = set(row['numeros'])
                    
                    jogo_gerado = set()
                    if "Teimosinha" in estrategia_escolhida:
                        jogo_gerado = teimosinha_set
                    elif "Frequentes" in estrategia_escolhida:
                        todas_nums = []
                        for nums in curr_history['numeros']: todas_nums.extend(nums)
                        c = Counter(todas_nums)
                        top15 = [x[0] for x in c.most_common(15)]
                        jogo_gerado = set(top15)
                    elif "Zebras" in estrategia_escolhida:
                        # Contagem do tempo em que as bolas não saem
                        # Simplificado: as 15 que menos saíram genericamente pro teste rápido na memory history
                        todas_nums = []
                        for nums in curr_history['numeros']: todas_nums.extend(nums)
                        c = Counter(todas_nums)
                        # preenche os que nem saíram com 0
                        for i in range(1, 26):
                            if i not in c: c[i] = 0
                        frias15 = [x[0] for x in c.most_common()[:-16:-1]]
                        jogo_gerado = set(frias15)
                    elif "Aleatório" in estrategia_escolhida:
                        jogo_gerado = set(random.sample(range(1, 26), 15))
                        
                    acertos = len(jogo_gerado.intersection(alvo))
                    premio = calcular_premio(acertos)
                    ganho_financeiro += premio
                    
                    resultados_estrategia.append({
                        'Rodada': row['rodada'],
                        'Acertos': acertos,
                        'Premio': premio
                    })
                    
                    # Alimenta o histórico simulando a passagem do tempo passo a passo
                    curr_history = pd.concat([curr_history, pd.DataFrame([row])])
            
            prog_bar.empty()
            
            # Análise
            df_res_est = pd.DataFrame(resultados_estrategia)
            custo_total = periodo_teste * custo_aposta
            lucro_liquido = ganho_financeiro - custo_total
            roi = (lucro_liquido / custo_total) * 100 if custo_total > 0 else 0
            
            # Tabela de ocorrências de acertos
            count_premios = {11: 0, 12: 0, 13: 0, 14: 0, 15: 0}
            for a in df_res_est['Acertos']:
                if a in count_premios: count_premios[a] += 1
                
            st.success("🏁 Simulação Temporo-Mecânica Concluída!")
            
            c_e1, c_e2, c_e3, c_e4 = st.columns(4)
            c_e1.metric("Investimento Fictício", f"R$ {custo_total:,.2f}")
            c_e2.metric("Retorno Bruto", f"R$ {ganho_financeiro:,.2f}")
            c_e3.metric("Lucro (ou Prejuízo)", f"R$ {lucro_liquido:,.2f}", delta=f"{roi:.1f}% ROI")
            
            # Formatar ROI
            cor_roi = "green" if roi > 0 else "red"
            st.markdown(f"**Conclusão Financeira:** Com essa estratégia, você teria tido um <span style='color:{cor_roi}'>ROI de {roi:.2f}%</span> ao longo de {periodo_teste} sorteios.", unsafe_allow_html=True)
            
            st.markdown("### 🏆 Distribuição de Acertos Desse Método")
            st.write("Quantos bilhetes bateram no pódio de premiação?")
            cb1, cb2, cb3, cb4, cb5 = st.columns(5)
            cb1.metric("🎉 11 pontos", f"{count_premios[11]}x")
            cb2.metric("🎉 12 pontos", f"{count_premios[12]}x")
            cb3.metric("🔥 13 pontos", f"{count_premios[13]}x")
            cb4.metric("💎 14 pontos", f"{count_premios[14]}x")
            cb5.metric("👑 15 pontos", f"{count_premios[15]}x")
            
            st.markdown("### 📈 Gráfico de Acertos ao Longo do Tempo")
            c_line = alt.Chart(df_res_est).mark_circle(size=60).encode(
                x=alt.X('Rodada:O', axis=alt.Axis(labelAngle=0)),
                y=alt.Y('Acertos:Q', scale=alt.Scale(domain=[5, 15])),
                tooltip=['Rodada', 'Acertos', 'Premio'],
                color=alt.condition(alt.datum.Acertos >= 11, alt.value("green"), alt.value("gray"))
            ).properties(height=300)
            
            r_line = alt.Chart(pd.DataFrame({'y': [11]})).mark_rule(color='red', strokeDash=[2, 2]).encode(y='y')
            st.altair_chart(c_line + r_line, use_container_width=True)
            st.caption("Pontos verdes significam sorteios em que a estratégia devolveu dinheiro (acima de 11 acertos).")
