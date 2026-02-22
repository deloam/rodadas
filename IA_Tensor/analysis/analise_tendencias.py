import streamlit as st
import pandas as pd
import altair as alt

def calcular_metricas(numeros):
    """Calcula usando o motor base centralizado."""
    from core.utils import calcular_metricas_dna
    m = calcular_metricas_dna(numeros)
    
    return {
        'Impares': m['impares'],
        'Primos': m['primos'],
        'Moldura': m['moldura'],
        'Fibo': m['fibo'],
        'Soma': m['soma']
    }

def analisar_tendencias_recentes(df, window=20):
    """
    Analisa os últimos 'window' concursos para identificar vieses/tendências
    que estejam desviando da normalidade estatística.
    """
    if len(df) < window:
        return None

    # Recorte recente
    df_recente = df.tail(window).copy()
    
    # Calcular métricas para cada jogo do recorte
    metricas_list = []
    for nums in df_recente['numeros']:
        metricas_list.append(calcular_metricas(nums))
        
    df_metrics = pd.DataFrame(metricas_list)
    
    # Médias Observadas vs Esperadas (Teóricas aproximadas para Lotofácil)
    referencias = {
        'Impares': {'teorico': 8.0, 'min': 7, 'max': 9, 'desc': 'Ímpares'},
        'Primos': {'teorico': 5.0, 'min': 4, 'max': 6, 'desc': 'Primos'},
        'Moldura': {'teorico': 10.0, 'min': 9, 'max': 11, 'desc': 'Moldura'},
        'Fibo': {'teorico': 4.0, 'min': 3, 'max': 5, 'desc': 'Fibonacci'},
        'Soma': {'teorico': 200.0, 'min': 180, 'max': 220, 'desc': 'Soma'}
    }
    
    insights = []
    
    for k, ref in referencias.items():
        media_obs = df_metrics[k].mean()
        desvio = media_obs - ref['teorico']
        
        # Analisar Desvios Significativos
        # Se desvio > 0.5 (significa que na média está saindo 0.5 a mais que o padrão)
        if abs(desvio) >= 0.5 or (k == 'Soma' and abs(desvio) > 10):
            estado = "🔥 ALTA" if desvio > 0 else "❄️ BAIXA"
            msg = f"Tendência de {estado} em {ref['desc']}"
            detalhe = f"Média Recente: {media_obs:.1f} (Padrão: {ref['teorico']})"
            
            # Avaliar se a tendência está 'Quente' (lucrativa seguir) ou 'Saturada'
            # Na loteria, tendências curtas costumam se manter (Hot Hand Fallacy works sometimes with physics/machines)
            # ou reverter à média (Gambler's Fallacy).
            # Vamos assumir reversão à média para segurança (Estratégia Conservadora)
            # Ou seguir tendência (Estratégia Agressiva).
            # Vamos apenas informar o fato.
            
            insights.append({
                'metrica': k,
                'estado': estado,
                'msg': msg,
                'valor': media_obs,
                'alvo': ref['teorico'],
                'detalhe': detalhe,
                'dica': f"Tente jogos com {ref['desc']} entre {int(media_obs)} e {int(media_obs)+1}." if desvio > 0 else f"Tente jogos com {ref['desc']} entre {int(media_obs)-1} e {int(media_obs)}."
            })
            
    return df_metrics, insights

def renderizar_detector_tendencias(df):
    st.markdown("## 📡 Detector de Tendências (Beta)")
    st.markdown("O sistema analisa os últimos 20 concursos para identificar **vieses estatísticos temporários**.")
    
    df_metrics, insights = analisar_tendencias_recentes(df, window=20)
    
    if not insights:
        st.success("✅ O mercado está estável. Nenhuma anomalia estatística detectada recentemente.")
        st.caption("Pode seguir os padrões clássicos (Ex: 8 Ímpares, 5 Primos, etc).")
    else:
        for item in insights:
            with st.expander(f"{item['estado']} - {item['metrica']} ({item['valor']:.1f})", expanded=True):
                st.write(item['msg'])
                st.caption(item['detalhe'])
                st.info(f"💡 **Sugestão:** {item['dica']}")
                
    st.markdown("---")
    
    # Gráfico de Evolução (Linha do Tempo)
    # Mostra como as métricas oscilaram nos ultimos jogos
    if df_metrics is not None:
        st.markdown("### 📈 Monitor de Oscilação (Últimos 20)")
        
        metrica_sel = st.selectbox("Escolha a métrica para visualizar:", ['Impares', 'Primos', 'Moldura', 'Fibo', 'Soma'])
        
        df_chart = df_metrics.reset_index()
        df_chart['Index'] = df_metrics.index + 1 # Apenas sequencial 1..20
        
        base = alt.Chart(df_chart).encode(x=alt.X('Index:O', title='Últimos Jogos (Recente -> Atual)', axis=alt.Axis(labelAngle=0)))
        
        line = base.mark_line(point=True, color='#e74c3c').encode(
            y=alt.Y(metrica_sel, scale=alt.Scale(zero=False), title=metrica_sel, axis=alt.Axis(tickMinStep=1, format='d')),
            tooltip=[metrica_sel]
        )
        
        # Linha de média teórica
        # Precisamos pegar o valor teórico do dicionario referencias (redefinindo rapido aqui ou passando como param)
        teorico_map = {'Impares': 8, 'Primos': 5, 'Moldura': 10, 'Fibo': 4, 'Soma': 200}
        val_teorico = teorico_map.get(metrica_sel, 0)
        
        rule = base.mark_rule(color='green', strokeDash=[5,5]).encode(y=alt.datum(val_teorico))
        
        st.altair_chart(line + rule, width='stretch')
        st.caption("Linha pontilhada verde = Padrão Teórico Matemático")
