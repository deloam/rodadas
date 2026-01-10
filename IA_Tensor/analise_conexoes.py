import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

def renderizar_mapa_conexoes(df):
    st.markdown("---")
    st.markdown("## 🕸️ Mapa de Conexões (Correlação)")
    st.markdown("Descubra as **'Panelinhas'** e as **'Rivalidades'**. Quais números gostam de sair juntos e quais se evitam?")

    # 1. Construir Matriz de Co-ocorrência
    # Vamos calcular: Dado que X saiu, qual a % de vezes que Y também saiu? (Probabilidade Condicional)
    # Mas para o Heatmap simétrico, melhor usar Correlação de Pearson ou Co-ocorrência Simples normalizada.
    # Vamos usar Co-ocorrência Simples para ser fácil de entender.
    
    n_concursos = len(df)
    matriz = np.zeros((26, 26)) # 1 a 25 (usaremos indices 1-25)
    
    # Preencher contagens
    for nums in df['numeros']:
        for n1 in nums:
            for n2 in nums:
                if n1 != n2:
                    matriz[n1][n2] += 1
                    
    # Converter para Porcentagem (Probabilidade de Par)
    # Ex: Se '1' saiu 100 vezes, e '1 e 2' saíram juntos 80 vezes -> Força = 80% (mas isso é condicional)
    # Se normalizarmos pelo TOTAL de concursos, temos a frequencia absoluta do par.
    
    # Para o Heatmap, vamos normalizar pelo Máximo de ocorrências de Pares para ter contraste
    max_val = np.max(matriz)
    
    # Preparar dados para Altair (Long Format)
    heatmap_data = []
    conexoes_list = []
    
    for i in range(1, 26):
        for j in range(1, 26):
            if i == j: continue
            
            count = matriz[i][j]
            # Normalização (0 a 100 de força relativa)
            strength = (count / n_concursos) * 100 
            
            heatmap_data.append({
                'Num A': i,
                'Num B': j,
                'Força': count,
                'Frequência (%)': round((count / n_concursos) * 100, 1)
            })
            
            # Só adiciona na lista se i < j para não duplicar (1-2 e 2-1)
            if i < j:
                conexoes_list.append({
                    'Par': f"{i:02d} - {j:02d}",
                    'Num A': i,
                    'Num B': j,
                    'Juntos': int(count),
                    'Freq': (count / n_concursos) * 100
                })

    df_heat = pd.DataFrame(heatmap_data)
    
    with st.expander("📊 Visualizar Matriz Completa (Heatmap)", expanded=True):
        st.caption("Quanto mais **vermelho**, mais os números aparecem juntos. Quanto mais **azul**, mais se evitam.")
        
        # Heatmap
        chart = alt.Chart(df_heat).mark_rect().encode(
            x=alt.X('Num A:O', title='Número A'),
            y=alt.Y('Num B:O', title='Número B'),
            color=alt.Color('Frequência (%):Q', scale=alt.Scale(scheme='redblue', reverse=True), legend=None),
            tooltip=['Num A', 'Num B', 'Frequência (%)', 'Força']
        ).properties(
            width=600,
            height=600
        )
        st.altair_chart(chart, use_container_width=True)

    # --- TOP AMIGOS E INIMIGOS ---
    df_conexoes = pd.DataFrame(conexoes_list)
    df_conexoes = df_conexoes.sort_values('Freq', ascending=False)
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("### 🤝 Melhores Amigos (Sinergia)")
        st.caption("Pares que saíram juntos mais vezes na história selecionada.")
        top_10 = df_conexoes.head(10)
        for i, row in top_10.iterrows():
            st.markdown(f"**{row['Par']}**: {row['Freq']:.1f}% das vezes")
            # Barra de progresso visual simples
            st.progress(int(row['Freq'])/100)

    with c2:
        st.markdown("### ⚔️ Inimigos (Repulsão)")
        st.caption("Pares que raramente se encontram.")
        bot_10 = df_conexoes.tail(10) # Já está sorted desc, então tail são os menores
        for i, row in bot_10.iloc[::-1].iterrows(): # Inverter para mostrar o menor primeiro
            st.markdown(f"**{row['Par']}**: Apenas {row['Freq']:.1f}%")
            st.progress(int(row['Freq'])/100)
            
    # --- BUSCADOR DE PARCERIAS ---
    st.markdown("#### 🔎 Analisar um Número Específico")
    num_alvo = st.number_input("Veja quem combina com o número:", min_value=1, max_value=25, value=1)
    
    # Filtrar conexões deste numero
    meus_amigos = df_conexoes[(df_conexoes['Num A'] == num_alvo) | (df_conexoes['Num B'] == num_alvo)].copy()
    # Ajustar para mostrar sempre o outro numero
    meus_amigos['Parceiro'] = np.where(meus_amigos['Num A'] == num_alvo, meus_amigos['Num B'], meus_amigos['Num A'])
    meus_amigos = meus_amigos.sort_values('Freq', ascending=False)
    
    best = meus_amigos.iloc[0]
    worst = meus_amigos.iloc[-1]
    
    st.info(f"O **Melhor Parceiro** do {num_alvo} é o **{int(best['Parceiro'])}** (saem juntos em {best['Freq']:.1f}% dos jogos).")
    st.warning(f"O **Pior Parceiro** do {num_alvo} é o **{int(worst['Parceiro'])}** (só se encontram em {worst['Freq']:.1f}%).")
