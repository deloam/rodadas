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
    from core.utils import calcular_metricas_dna
    nums = sorted(list(numeros))
    m = calcular_metricas_dna(nums)
    soma = m['soma']
    imp = m['impares']
    pri = m['primos']
    mol = m['moldura']
    
    # Métricas de dispersão (distribuição no volante)
    std = np.std(nums)
    iqr = np.percentile(nums, 75) - np.percentile(nums, 25)
    
    return [soma, imp, pri, mol, std, iqr]

@st.cache_data
def treinar_modelo_clusters(numeros_historico):
    """
    Treina o KMeans com todo o histórico para encontrar os arquétipos (famílias) de jogos.
    """
    # Preparar Dataset
    X = []
    for nums in numeros_historico:
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
    familias_detalhes = {}
    for i, center in enumerate(centers):
        soma_media = round(center[0])
        imp_media = round(center[1])
        primos_media = round(center[2])
        moldura_media = round(center[3])
        
        # Naming Logic simples
        nome = f"Família {i+1}"
        desc = []
        
        if soma_media < 190: desc.append("Baixos")
        elif soma_media > 210: desc.append("Altos")
        else: desc.append("Equilibrados")
        
        if imp_media >= 9: desc.append("Ímpares+")
        elif imp_media <= 6: desc.append("Pares+")
        
        familias[i] = f"{nome} ({'/'.join(desc)})"
        
        # Detalhamento rico para legenda
        detalhe = f"**{familias[i]}**: Jogos com Soma média de **{soma_media}** e cerca de **{imp_media}** Ímpares. "
        if primos_media >= 6: detalhe += f"Tendência a ter cerca de {primos_media} Primos. "
        if moldura_media >= 11: detalhe += f"Destaque para {moldura_media} números na Moldura. "
        familias_detalhes[i] = detalhe
        
    return kmeans, scaler, X, familias, familias_detalhes

def renderizar_clusters(df):
    st.markdown("## 🧬 Clusterização Inteligente (Famílias de Jogos)")
    st.markdown("A IA analisou todo o histórico e dividiu os resultados em **5 Famílias (Arquétipos)** baseadas em suas características matemáticas.")
    
    if len(df) < 50:
        st.warning("Poucos dados para clusterização robusta.")
        return

    # Converter 'numeros' para tupla de tuplas para ser hashable pelo st.cache_data
    numeros_tuple = tuple(tuple(x) for x in df['numeros'])
    model, scaler, X_raw, nomes_familias, detalhes_familias = treinar_modelo_clusters(numeros_tuple)
    
    # Prever clusters para o histórico
    X_scaled = scaler.transform(X_raw)
    labels = model.predict(X_scaled)
    
    df_clusters = df.copy()
    df_clusters['cluster'] = labels
    df_clusters['nome_familia'] = df_clusters['cluster'].map(nomes_familias)
    
    # Adicionar métricas ao DF antes de filtrar (Evita erro de índice)
    df_clusters['Soma'] = X_raw[:, 0]
    df_clusters['Impares'] = X_raw[:, 1]
    
    # --- Enriquecimento Temporal ---
    # Helper Estações Hemisfério Sul
    def get_estacao(data):
        dia = data.day
        mes = data.month
        if (mes == 3 and dia >= 21) or (mes in [4, 5]) or (mes == 6 and dia < 21): return "Outono"
        if (mes == 6 and dia >= 21) or (mes in [7, 8]) or (mes == 9 and dia < 23): return "Inverno"
        if (mes == 9 and dia >= 23) or (mes in [10, 11]) or (mes == 12 and dia < 21): return "Primavera"
        return "Verão"

    # Garantir datetime
    if not pd.api.types.is_datetime64_any_dtype(df_clusters['data']):
        df_clusters['data'] = pd.to_datetime(df_clusters['data'])

    df_clusters['dia_semana_nome'] = df_clusters['data'].dt.day_name(locale='pt_BR') # Requer locale, fallback english se falhar
    # Mapeamento manual para garantir PT-BR sem depender de locale do sistema
    dias_map = {
        0: '2ª Feira', 1: '3ª Feira', 2: '4ª Feira', 3: '5ª Feira', 
        4: '6ª Feira', 5: 'Sábado'
    }
    df_clusters['dia_semana'] = df_clusters['data'].dt.dayofweek.map(dias_map)
    df_clusters = df_clusters[df_clusters['dia_semana'].notna()]
    df_clusters['mes_nome'] = df_clusters['data'].dt.month.apply(lambda x: f"{x:02d}")
    df_clusters['trimestre'] = df_clusters['data'].dt.quarter.apply(lambda x: f"{x}º Trim")
    df_clusters['ano'] = df_clusters['data'].dt.year.astype(str)
    df_clusters['estacao'] = df_clusters['data'].apply(get_estacao)
    df_clusters['paridade_dia'] = df_clusters['data'].dt.day.apply(lambda x: "Dia Par" if x % 2 == 0 else "Dia Ímpar")

    # Analisar Último Jogo
    ultimo_idx = len(df) - 1
    cluster_ultimo = labels[ultimo_idx]
    
    c1, c2 = st.columns([2, 1])
    
    with c1:
        # Gráfico de Dispersão (Soma vs Ímpares colorido por Cluster)
        chart_data = df_clusters[['rodada', 'nome_familia', 'Soma', 'Impares']].copy()
        
        scatter = alt.Chart(chart_data).mark_circle(size=60).encode(
            x=alt.X('Soma', scale=alt.Scale(domain=[120, 280])),
            y=alt.Y('Impares', scale=alt.Scale(domain=[4, 13])),
            color=alt.Color('nome_familia', legend=alt.Legend(title="Família")),
            tooltip=['rodada', 'nome_familia', 'Soma', 'Impares']
        ).properties(
            title="Mapa das Famílias (Soma vs Ímpares)",
            height=300
        ).interactive()
        
        st.altair_chart(scatter, width='stretch')
        
    with c2:
        st.info(f"📍 **O Último Sorteio**  pertence à **{nomes_familias[cluster_ultimo]}**.")
        st.markdown("**Tendência Recente (Últimos 20):**")
        recents = df_clusters.tail(20)['nome_familia'].value_counts()
        st.dataframe(recents, width='stretch')

    # Legenda Detalhada
    with st.expander("📖 Dicionário das Famílias (Entenda cada Grupo)", expanded=False):
        for k, v in detalhes_familias.items():
            st.markdown(f"- {v}")

    st.markdown("---")
    st.markdown("### 📅 Sazonalidade das Famílias")
    st.caption("Descubra se certas famílias de jogos preferem dias específicos, estações ou períodos do ano.")

    # Filtro de Janela de Tempo
    min_year = int(df_clusters['data'].dt.year.min())
    max_year = int(df_clusters['data'].dt.year.max())
    
    col_t1, col_t2 = st.columns([2, 1])
    year_range = col_t1.slider("Janela de Análise (Anos):", min_year, max_year, (min_year, max_year))
    
    # Aplicar Filtro de Tempo
    df_sazonal = df_clusters[
        (df_clusters['data'].dt.year >= year_range[0]) & 
        (df_clusters['data'].dt.year <= year_range[1])
    ].copy()

    if len(df_sazonal) < 20:
        st.warning(f"⚠️ Atenção: Apenas {len(df_sazonal)} jogos encontrados no período de {year_range[0]} a {year_range[1]}. Os resultados podem não ser estatisticamente confiáveis. Tente ampliar a janela.")
    
    tipo_analise = st.radio(
        "Agrupar por:",
        ["Dia da Semana", "Estação do Ano", "Par/Ímpar (Dia)", "Mês", "Trimestre", "Ano"],
        horizontal=True
    )

    mapa_coluna = {
        "Dia da Semana": "dia_semana",
        "Estação do Ano": "estacao",
        "Par/Ímpar (Dia)": "paridade_dia",
        "Mês": "mes_nome",
        "Trimestre": "trimestre",
        "Ano": "ano"
    }

    col_tempo = mapa_coluna[tipo_analise]

    # Criar um Heatmap de Contagem (Mais fácil de ler que barras empilhadas)
    # Agrupar para ter os totais usando o DF filtrado
    df_agg = df_sazonal.groupby([col_tempo, 'nome_familia']).size().reset_index(name='count')
    
    if df_agg.empty:
        st.info("Nenhum dado disponível para os filtros selecionados.")
    else:
        heatmap = alt.Chart(df_agg).mark_rect().encode(
            x=alt.X(f"{col_tempo}:O", title=tipo_analise, axis=alt.Axis(labelAngle=0 if tipo_analise != "Mês" else -45)),
            y=alt.Y('nome_familia:N', title="Família"),
            color=alt.Color('count:Q', scale=alt.Scale(scheme='lightmulti'), legend=alt.Legend(title="Qtd Jogos")),
            tooltip=[col_tempo, 'nome_familia', 'count']
        ).properties(
            height=320,
            title=f"Mapa de Calor: Ocorrências de Famílias por {tipo_analise}"
        )

        # Adicionar texto com o número exato para máxima clareza
        text = heatmap.mark_text(baseline='middle').encode(
            text='count:Q',
            color=alt.condition(
                alt.datum.count > (df_agg['count'].max() / 2),
                alt.value('white'),
                alt.value('black')
            )
        )

        st.altair_chart(heatmap + text, width='stretch')

        # Adicionar um Insight resumido
        # Encontrar o maior valor por coluna (período selecionado)
        idx_max = df_agg.groupby(col_tempo)['count'].idxmax()
        destaques = df_agg.loc[idx_max].sort_values('count', ascending=False).head(3)
        
        st.markdown("#### 💡 Insights de Sazonalidade")
        cols_ins = st.columns(len(destaques))
        for i, (_, row) in enumerate(destaques.iterrows()):
            cols_ins[i].metric(
                label=f"Dominante em {row[col_tempo]}",
                value=row['nome_familia'].split(" (")[0],
                delta=f"{row['count']} jogos"
            )

    return model, scaler, nomes_familias
