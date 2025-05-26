import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime

def carregar_dados(caminho_csv, ano=None, data_fim=None):
    df = pd.read_csv(caminho_csv)
    df['data'] = pd.to_datetime(df['data'])

    if ano:
        df = df[df['data'].dt.year == ano]

    if data_fim:
        df = df[df['data'] <= pd.to_datetime(data_fim)]

    numeros = df[[f'num_{i+1}' for i in range(15)]].values
    return numeros

def preparar_sequencias(numeros, passo=5):
    X, y = [], []
    for i in range(len(numeros) - passo):
        entrada = numeros[i:i+passo].flatten()
        alvo = numeros[i+passo]
        X.append(entrada)
        y.append(alvo)
    return np.array(X), np.array(y)

def normalizar(X):
    scaler = MinMaxScaler()
    return scaler.fit_transform(X), scaler
