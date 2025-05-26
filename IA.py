import json
import pandas as pd
from datetime import datetime
from collections import Counter
import random

# Carregar dados
with open('rodadas_normalizadas.json', 'r') as f:
    dados = json.load(f)

# Transformar em DataFrame
df = pd.DataFrame(dados)
df['data'] = pd.to_datetime(df['data'])

# Função para filtrar por intervalo de datas
def filtrar_intervalo(df, inicio, fim):
    inicio = pd.to_datetime(inicio)
    fim = pd.to_datetime(fim)
    return df[(df['data'] >= inicio) & (df['data'] <= fim)]

# Análise de números mais comuns em dias pares/ímpares
def frequencias_par_impar(df_filtrado):
    pares = []
    impares = []
    for _, row in df_filtrado.iterrows():
        target = pares if row['data'].day % 2 == 0 else impares
        target.extend(row['numeros'])
    return Counter(pares), Counter(impares)

# Sequências mais comuns (pares consecutivos)
def sequencias_comuns(df_filtrado):
    sequencias = []
    for nums in df_filtrado['numeros']:
        nums = sorted(nums)
        for i in range(len(nums) - 1):
            if nums[i+1] == nums[i] + 1:
                sequencias.append((nums[i], nums[i+1]))
    return Counter(sequencias)

# Previsão baseada em maior frequência geral
def prever_proxima(df_filtrado):
    todos_numeros = sum(df_filtrado['numeros'].tolist(), [])
    frequencias = Counter(todos_numeros)
    mais_comuns = [num for num, _ in frequencias.most_common(15)]
    return sorted(mais_comuns)

# Exemplo de uso
inicio = "2020-01-01"
fim = "2025-04-25"
df_filtrado = filtrar_intervalo(df, inicio, fim)

# Análises
pares, impares = frequencias_par_impar(df_filtrado)
sequencias = sequencias_comuns(df_filtrado)
previsao = prever_proxima(df_filtrado)

# Resultados
print("Frequência em dias pares:", pares.most_common(5))
print("Frequência em dias ímpares:", impares.most_common(5))
print("Sequências mais comuns:", sequencias.most_common(5))
print("Previsão de próximos 15 números:", previsao)
