import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
import joblib
import os

def preparar_dados_ensemble(df, janela_atraso=10):
    """
    Prepara dados para Random Forest:
    Features: Frequência recente (10 jogos) + Atrasos
    Target: Vetor binário (25 números) do próximo jogo
    """
    X = []
    y = []
    
    # Precisamos de pelo menos 'janela_atraso' para criar o primeiro input
    # E mais 1 para o target
    start_idx = janela_atraso
    
    for i in range(start_idx, len(df)):
        # --- FEATURES (O que a IA vê) ---
        # 1. Frequência nos últimos 10 jogos
        window = df.iloc[i-janela_atraso:i]
        freqs = np.zeros(25)
        for nums in window['numeros']:
            for n in nums:
                freqs[n-1] += 1
        freqs = freqs / janela_atraso # Normaliza
        
        # 2. Atrasos (Delay)
        atrasos = np.zeros(25)
        ultima_rodada = df.iloc[i-1]['rodada']
        
        # Otimização de cálculo de atraso
        # (Poderíamos iterar pra trás, mas vamos simplificar usando o que temos)
        # Para ser rápido no treino, calculamos aproximado ou iterativo.
        # Vamos fazer iterativo simples na janela total disponível nos dados passados é muito lento.
        # Vamos usar apenas a feature de frequencia por enquanto para ser rápido,
        # e adicionar se o número saiu no ÚLTIMO jogo (Hot/Cold imediato).
        
        no_ultimo = np.zeros(25)
        last_draw = df.iloc[i-1]['numeros']
        for n in last_draw:
            no_ultimo[n-1] = 1
            
        # Feature Vector: [25 freqs] + [25 binary last draw] = 50 features
        features = np.concatenate([freqs, no_ultimo])
        X.append(features)
        
        # --- TARGET (O que ela tem que prever) ---
        target_nums = df.iloc[i]['numeros']
        target_vec = np.zeros(25)
        for n in target_nums:
            target_vec[n-1] = 1
        y.append(target_vec)
        
    return np.array(X), np.array(y)

def treinar_ensemble(df):
    """Treina um Random Forest para prever probabilidades."""
    print("Treinando Ensemble (Random Forest)...")
    X, y = preparar_dados_ensemble(df)
    if len(X) == 0:
        # Fallback para evitar erro se houver poucos dados
        return None
    
    # Modelo: MultiOutput Regressor com Random Forest
    # Usamos Regressor porque queremos "probabilidade" de sair (0.0 a 1.0)
    # n_estimators=100 é um bom balanço entre performance e velocidade
    rf = RandomForestRegressor(n_estimators=100, n_jobs=-1, random_state=42, max_depth=10)
    
    # Treina em tudo (pois é para prever o FUTURO desconhecido)
    rf.fit(X, y)
    
    return rf

def prever_ensemble(modelo, df_recente):
    """
    Gera previsão para o próximo concurso usando os últimos dados (df_recente).
    df_recente deve conter pelo menos os últimos 10 jogos.
    """
    # Montar APENAS o último vetor de input
    # 1. Frequencia ultimos 10
    ultimos_10 = df_recente.tail(10)
    freqs = np.zeros(25)
    for nums in ultimos_10['numeros']:
        for n in nums:
            freqs[n-1] += 1
    freqs = freqs / 10
    
    # 2. No ultimo jogo
    no_ultimo = np.zeros(25)
    last_draw = df_recente.iloc[-1]['numeros']
    for n in last_draw:
        no_ultimo[n-1] = 1
        
    features = np.concatenate([freqs, no_ultimo])
    
    # Prever (reshape para 1 amostra)
    # Retorna array de shape (1, 25) com as probabilidades
    probabilidade = modelo.predict(features.reshape(1, -1))[0]
    
    return probabilidade
