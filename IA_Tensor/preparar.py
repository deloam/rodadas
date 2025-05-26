import json
import pandas as pd

with open('rodadas.json') as f:
    data = json.load(f)

linhas = []
for item in data:
    linha = {
        'rodada': item['rodada'],
        'data': item['data']
    }
    for i, num in enumerate(item['numeros']):
        linha[f'num_{i+1}'] = num
    linhas.append(linha)

df = pd.DataFrame(linhas)
df.to_csv('rodadas.csv', index=False)
print("CSV salvo como 'rodadas.csv'")
