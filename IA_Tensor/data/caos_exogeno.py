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
    'BTC': 'BTC-USD',       # Cripto e Ganância Global (Bitcoin)
    'VIX': '^VIX',          # Índice Global do Medo e Pânico
    'LUA': 'LUMINOSIDADE',  # Ciclo Natural (0=Nova, 100=Cheia)
    'PAGAMENTO': 'SALARIO', # Distância para dia útil de 5 ou 20
    'GOLS_BR': 'GOLS_ONTEM',# Gols Totais no Dia Anterior (Série A/B/Copa)
    'FLA': 'FLAMENGO_ONTEM',# Flamengo Vitória/Derrota (-1, 0, 1)
    'PAL': 'PALMEIRAS_ONTEM',
    'SAO': 'SAO_PAULO_ONTEM',
    'COR': 'CORINTHIANS_ONTEM'
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
        # Apenas os tickers REAIS que buscam da API.
        ativos_reais = ['IBOV', 'DOLAR', 'ITUB4', 'BBDC4', 'BBAS3', 'SANB11', 'BPAC11', 'PETR4', 'VALE3', 'CXSE3', 'EWZ', 'BTC', 'VIX']
        real_tickers = [TICKERS[a] for a in ativos_reais]
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

def get_forca_pagamento(data):
    """
    Calcula uma 'Força' de 0 a 100 baseada na proximidade dos dias de pagamento
    (dia 5 e dia 20 do mês). Simula o volume de apostadores amadores nas lotéricas.
    """
    data = pd.to_datetime(data)
    dia = data.day
    
    # Calcular distância em dias para o 5 ou o 20 mais próximo.
    d1 = abs(dia - 5)
    d2 = abs(dia - 20)
    
    dist_min = min(d1, d2)
    
    # Correção para virada de mês
    if dia > 25: 
        dist_min = min(dist_min, abs(30 - dia) + 5)
    elif dia < 5:
        dist_min = min(dist_min, abs(dia + 10)) # ex dia 1 -> dist pro dia 20 passado = 11. (simplificado)
        dist_min = min(dist_min, abs(5 - dia))
        
    # Pontuação max 100 (exatamente no dia), cai 15 pts por dia distante. zera em 7 dias.
    forca = max(0, 100 - (dist_min * 15))
    return forca



from data.futebol_stats import sincronizar_futebol

def correlacionar_mercado_loteria(df_loto, df_mercado):
    """
    Cruza datas dos sorteios com fechamento do mercado e calcula impacto nas dezenas.
    """
    # Preparar Dados da Loteria
    # Criar uma matriz one-hot de Números Sorteados (Linhas=Datas, Colunas=1..25)
    records = []
    
    # Garantir datetime sem hora no df_loto
    df_loto['data_dt'] = pd.to_datetime(df_loto['data'])
    
    # 0. Sincronizar Calendário de Futebol Oficial (ESPN API)
    # Lista de datas no formato YYYYMMDD do Dia Anterior
    df_loto['data_ontem'] = pd.to_datetime(df_loto['data']) - pd.Timedelta(days=1)
    datas_yyyymmdd = df_loto['data_ontem'].dt.strftime('%Y%m%d').tolist()
    
    # Progress bar para tranquilizar usuário caso seja a primeira vez
    progress_bar = None
    if 'st' in globals() and hasattr(st, 'progress'):
        # Só cria se estiver no contexto da aplicação
        try: progress_bar = st.progress(0, text="Sincronizando Placar de Futebol (ESPN)...")
        except: pass
        
    df_futebol = sincronizar_futebol(datas_yyyymmdd, barra_progresso=progress_bar)
    
    if progress_bar: progress_bar.empty()
    
    # Converter para dicionário para O(1) fetch
    # { '20230813': {'gols_total': 18, 'fla_status': 1, ...} }
    dict_fut = df_futebol.set_index('data').to_dict(orient='index')

    for idx, row in df_loto.iterrows():
        data_sorteio = row['data_dt']
        dt_str = row['data_ontem'].strftime('%Y%m%d')
        
        # O One Hot Vector temporário e Variáveis Sintéticas
        numeros = row['numeros']
        vetor = {f"num_{n}": (1 if n in numeros else 0) for n in range(1, 26)}
        vetor['data'] = data_sorteio
        
        # --- VARIÁVEIS EXÓGENAS SINTÉTICAS (Matemáticas) ---
        vetor['LUMINOSIDADE'] = get_fase_lua_luminosidade(data_sorteio)
        vetor['SALARIO'] = get_forca_pagamento(data_sorteio)
        
        # --- VARIÁVEIS EXÓGENAS REAIS (Via API) ---
        fut_data = dict_fut.get(dt_str, {})
        
        def safe_float(val):
            if val is None or pd.isna(val): return np.nan
            return float(val)
            
        vetor['GOLS_ONTEM'] = safe_float(fut_data.get('gols_total', np.nan))
        vetor['FLAMENGO_ONTEM'] = safe_float(fut_data.get('fla_status', np.nan))
        vetor['PALMEIRAS_ONTEM'] = safe_float(fut_data.get('pal_status', np.nan))
        vetor['SAO_PAULO_ONTEM'] = safe_float(fut_data.get('sao_status', np.nan))
        vetor['CORINTHIANS_ONTEM'] = safe_float(fut_data.get('cor_status', np.nan))
        
        records.append(vetor)
        
    df_loto_matrix = pd.DataFrame(records)
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
                    'Correlação': corr,
                    'Influencia': corr * 100 # Multiplica por 100 para facilitar leitura (Força / %)
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
    st.caption("A intensidade das cores mostra o quanto a movimentação do mercado altera a chance de uma bola sair.")
    
    # Pivotar para Heatmap
    heatmap = alt.Chart(df_corr).mark_rect().encode(
        x=alt.X('Dezena:O', title='Dezena da Lotofácil'),
        y=alt.Y('Ativo:N', title='Ativo Financeiro'),
        color=alt.Color('Influencia:Q', scale=alt.Scale(scheme='redblue', domain=[-10, 10]), title="Força (%)"),
        tooltip=[
            alt.Tooltip('Ativo', title='Ativo Financeiro'), 
            alt.Tooltip('Dezena', title='Número'), 
            alt.Tooltip('Influencia', format='+,.1f', title='Alteração de Chance (%)')
        ]
    ).properties(
        width=700,
        height=300
    )
    st.altair_chart(heatmap, width='stretch')
    
    # --- VISUALIZAÇÃO 2: TOP OPORTUNIDADES ---
    st.subheader("💎 Oportunidades de Ouro (Correlações Fortes)")
    
    # Filtrar Correlações Significativas (Top 5 Positivas e Top 5 Negativas)
    top_pos = df_corr.nlargest(5, 'Influencia')
    top_neg = df_corr.nsmallest(5, 'Influencia')
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("**🚀 Impulsionadores (Jogar quando Ativo SOBE)**")
        for _, row in top_pos.iterrows():
            st.success(f"Quando o **{row['Ativo']}** sobe, a chance do número **{row['Dezena']:02d}** aumenta em **+{row['Influencia']:.1f}%**")
            
    with c2:
        st.markdown("**🛑 Bloqueadores (Evitar quando Ativo SOBE)**")
        for _, row in top_neg.iterrows():
            st.error(f"Quando o **{row['Ativo']}** sobe, a chance do número **{row['Dezena']:02d}** cai em **{row['Influencia']:.1f}%**")
    
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
        df_ativo = df_corr[df_corr['Ativo'] == ativo_sel].copy()
        
        # Calcular "Força" projetada para cada número
        # A variação do ativo atua como multiplicador da influência base.
        # Ex: se a influência base é de +3% quando o ativo sobe e ele variou +2%, o impulso é de +6%.
        df_ativo['Forca_Projetada'] = (df_ativo['Influencia'] * variacao) / 1.0 # ajustando pra manter logica
        
        # Top 5 sugeridos para hoje
        sugestao = df_ativo.nlargest(5, 'Forca_Projetada')
        
        st.markdown(f"### 🔥 Números 'Puxados' pelo {ativo_sel} hoje:")
        st.caption(f"Com a variação de {variacao}%, a IA indica que estes números ganharam muita força estatística.")
        
        cols = st.columns(5)
        for i, (_, row) in enumerate(sugestao.iterrows()):
            cols[i].metric(
                label=f"Bola {row['Dezena']}", 
                value=f"+{row['Forca_Projetada']:.1f}%", 
                delta="Alta Influência",
                delta_color="normal"
            )
            
    return df_full

def calcular_multiplicadores_exogenos(df_loto):
    """
    Retorna um dicionário {dezena: fator_multiplicador} baseado no fechamento mais recente
    do mercado versus as correlações históricas calculadas. Fator 1.0 = Neutro.
    """
    data_fim = datetime.datetime.now()
    data_inicio = data_fim - timedelta(days=365*3)
    
    df_precos, df_mercado = sincronizar_dados_financeiros(data_inicio, data_fim)
    if df_mercado.empty:
        return {n: 1.0 for n in range(1, 26)}
        
    df_loto_recorte = df_loto[df_loto['data'] >= pd.to_datetime(data_inicio)].copy()
    df_full = correlacionar_mercado_loteria(df_loto_recorte, df_mercado)
    df_corr = calcular_correlacao_exogena(df_full)
    
    if df_corr.empty:
        return {n: 1.0 for n in range(1, 26)}
        
    try:
        ultima_variacao = df_mercado.iloc[-1]
    except Exception:
        return {n: 1.0 for n in range(1, 26)}
        
    multiplicadores = {n: 1.0 for n in range(1, 26)}
    
    # Loop em dicionário p/ performance
    mapa_inverso = {k: v for k, v in TICKERS.items()}
    
    for ativo_code, variacao in ultima_variacao.items():
        if pd.isna(variacao): continue
        ativo_nome = next((k for k, v in TICKERS.items() if v == ativo_code), ativo_code)
        
        for d in range(1, 26):
            corr_row = df_corr[(df_corr['Ativo'] == ativo_nome) & (df_corr['Dezena'] == d)]
            if not corr_row.empty:
                influencia = corr_row.iloc[0]['Influencia']
                # Força final em escala decimal ex: 5% * 2% variação = 0.1 => 10%
                forca = (influencia * variacao) / 100.0 
                forca = max(-0.15, min(0.15, forca)) # Limite por ativo = +/- 15%
                multiplicadores[d] += forca
                
    # Normalizar limites absolutos (entre 0.5x e 2.0x) para não zerar bolas nem estourar
    for d in range(1, 26):
        multiplicadores[d] = max(0.5, min(2.0, multiplicadores[d]))
        
    return multiplicadores
