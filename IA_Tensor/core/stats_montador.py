import pandas as pd
import numpy as np

def calcular_estado_ciclo(df):
    """
    Retorna quais dezenas faltam para fechar o ciclo atual e qual é o sorteio atual do ciclo.
    Um ciclo se inicia no sorteio X e se encerra quando as 25 dezenas foram sorteadas pelo menos uma vez.
    """
    dezenas_sorteadas = set()
    sorteio_ciclo = 0
    df_sorted = df.sort_values(by='rodada', ascending=True)
    
    # Processar rodadas a partir da última até achar o ciclo atual
    # Para ser eficiente, contaremos de trás pra frente
    # Mas é mais seguro iterar de toda a vida e achar ciclos:
    for _, row in df_sorted.iterrows():
        nums = set(row['numeros'])
        dezenas_sorteadas.update(nums)
        sorteio_ciclo += 1
        
        if len(dezenas_sorteadas) == 25:
            # Ciclo fechou, zera para o próximo
            dezenas_sorteadas = set()
            sorteio_ciclo = 0
            
    todas_dezenas = set(range(1, 26))
    dezenas_faltantes = list(todas_dezenas - dezenas_sorteadas)
    
    return {
        'sorteio_atual_do_ciclo': sorteio_ciclo,
        'dezenas_faltantes': sorted(dezenas_faltantes),
        'progresso_percentual': (len(dezenas_sorteadas) / 25.0) * 100
    }

def calcular_forca_dezenas(df):
    """
    Calcula um 'Power Score' de 0 a 100 para cada uma das 25 dezenas com base recente.
    """
    scores = {}
    df_rec = df.sort_values(by='rodada', ascending=False)
    
    ultimos_10 = df_rec.head(10)['numeros'].tolist()
    ultimos_20 = df_rec.head(20)['numeros'].tolist()
    
    # Calcular frequência nos últimos 10 (max 10) -> peso até 40
    for i in range(1, 26):
        freq_10 = sum(1 for jogo in ultimos_10 if i in jogo)
        freq_20 = sum(1 for jogo in ultimos_20 if i in jogo)
        
        # Calcular atraso
        atraso = 0
        for jogo in df_rec['numeros'].tolist():
            if i in jogo:
                break
            atraso += 1
            
        # Fórmula customizada (exemplo heurístico)
        # Freq 10 jogos ideal: ~6 (60%) -> 40 pts
        pontuacao_freq = (freq_10 / 10.0) * 40 
        
        # Atraso ideal (1 a 3 jogos atrasado costuma voltar) -> 30 pts
        pontuacao_atraso = 0
        if atraso == 0: pontuacao_atraso = 10 
        elif 1 <= atraso <= 3: pontuacao_atraso = 30
        elif 4 <= atraso <= 6: pontuacao_atraso = 15
        else: pontuacao_atraso = 5
        
        # Freq longo prazo estabilidade -> 30 pts
        pontuacao_longo = (freq_20 / 20.0) * 30
        
        score_total = min(100, int(pontuacao_freq + pontuacao_atraso + pontuacao_longo))
        scores[i] = score_total
        
    return scores

def analisar_desenho_5x5(selecionados):
    """
    Analisa os padrões espaciais na grade 5x5 do volante da Lotofácil.
    Retorna uma lista de strings com alertas ou insights.
    """
    if len(selecionados) == 0:
        return []
    
    # Criar grade 5x5 booleana
    grade = np.zeros((5, 5), dtype=bool)
    for n in selecionados:
        n_zero_based = n - 1
        row = n_zero_based // 5
        col = n_zero_based % 5
        grade[row, col] = True
        
    insights = []
    
    # Análise de linhas e colunas vazias
    linhas_vazias = 0
    linhas_cheias = 0
    for i in range(5):
        qtd_linha = np.sum(grade[i, :])
        if qtd_linha == 0: linhas_vazias += 1
        if qtd_linha == 5: linhas_cheias += 1
        
    colunas_vazias = 0
    colunas_cheias = 0
    for j in range(5):
        qtd_col = np.sum(grade[:, j])
        if qtd_col == 0: colunas_vazias += 1
        if qtd_col == 5: colunas_cheias += 1
        
    if linhas_vazias >= 2:
        insights.append("⚠️ Você deixou 2 ou mais linhas totalmente vazias. Padrão MUITO raro (menos de 0.5% dos sorteios).")
    elif linhas_vazias == 1:
        insights.append("📊 1 linha vazia. Ocorre em cerca de 4% dos sorteios. Um pouco arriscado.")
        
    if colunas_vazias >= 2:
        insights.append("⚠️ Você deixou 2 ou mais colunas totalmente vazias. Altíssimo risco.")
        
    if linhas_cheias >= 3:
         insights.append("⚠️ Você tem 3 linhas completas (fechadas). Muito incomum, tente distribuir mais.")
         
    # Padrão Cruz
    meio_linha = np.sum(grade[2, :])
    meio_coluna = np.sum(grade[:, 2])
    if meio_linha == 5 and meio_coluna == 5:
        insights.append("✝️ Você desenhou uma 'Cruz' perfeita. Padrão estético que raramente se concretiza integralmente.")

    return insights

