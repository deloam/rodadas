import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import altair as alt
import streamlit as st

def extrair_metricas_avancadas(numeros):
    """
    Retorna vetor de features para clusterização:
    [Soma, Ímpares, Primos, Moldura, Desvio Padrão, Amplitude Interquartil]
    """
    numeros = np.array(sorted(numeros))
    
    PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}
    MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
    
    soma = np.sum(numeros)
    impares = np.sum(numeros % 2 != 0)
    primos = sum(1 for x in numeros if x in PRIMOS)
    moldura = sum(1 for x in numeros if x in MOLDURA)
    std_dev = np.std(numeros) # Espalhamento
    
    # Q3 - Q1 (Concentração do miolo do jogo)
    q75, q25 = np.percentile(numeros, [75 ,25])
    iqr = q75 - q25
    
    return [soma, impares, primos, moldura, std_dev, iqr]

@st.cache_resource
def treinar_modelo_clusters(df_completo):
    """
    Treina o KMeans com todo o histórico para encontrar os arquétipos (famílias) de jogos.
    """
    # Preparar Dataset
    X = []
    for nums in df_completo['numeros']:
        X.append(extrair_metricas_avancadas(nums))
    
    X = np.array(X)
    
    # Normalizar (Importante pois Soma ~200 e Primos ~5 têm escalas muito diferentes)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # K=5 Famílias (Arquetipos)
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    kmeans.fit(X_scaled)
    
    # Atribuir nomes amigáveis às famílias com base nas características médias
    # Vamos analisar os centroides
    centers = scaler.inverse_transform(kmeans.cluster_centers_)
    # Features: 0:Soma, 1:Imp, 2:Pri, 3:Mol, 4:Std, 5:IQR
    
    familias = {}
    for i, center in enumerate(centers):
        soma_media = center[0]
        imp_media = center[1]
        
        # Naming Logic simples
        nome = f"Família {i+1}"
        desc = []
        
        if soma_media < 190: desc.append("Baixos")
        elif soma_media > 210: desc.append("Altos")
        else: desc.append("Equilibrados")
        
        if imp_media > 8.5: desc.append("Ímpares+")
        elif imp_media < 6.5: desc.append("Pares+")
        
        familias[i] = f"{nome} ({'/'.join(desc)})"
        
    return kmeans, scaler, X, familias

def renderizar_clusters(df):
    st.markdown("## 🧬 Clusterização Inteligente (Famílias de Jogos)")
    st.markdown("A IA analisou todo o histórico e dividiu os resultados em **5 Famílias (Arquétipos)** baseadas em suas características matemáticas.")
    
    if len(df) < 50:
        st.warning("Poucos dados para clusterização robusta.")
        return

    model, scaler, X_raw, nomes_familias = treinar_modelo_clusters(df)
    
    # Prever clusters para o histórico
    X_scaled = scaler.transform(X_raw)
    labels = model.predict(X_scaled)
    
    df_clusters = df.copy()
    df_clusters['cluster'] = labels
    df_clusters['nome_familia'] = df_clusters['cluster'].map(nomes_familias)
    
    # Analisar Último Jogo
    ultimo_idx = len(df) - 1
    cluster_ultimo = labels[ultimo_idx]
    
    c1, c2 = st.columns([2, 1])
    
    with c1:
        # Gráfico de Dispersão (Soma vs Ímpares colorido por Cluster)
        # É uma projeção 2D simples das famílias
        chart_data = df_clusters[['rodada', 'nome_familia']].copy()
        # Adicionar Soma e Impares do X_raw para plotar
        chart_data['Soma'] = X_raw[:, 0]
        chart_data['Impares'] = X_raw[:, 1]
        
        scatter = alt.Chart(chart_data).mark_circle(size=60).encode(
            x=alt.X('Soma', scale=alt.Scale(domain=[120, 280])),
            y=alt.Y('Impares', scale=alt.Scale(domain=[4, 13])),
            color=alt.Color('nome_familia', legend=alt.Legend(title="Família")),
            tooltip=['rodada', 'nome_familia', 'Soma', 'Impares']
        ).properties(
            title="Mapa das Famílias (Soma vs Ímpares)",
            height=300
        ).interactive()
        
        st.altair_chart(scatter, use_container_width=True)
        
    with c2:
        st.info(f"📍 **O Último Sorteio**  pertence à **{nomes_familias[cluster_ultimo]}**.")
        
        # Frequencia das famílias nos últimos 20 jogos
        st.markdown("**Tendência Recente (Últimos 20):**")
        recents = df_clusters.tail(20)['nome_familia'].value_counts()
        st.dataframe(recents, use_container_width=True)

    return model, scaler, nomes_familias
