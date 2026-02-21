import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

def plotar_radar_equilibrio(metrics):
    """
    Gera um gráfico de Radar (Spider Chart) usando Altair (Simulado com coordenadas polares ou barras radiais).
    Plotly seria ideal, mas vamos usar Altair para manter consistência sem novas dependencias pesadas se possível.
    
    Metrics input expected: dict with {Impares, Primos, Moldura, Fibo, Soma}
    """
    # Normalização (0 a 100%) em relação ao ideal
    # Eixo X: Categorias
    # Eixo Y: Score (0 a 100)
    
    # Metas
    metas = {
        'Ímpares': 8,
        'Primos': 5,
        'Moldura': 10,
        'Fibo': 4,
        'Soma': 200 # Soma será escalada diferente
    }
    
    # Calcular % de Precisão para cada
    # Fórmula: 100 - abs(Real - Meta) * Penalidade
    
    scores = []
    
    # 1. Impares (Meta 8. Se for 8 -> 100. Se for 4 -> 0. Se for 12 -> 0)
    diff_imp = abs(metrics['impares'] - metas['Ímpares'])
    score_imp = max(0, 100 - (diff_imp * 20)) # Cada desvio tira 20 pontos
    scores.append({'Métrica': 'Ímpares', 'Score': score_imp})
    
    # 2. Primos (Meta 5)
    diff_pri = abs(metrics['primos'] - metas['Primos'])
    score_pri = max(0, 100 - (diff_pri * 20))
    scores.append({'Métrica': 'Primos', 'Score': score_pri})
    
    # 3. Moldura (Meta 10)
    diff_mol = abs(metrics['moldura'] - metas['Moldura'])
    score_mol = max(0, 100 - (diff_mol * 15))
    scores.append({'Métrica': 'Moldura', 'Score': score_mol})
    
    # 4. Fibo (Meta 4)
    diff_fib = abs(metrics['fibo'] - metas['Fibo'])
    score_fib = max(0, 100 - (diff_fib * 25))
    scores.append({'Métrica': 'Fibonacci', 'Score': score_fib})
    
    # 5. Soma (Meta 200. Tolerancia +/- 20 é 100%)
    # Vamos simplificar: desvio absoluto sobre 200
    diff_soma = abs(metrics['soma'] - 200)
    # Se diff <= 10 -> 100. Se diff 30 -> 50.
    if diff_soma <= 10: score_soma = 100
    else: score_soma = max(0, 100 - ((diff_soma - 10) * 2))
    scores.append({'Métrica': 'Soma', 'Score': score_soma})

    df_radar = pd.DataFrame(scores)

    # Visualização Radial (Barra Circular) - Estilo Apple Watch Activity Rings ou parecido
    # Altair não tem Radar nativo fácil. Vamos fazer um Gráfico de Barras Polar ou Barras Normais Estilizadas.
    # Barras Normais são mais fáceis de ler que Radar as vezes.
    # Mas o usuário pediu "Radar". Vamos tentar usar `st.plotly_chart` se disponível, se não Altair.
    # Vou fazer Altair Bar Chart estilizado "Equalizer" que é muito intuitivo.
    
    # Ajuste de Cor baseado na nota
    df_radar['Cor'] = df_radar['Score'].apply(lambda x: '#2ecc71' if x >= 80 else ('#f1c40f' if x >= 50 else '#e74c3c'))
    
    # Gráfico de Barras Vertical Robusto
    base = alt.Chart(df_radar).encode(
        x=alt.X('Métrica:N', axis=alt.Axis(title=None, labelAngle=0, labelFontSize=12)),
        y=alt.Y('Score:Q', scale=alt.Scale(domain=[0, 110]), axis=None),
        color=alt.Color('Cor', scale=None),
        tooltip=['Métrica', 'Score']
    )
    
    bars = base.mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).properties(width=45)
    
    text = base.mark_text(dy=-10, color='white', size=14, fontWeight='bold').encode(
        text=alt.Text('Score', format='d'),
        y=alt.Y('Score:Q') # Posiciona na altura da barra
    )

    chart = (bars + text).properties(
        title="🛡️ Nível de Perfeição (0-100)",
        height=180
    )
    
    st.altair_chart(chart, width='stretch')
