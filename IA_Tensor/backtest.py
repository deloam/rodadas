import streamlit as st
import pandas as pd
import numpy as np
from lstm import preparar_dados, treinar_modelo
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
    st.markdown("Simule jogos passados e compare: **Sua IA Inteligente** vs **Sorte Pura (Aleatória)**.")
    
    qtd_sim = st.slider("Quantos concursos passados simular?", 3, 50, 10) # Aumentei range
    custo_aposta = 3.50
    
    if st.button("Iniciar Simulação (Backtest)"):
        with st.spinner(f"Simulando {qtd_sim} jogos ($$). isso pode levar alguns segundos..."):
            df_res = executar_simulacao(df, n_dias, qtd_sim)
            
            if not df_res.empty:
                # Financeiro IA
                custo_total = qtd_sim * custo_aposta
                ganho_total_ia = df_res['IA_Premio'].sum()
                lucro_ia = ganho_total_ia - custo_total
                
                # Exibir Métricas Financeiras
                st.markdown("### 💵 Resultado Financeiro (IA)")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Investido", f"R$ {custo_total:,.2f}")
                c2.metric("Retorno (Prêmios)", f"R$ {ganho_total_ia:,.2f}")
                c3.metric("Lucro Líquido", f"R$ {lucro_ia:,.2f}", delta=f"{lucro_ia:,.2f}")
                c4.metric("Média Acertos IA", f"{df_res['IA_Acertos'].mean():.1f}")
                
                st.markdown("---")
                
                # Gráfico Comparativo IA vs Random
                st.markdown("### 🆚 Batalha: IA vs Aleatório")
                
                # Transformar dados para formato longo (tidy) para o Altair agrupar
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
                
                # Linha de 11 pontos (Premiação Mínima)
                rule = alt.Chart(pd.DataFrame({'y': [11]})).mark_rule(color='red', strokeDash=[5, 5]).encode(y='y')
                
                st.altair_chart(chart + rule, use_container_width=True)
                st.caption("A linha vermelha indica a zona de premiação (11 acertos).")

                # Tabela detalhada
                with st.expander("Ver detalhes dos jogos simulados"):
                    st.dataframe(df_res[['Concurso', 'IA_Acertos', 'Random_Acertos', 'IA_Premio', 'IA_Palpite']], use_container_width=True)
            else:
                st.error("Dados insuficientes para simulação.")
