import json
from datetime import datetime

# Carregar o JSON original
with open("dados.json", "r", encoding="utf-8") as f:
    dados_originais = json.load(f)

# Normalizar os dados
dados_normalizados = []
for item in dados_originais:
    numeros = [item[f"N {i}"] for i in range(1, 16)]
    dados_normalizados.append({
        "rodada": item["Rodada"],
        "data": datetime.strptime(item["Data"], "%d/%m/%Y").strftime("%Y-%m-%d"),
        "numeros": sorted(numeros)  # ordenar para facilitar análises
    })

# Salvar novo JSON
with open("rodadas_normalizadas.json", "w", encoding="utf-8") as f:
    json.dump(dados_normalizados, f, indent=2, ensure_ascii=False)

print("Rodadas normalizadas com sucesso!")
