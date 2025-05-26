import json
import pandas as pd
from collections import Counter
from datetime import datetime

# Carregue o JSON
with open("rodadas_normalizadas.json", "r") as f:
    data = json.load(f)

# Transformar em DataFrame
df = pd.DataFrame(data)

# Converter a data para datetime e extrair o ano
df['data'] = pd.to_datetime(df['data'])
df['ano'] = df['data'].dt.year

# Contar quantas vezes cada número saiu por ano
def freq_por_ano(df):
    resultado = {}
    for ano, grupo in df.groupby('ano'):
        todos_numeros = sum(grupo['numeros'].tolist(), [])  # flatten
        contador = Counter(todos_numeros)
        resultado[ano] = dict(contador.most_common())
    return resultado

frequencias_ano = freq_por_ano(df)

# Exibir os 3 mais frequentes de cada ano
for ano, freqs in frequencias_ano.items():
    top3 = list(freqs.items())[:3]
    print(f"{ano} - Top 3: {top3}")


def quando_top3_aparecem_juntos(df, frequencias_ano):
    resultados = {}

    for ano, freqs in frequencias_ano.items():
        top3 = [num for num, _ in list(freqs.items())[:3]]
        df_ano = df[df['ano'] == ano].copy()
        df_ano['tem_top3'] = df_ano['numeros'].apply(lambda nums: all(n in nums for n in top3))
        
        ocorrencias = df_ano[df_ano['tem_top3']]
        if not ocorrencias.empty:
            rodada_primeira = int(ocorrencias.iloc[0]['rodada'])
            data_primeira = ocorrencias.iloc[0]['data'].date()
        else:
            rodada_primeira = None
            data_primeira = None
        
        resultados[ano] = {
            'top3': top3,
            'primeira_vez': rodada_primeira,
            'data_primeira': data_primeira
        }
    
    return resultados

resultados_top3 = quando_top3_aparecem_juntos(df, frequencias_ano)

for ano, info in resultados_top3.items():
    print(f"{ano}: Top 3 = {info['top3']} → Primeira vez juntos: rodada {info['primeira_vez']} em {info['data_primeira']}")


from itertools import combinations

def pares_mais_comuns(df, tamanho=2, top_n=5):
    resultados = {}

    for ano, grupo in df.groupby('ano'):
        combinacoes = []
        for numeros in grupo['numeros']:
            combinacoes.extend(combinations(sorted(numeros), tamanho))
        contador = Counter(combinacoes)
        resultados[ano] = contador.most_common(top_n)

    return resultados

# Pares
print("\nPares mais comuns por ano:")
pares = pares_mais_comuns(df, tamanho=2)
for ano, top_pares in pares.items():
    print(f"{ano}: {top_pares}")

# Trios
print("\nTrios mais comuns por ano:")
trios = pares_mais_comuns(df, tamanho=3)
for ano, top_trios in trios.items():
    print(f"{ano}: {top_trios}")


def prob_top3_juntos(df, frequencias_ano):
    resultados = {}

    for ano, freqs in frequencias_ano.items():
        top3 = [num for num, _ in list(freqs.items())[:3]]
        df_ano = df[df['ano'] == ano]
        total = len(df_ano)
        juntos = df_ano['numeros'].apply(lambda nums: all(n in nums for n in top3)).sum()
        resultados[ano] = juntos / total if total else 0.0

    return resultados

probs = prob_top3_juntos(df, frequencias_ano)
print("\nProbabilidades dos top 3 saírem juntos por ano:")
for ano, prob in probs.items():
    print(f"{ano}: {prob:.2%}")
