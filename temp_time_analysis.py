import json
from collections import Counter
from datetime import datetime

def calcular_dna(numeros):
    impares = sum(1 for x in numeros if x % 2 != 0)
    primos = sum(1 for x in numeros if x in [2, 3, 5, 7, 11, 13, 17, 19, 23])
    moldura = sum(1 for x in numeros if x in [1,2,3,4,5,6,10,11,15,16,20,21,22,23,24,25])
    soma = sum(numeros)
    return impares, primos, moldura, soma

print("Carregando base de dados...")
with open('IA_Tensor/rodadas.json', 'r') as f:
    data = json.load(f)

# Sort by round number (rodada) to ensure temporal order
data.sort(key=lambda x: x['rodada'])

# Annotate data
for row in data:
    dt = datetime.strptime(row['data'], '%Y-%m-%d')
    row['dt'] = dt
    row['dia'] = dt.day
    row['mes'] = dt.month
    row['dia_semana'] = dt.weekday() # 0 = Monday, 6 = Sunday
    
    if row['dia'] <= 10:
        row['periodo_mes'] = 'Inicio'
    elif row['dia'] <= 20:
        row['periodo_mes'] = 'Meio'
    else:
        row['periodo_mes'] = 'Fim'
        
    i, p, m, s = calcular_dna(row['numeros'])
    row['impares'] = i
    row['primos'] = p
    row['moldura'] = m
    row['soma'] = s

# --- TEORIA 1: O Período do Mês Influencia o DNA do Sorteio? ---
print("\\n=== TEORIA 1: O Período do Mês Influencia o DNA do Sorteio? ===")
stats_periodo = {'Inicio': {'soma': 0, 'count': 0}, 'Meio': {'soma': 0, 'count': 0}, 'Fim': {'soma': 0, 'count': 0}}
for row in data:
    p = row['periodo_mes']
    stats_periodo[p]['soma'] += row['soma']
    stats_periodo[p]['count'] += 1

for p in ['Inicio', 'Meio', 'Fim']:
    media = stats_periodo[p]['soma'] / stats_periodo[p]['count']
    print(f"[{p}] Média da Soma: {media:.2f} (Total Jogos: {stats_periodo[p]['count']})")

# --- TEORIA 2: O Dia da Semana Cria Vieses? ---
print("\\n=== TEORIA 2: O Dia da Semana Cria Vieses? (0=Seg, ..., 5=Sab) ===")
stats_dia = {i: {'soma': 0, 'impares': 0, 'count': 0} for i in range(7)}
for row in data:
    d = row['dia_semana']
    stats_dia[d]['soma'] += row['soma']
    stats_dia[d]['impares'] += row['impares']
    stats_dia[d]['count'] += 1

for d in range(6): # Domingo (6) geralmente nao tem sorteio, mas ignora se count=0
    if stats_dia[d]['count'] > 0:
        media_s = stats_dia[d]['soma'] / stats_dia[d]['count']
        media_i = stats_dia[d]['impares'] / stats_dia[d]['count']
        print(f"[Dia da Semana {d}] Média Soma: {media_s:.2f} | Média Ímpares: {media_i:.2f} (Total: {stats_dia[d]['count']})")


# --- TEORIA 3: Duração de Tendência (Momentum) ---
print("\\n=== TEORIA 3: Momentum de Somas Altas (>195) ===")
# Mediana historica costuma ser 195
altas_consecutivas = 0
reversoes = 0

for i in range(len(data)-1):
    atual_alta = data[i]['soma'] > 195
    prox_alta = data[i+1]['soma'] > 195
    
    if atual_alta:
        if prox_alta:
            altas_consecutivas += 1
        else:
            reversoes += 1

total_altas = altas_consecutivas + reversoes
prob_manter = (altas_consecutivas / total_altas) * 100
prob_reverter = (reversoes / total_altas) * 100

print(f"Se a Soma foi > 195 hoje:")
print(f"Prob. de continuar ALTA amanhã: {prob_manter:.1f}%")
print(f"Prob. de Reverter à média (Baixa) amanhã: {prob_reverter:.1f}%")

# --- TEORIA 4: Repetições de Dezenas do Jogo Anterior ---
print("\\n=== TEORIA 4: Padrão das Dezenas Repetidas ===")
repetentes = Counter()
for i in range(1, len(data)):
    set_atual = set(data[i]['numeros'])
    set_ant = set(data[i-1]['numeros'])
    inter = len(set_atual.intersection(set_ant))
    repetentes[inter] += 1
    
total = sum(repetentes.values())
for k in sorted(repetentes.keys()):
    pct = (repetentes[k] / total) * 100
    if pct > 1.0: # Mostra so os relevantes (>1%)
        print(f"{k} repetidas: {pct:.2f}% das vezes")
