from core.constants import PRIMOS, MOLDURA, FIBONACCI

def calcular_metricas_dna(numeros):
    """
    Calcula as métricas matemáticas base (DNA) para uma sequência de números.
    Retorna um dicionário com os valores.
    """
    seq = sorted(list(numeros))
    
    impares = sum(1 for x in seq if x % 2 != 0)
    primos = sum(1 for x in seq if x in PRIMOS)
    moldura = sum(1 for x in seq if x in MOLDURA)
    fibo = sum(1 for x in seq if x in FIBONACCI)
    soma = sum(seq)
    
    return {
        'impares': impares,
        'primos': primos,
        'moldura': moldura,
        'fibo': fibo,
        'soma': soma
    }

def avaliar_qualidade_jogo(seq, ultima_rodada=None):
    """
    Gera um score de 0 a 10 + baseado na proximidade das métricas ideais.
    """
    m = calcular_metricas_dna(seq)
    score = 0
    
    if 7 <= m['impares'] <= 9: score += 2
    elif 6 <= m['impares'] <= 10: score += 1
    
    if 4 <= m['primos'] <= 6: score += 2
    elif 3 <= m['primos'] <= 7: score += 1
    
    if 9 <= m['moldura'] <= 11: score += 2
    elif 8 <= m['moldura'] <= 12: score += 1
    
    if m['fibo'] == 4: score += 2
    elif 3 <= m['fibo'] <= 5: score += 1
    
    if 180 <= m['soma'] <= 220: score += 2
    elif 170 <= m['soma'] <= 230: score += 1
    
    if ultima_rodada is not None:
        repetentes = len(set(seq).intersection(set(ultima_rodada)))
        m['repetentes'] = repetentes
        if 8 <= repetentes <= 10: score += 2
        elif 7 <= repetentes <= 11: score += 1
    
    return score, m
