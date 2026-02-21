import pandas as pd
import json
import numpy as np
import streamlit as st

@st.cache_data
def carregar_dados():
    caminho = "rodadas.json"
    with open(caminho, 'r') as f:
        dados = json.load(f)
    df = pd.DataFrame(dados)
    df['data'] = pd.to_datetime(df['data'])
    return df

def contar_frequencias(df, idx, n):
    start = max(0, idx - n)
    subset = df.iloc[start:idx]['numeros'].explode()
    freq = subset.value_counts().to_dict()
    return freq

def preencher_frequencias(df, n_dias):
    # Otimização: Criar matriz binária uma única vez
    X = np.zeros((len(df), 25))
    for i, nums in enumerate(df['numeros']):
        for n in nums:
            if 1 <= n <= 25:
                X[i, n-1] = 1
    
    # Usar soma móvel (rolling sum) para calcular frequencias em massa
    df_bins = pd.DataFrame(X, columns=[f'freq_{i}' for i in range(1, 26)])
    df_rolling = df_bins.rolling(window=n_dias, min_periods=1).sum().shift(1).fillna(0)
    
    # Adicionar de volta ao dataframe
    for col in df_rolling.columns:
        df[col] = df_rolling[col]
    return df

def extrair_features(df, n_dias):
    df = df.copy()
    df['dia_par'] = df['data'].dt.day % 2 == 0
    df['fim_de_semana'] = df['data'].dt.dayofweek >= 5
    df['mes'] = df['data'].dt.month
    df['consecutivos'] = df['numeros'].apply(lambda x: sum(1 for i in range(len(x)-1) if x[i]+1 == x[i+1]))
    df = preencher_frequencias(df, n_dias)
    return df
