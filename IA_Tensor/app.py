import streamlit as st
import pandas as pd
import json
from datetime import datetime
from ai.lstm import preparar_dados, treinar_modelo, prever_proxima_rodada
from analysis.analise_padroes import renderizar_analise_padroes, renderizar_ciclos
import numpy as np
import os
from keras.models import load_model, save_model
from collections import Counter
from ui.desdobramento import renderizar_tab_desdobramento
from analysis.backtest import renderizar_tab_lab
import altair as alt
from data.atualizador import atualizar_dados
import random
from ai.ensemble import treinar_ensemble, prever_ensemble # Segundo Cérebro
from analysis.analise_temporal import renderizar_analise_temporal
from ui.montador import renderizar_montador_manual
from analysis.analise_conexoes import renderizar_mapa_conexoes
from data.historico_previsoes import salvar_previsoes_detalhadas, renderizar_historico_previsoes_tab, executar_retro_analise, sincronizar_resultados
from ui.dashboard_resumo import renderizar_dashboard_resumo
from analysis.analise_tendencias import renderizar_detector_tendencias 
from ai.ia_critica import analisar_riscos_jogo
from ui.visualizacao import plotar_radar_equilibrio
from analysis.smart_clustering import renderizar_clusters
from ui.manual import renderizar_manual_instrucoes
from data.caos_exogeno import renderizar_caos_exogeno
from ui.tab_previsao import renderizar_tab_previsao
from ai.engine import AIEngine

from ai.evolutiva import renderizar_tab_evolutiva



# ... (rest of imports/functions) ...

from core.data_loader import carregar_dados, extrair_features, preencher_frequencias, contar_frequencias

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

tab_manual, tab_previsao, tab_evolutiva, tab_analise, tab_montador, tab_desdobra, tab_lab, tab_caos = st.tabs(["📘 Manual", "🔮 Previsão", "🧬 IA Evolutiva", "📊 Análise", "🏗️ Montador", "🔢 Desdobrador", "🧪 Laboratório", "🌌 Caos Exógeno"])


# Filtrar dados para análise baseado no sidebar definido acima
df_filtrado_analise = df[(df['data'] >= pd.to_datetime(data_inicial)) & (df['data'] <= pd.to_datetime(data_final))].reset_index(drop=True)

with tab_manual:
    renderizar_manual_instrucoes()

with tab_evolutiva:
    renderizar_tab_evolutiva(df)


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
    renderizar_tab_previsao(
        df=df,
        df_filtrado_analise=df_filtrado_analise,
        sequencia_correta_auto=sequencia_correta_auto,
        concurso_str=concurso_str,
        usar_aprendizado=usar_aprendizado,
        salvar_aprendizado=salvar_aprendizado,
        qtd_sequencias=qtd_sequencias,
        qtd_numeros=qtd_numeros,
        n_dias=int(n_dias),
        nums_fixos_str=nums_fixos_str,
        nums_excluidos_str=nums_excluidos_str
    )
