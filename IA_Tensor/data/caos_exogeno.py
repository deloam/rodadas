import yfinance as yf
import pandas as pd
import numpy as np
import altair as alt
import streamlit as st
import datetime
from datetime import timedelta
import sqlite3

# Lista de Ativos Financeiros Relevantes (Bancos + Índices)
TICKERS = {
    'IBOV': '^BVSP',        # Índice Bovespa
    'DOLAR': 'BRL=X',       # Dólar Americano
    'ITUB4': 'ITUB4.SA',    # Itaú Unibanco (Maior Banco Privado)
    'BBDC4': 'BBDC4.SA',    # Bradesco
    'BBAS3': 'BBAS3.SA',    # Banco do Brasil
    'SANB11': 'SANB11.SA',  # Santander
    'BPAC11': 'BPAC11.SA',  # BTG Pactual
    'PETR4': 'PETR4.SA',    # Petrobras (Influência Econômica)
    'VALE3': 'VALE3.SA',    # Vale (Exportação)
    'CXSE3': 'CXSE3.SA',    # Caixa Seguridade (O mais próximo da CEF)
    'EWZ': 'EWZ',           # Termômetro Político (ETF Brasil)
    'LUA': 'LUMINOSIDADE'   # Ciclo Natural (0=Nova, 100=Cheia)
}

def init_db_financeiro():
    conn = sqlite3.connect("previsoes.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historico_financeiro (
        data TEXT,
        ticker TEXT,
        fechamento REAL,
        variacao REAL,
        PRIMARY KEY (data, ticker)
    )
    """)
    conn.commit()
    return conn

@st.cache_data(ttl=3600*12) # Cache de 12 horas
def sincronizar_dados_financeiros(data_inicio, data_fim):
    """
    Sincroniza os dados do Yahoo Finance com o SQLite local.
    Só baixa da internet os pregões que estão faltando na base de dados, economizando banda e tempo.
    Retorna dois DataFrames: df_precos, df_retornos
    """
    conn = init_db_financeiro()
    
    # 1. Carregar todo o histórico do BD local
    df_bd = pd.read_sql("SELECT * FROM historico_financeiro", conn)
    
    precisa_fetch = False
    fetch_inicio = data_inicio
    
    if df_bd.empty:
        precisa_fetch = True
    else:
        df_bd['data'] = pd.to_datetime(df_bd['data'])
        max_date_db = df_bd['data'].max()
        
        # O Fetch acontece se o DB estiver defasado em mais de 3 dias considerando o data_fim
        if pd.Timestamp(data_fim) - max_date_db > pd.Timedelta(days=3):
            precisa_fetch = True
            # Retorna 5 dias extras para garantir o cálculo de variação %
            fetch_inicio = (max_date_db - pd.Timedelta(days=5)).to_pydatetime()
            
    # 2. Busca na Internet (B3) só se estiver desatualizado
    if precisa_fetch:
        real_tickers = [v for k,v in TICKERS.items() if k != 'LUA']
        try:
            dados = yf.download(real_tickers, start=fetch_inicio, end=data_fim, progress=False, ignore_tz=True)['Close']
            
            if not dados.empty:
                retornos = dados.ffill().pct_change() * 100
                retornos.index = pd.to_datetime(retornos.index).tz_localize(None)
                dados.index = pd.to_datetime(dados.index).tz_localize(None)
                
                # Salvar os dias novos no SQLite Otimizado
                cursor = conn.cursor()
                for ticker_code in dados.columns:
                    ticker_nome = next((k for k, v in TICKERS.items() if v == ticker_code), ticker_code)
                        
                    series_preco = dados[ticker_code].dropna()
                    series_retorno = retornos[ticker_code].dropna()
                    datas_comuns = series_preco.index.intersection(series_retorno.index)
                    
                    for data in datas_comuns:
                        data_str = data.strftime("%Y-%m-%d")
                        p = float(series_preco.loc[data])
                        v = float(series_retorno.loc[data])
                        cursor.execute("INSERT OR REPLACE INTO historico_financeiro VALUES (?, ?, ?, ?)", 
                                       (data_str, ticker_nome, p, v))
                conn.commit()
                
                # Atualiza memória com dados novos do BD
                df_bd = pd.read_sql("SELECT * FROM historico_financeiro", conn)
                df_bd['data'] = pd.to_datetime(df_bd['data'])
        except Exception as e:
            st.warning(f"Não foi possível buscar atualizações do mercado online. Usando dados cacheados locais. Erro: {e}")

    conn.close()
    
    if df_bd.empty:
         return pd.DataFrame(), pd.DataFrame()
         
    # 3. Pivotar para formato esperado pelas métricas (colunas=Tickers, Index=Data)
    mapa_inverso = {k: v for k, v in TICKERS.items()}
    df_bd['ticker_code'] = df_bd['ticker'].map(mapa_inverso).fillna(df_bd['ticker'])
    
    # Recortar à janela solicitada
    df_janela = df_bd[(df_bd['data'] >= pd.to_datetime(data_inicio)) & (df_bd['data'] <= pd.to_datetime(data_fim))]
    
    df_precos = df_janela.pivot(index='data', columns='ticker_code', values='fechamento')
    df_retornos = df_janela.pivot(index='data', columns='ticker_code', values='variacao')
    
    return df_precos, df_retornos

def get_fase_lua_luminosidade(data):
    """
    Calcula a luminosidade da lua (0 a 100) para uma data.
    0 = Lua Nova, 100 = Lua Cheia.
    Ciclo médio: 29.53 dias.
    Base: Lua Nova em 06/01/2000.
    """
    LUA_NOVA_BASE = datetime.datetime(2000, 1, 6)
    delta = (data - LUA_NOVA_BASE).days
    dias_no_ciclo = delta % 29.53058867
    
    # Onda senoidal (0 -> 100 -> 0)
    # Cos vai de 1 a -1. Queremos Novo(0) em 0.
    # Ângulo 0 (Nova) -> Cos=1. (1-1)/2 = 0.
    # Ângulo PI (Cheia) -> Cos=-1. (1-(-1))/2 = 1.
    
    angulo = (dias_no_ciclo / 29.53058867) * 2 * np.pi
    luminosidade = (1 - np.cos(angulo)) / 2 * 100
    return luminosidade

def correlacionar_mercado_loteria(df_loto, df_mercado):
    """
    Cruza datas dos sorteios com fechamento do mercado e calcula impacto nas dezenas.
    """
    # Preparar Dados da Loteria
    # Criar uma matriz one-hot de Números Sorteados (Linhas=Datas, Colunas=1..25)
    records = []
    
    # Garantir datetime sem hora no df_loto
    df_loto['data_dt'] = pd.to_datetime(df_loto['data'])
    
    for idx, row in df_loto.iterrows():
        data_sorteio = row['data_dt']
        
        # Buscar dados de mercado (Do dia do sorteio ou dia anterior útil)
        # Tentar casar data exata, senão pega a última válida (ffill logic)
        # Mas para correlação justa, usamos apenas se tiver pregão no dia ou dia anterior
        # Se for Sábado (Sorteio), mercado fechado -> pega Sexta.
        
        # Vamos fazer merge asof depois
        numeros = row['numeros']
        # One Hot Vector temporário
        vetor = {f"num_{n}": 1 for n in range(1, 26)}
        vetor['data'] = data_sorteio
        
        # --- CÁLCULO FASE DA LUA (VARIÁVEL EXÓGENA SINTÉTICA) ---
        vetor['LUMINOSIDADE'] = get_fase_lua_luminosidade(data_sorteio)
        
        records.append(vetor)
        
    df_loto_matrix = pd.DataFrame(records).fillna(0)
    df_loto_matrix.set_index('data', inplace=True)
    
    # Merge Inteligente (ASOF) - Encontra a data de mercado mais próxima (anterior ou igual)
    # Porque o sorteio é a noite, e o pregão fecha 17h (ou pega fechamento anterior)
    df_mercado_sort = df_mercado.sort_index()
    df_loto_sort = df_loto_matrix.sort_index()
    
    # Merge
    df_final = pd.merge_asof(df_loto_sort, df_mercado_sort, left_index=True, right_index=True, direction='backward', tolerance=pd.Timedelta(days=3))
    
    # Remover linhas onde não achou dados de mercado (ex: feriados longos ou início da série)
    df_final.dropna(inplace=True)
    
    return df_final

def calcular_correlacao_exogena(df_final):
    """
    Calcula a matriz de correlação (Pearson) entre cada Ativo Financeiro e cada Dezena.
    """
    # Colunas de Ativos (tickers)
    cols_ativos = list(TICKERS.values())
    # Colunas de Números (num_1 a num_25)
    cols_numeros = [f"num_{i}" for i in range(1, 26)]
    
    # Filtrar apenas colunas que existem no df_final
    cols_ativos = [c for c in cols_ativos if c in df_final.columns]
    
    correlacoes = []
    
    for ativo in cols_ativos:
        for num_col in cols_numeros:
            # Correlação (Pearson) - Ignorar se não houver variação (std=0 ou NaN)
            std_ativo = df_final[ativo].std()
            std_num = df_final[num_col].std()
            
            if pd.isna(std_ativo) or std_ativo == 0 or pd.isna(std_num) or std_num == 0:
                corr = np.nan
            else:
                corr = df_final[ativo].corr(df_final[num_col])
            
            # Se correlação for NaN (sem variância), ignora
            if not pd.isna(corr):
                correlacoes.append({
                    'Ativo': [k for k, v in TICKERS.items() if v == ativo][0], # Nome legível
                    'Dezena': int(num_col.split('_')[1]),
                    'Correlação': corr
                })
                
    return pd.DataFrame(correlacoes)

def renderizar_caos_exogeno(df_loto):
    st.markdown("## 🌌 Caos Exógeno (Influência do Mercado Financeiro)")
    st.markdown("""
        Esta aba investiga a teoria da **Sincronicidade**: Será que o caos do mercado financeiro influencia a entropia do globo de sorteio?
        Aqui analisamos se altas/baixas de Bancos, Dólar e Bolsa "empurram" a probabilidade de certos números.
    """)
    
    # Definir Janela de Tempo (Para não baixar dados de 20 anos demorados, pegar ultimos 5 anos)
    data_fim = datetime.datetime.now()
    data_inicio = data_fim - timedelta(days=365*3) # 3 anos de análise
    
    with st.spinner("💸 Sincronizando com Base de Dados do Mercado (B3/Dólar)..."):
        df_precos, df_mercado = sincronizar_dados_financeiros(data_inicio, data_fim)
    
    if df_mercado.empty:
        st.warning("Não foi possível carregar dados financeiros. Verifique conexão.")
        return

    # Filtrar loteria para mesmo período
    df_loto_recorte = df_loto[df_loto['data'] >= pd.to_datetime(data_inicio)].copy()
    
    # Cruzar Dados
    df_full = correlacionar_mercado_loteria(df_loto_recorte, df_mercado)
    
    # Calcular Correlações
    df_corr = calcular_correlacao_exogena(df_full)
    
    if df_corr.empty:
        st.info("Dados insuficientes para correlação.")
        return

    # --- VISUALIZAÇÃO 1: MATRIX DE CALOR (HEATMAP) ---
    st.subheader("🌡️ Matriz de Influência (Ativo vs Dezena)")
    st.caption("Vermelho: O ativo 'Derruba' a chance da dezena. Azul: O ativo 'Aumenta' a chance.")
    
    # Pivotar para Heatmap
    heatmap = alt.Chart(df_corr).mark_rect().encode(
        x=alt.X('Dezena:O', title='Dezena da Lotofácil'),
        y=alt.Y('Ativo:N', title='Ativo Financeiro'),
        color=alt.Color('Correlação:Q', scale=alt.Scale(scheme='redblue', domain=[-0.15, 0.15])),
        tooltip=['Ativo', 'Dezena', alt.Tooltip('Correlação', format='.3f')]
    ).properties(
        width=700,
        height=300
    )
    st.altair_chart(heatmap, width='stretch')
    
    # --- VISUALIZAÇÃO 2: TOP OPORTUNIDADES ---
    st.subheader("💎 Oportunidades de Ouro (Correlações Fortes)")
    
    # Filtrar Correlações Significativas (Top 5 Positivas e Top 5 Negativas)
    top_pos = df_corr.nlargest(5, 'Correlação')
    top_neg = df_corr.nsmallest(5, 'Correlação')
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("**🚀 Impulsionadores (Jogar quando Ativo SOBE)**")
        for _, row in top_pos.iterrows():
            st.success(f"Quando **{row['Ativo']}** sobe, a dezena **{row['Dezena']:02d}** tende a sair! (Corr: {row['Correlação']:.3f})")
            
    with c2:
        st.markdown("**🛑 Bloqueadores (Evitar quando Ativo SOBE)**")
        for _, row in top_neg.iterrows():
            st.error(f"Quando **{row['Ativo']}** sobe, a dezena **{row['Dezena']:02d}** tende a falhar. (Corr: {row['Correlação']:.3f})")
    
    # --- SIMULADOR DE HOJE ---
    st.markdown("---")
    st.subheader("🔮 Oráculo de Hoje")
    st.caption("Como fechou o mercado hoje? Simule abaixo para ver quais números estão 'energizados'.")
    
    col_sim1, col_sim2 = st.columns([1, 2])
    
    with col_sim1:
        ativo_sel = st.selectbox("Escolha um Ativo Guia:", list(TICKERS.keys()))
        variacao = st.slider(f"Variação do {ativo_sel} hoje (%):", -5.0, 5.0, 1.0)
    
    with col_sim2:
        # Filtrar correlações desse ativo
        df_ativo = df_corr[df_corr['Ativo'] == ativo_sel]
        
        # Calcular "Força" projetada para cada número
        # Força = Correlação * Variação
        df_ativo['Forca_Projetada'] = df_ativo['Correlação'] * variacao
        
        # Top 5 sugeridos para hoje
        sugestao = df_ativo.nlargest(5, 'Forca_Projetada')
        
        st.markdown(f"### Números Sugeridos pelo {ativo_sel}:")
        
        cols = st.columns(5)
        for i, (_, row) in enumerate(sugestao.iterrows()):
            cols[i].metric(f"Bola {row['Dezena']}", f"{row['Forca_Projetada']:.2f}")
            
    return df_full
