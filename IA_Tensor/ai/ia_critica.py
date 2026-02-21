def analisar_riscos_jogo(numeros):
    """
    Analisa um jogo (lista de números) e retorna alertas de riscos
    baseados em anomalias estatísticas extremas (Advogado do Diabo).
    """
    numeros = sorted(list(numeros))
    riscos = []
    
    # 1. Sequência Monstruosa (Ex: 1,2,3,4,5,6)
    consecutivos = 0
    max_consec = 0
    for i in range(len(numeros)-1):
        if numeros[i+1] == numeros[i] + 1:
            consecutivos += 1
        else:
            max_consec = max(max_consec, consecutivos)
            consecutivos = 0
    max_consec = max(max_consec, consecutivos) + 1 # +1 pois conta os numeros
    
    if max_consec >= 6:
        riscos.append(f"⚠️ Sequência muito longa ({max_consec} números seguidos). Raríssimo.")
    elif max_consec >= 5:
        riscos.append(f"⚠️ Sequência perigosa ({max_consec} números).")

    # 2. Início muito tardio ou Fim muito cedo
    if numeros[0] > 6:
        riscos.append(f"⚠️ Jogo começa muito tarde (Número {numeros[0]}).")
    if numeros[-1] < 20:
        riscos.append(f"⚠️ Jogo termina muito cedo (Número {numeros[-1]}).")
        
    # 3. Desequilíbrio de Pares/Ímpares Extremo
    impares = sum(1 for n in numeros if n % 2 != 0)
    if impares >= 11:
        riscos.append(f"⚠️ Excesso de Ímpares ({impares}). Normal é 7 a 9.")
    elif impares <= 4:
        riscos.append(f"⚠️ Excesso de Pares ({15-impares}). Normal é 6 a 8.")
        
    # 4. Soma Fora da Curva
    soma = sum(numeros)
    if soma < 165:
        riscos.append(f"⚠️ Soma muito baixa ({soma}). Jogo concentrado no início.")
    elif soma > 235:
        riscos.append(f"⚠️ Soma muito alta ({soma}). Jogo concentrado no final.")
        
    # 5. Colunas/Linhas Vazias (Buracos)
    # Linhas: 1-5, 6-10, 11-15, 16-20, 21-25
    linhas_vazias = 0
    for r in range(0, 5):
        inicio = r * 5 + 1
        fim = inicio + 4
        if not any(inicio <= n <= fim for n in numeros):
            linhas_vazias += 1
            
    if linhas_vazias >= 2:
        riscos.append("⚠️ Duas ou mais linhas inteiras vazias.")
        
    return riscos
