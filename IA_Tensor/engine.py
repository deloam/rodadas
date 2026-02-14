
import numpy as np
import pandas as pd
from collections import Counter
import os
from lstm import preparar_dados, treinar_modelo
from ensemble import treinar_ensemble, prever_ensemble
from keras.models import load_model

class AIEngine:
    def __init__(self, df_historico, n_dias=30):
        self.df = df_historico
        self.n_dias = n_dias
        self.PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}
        self.MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
        self.FIBONACCI = {1, 2, 3, 5, 8, 13, 21}

    def extrair_features(self, df):
        df = df.copy()
        df['dia_par'] = df['data'].dt.day % 2 == 0
        df['fim_de_semana'] = df['data'].dt.dayofweek >= 5
        df['mes'] = df['data'].dt.month
        df['consecutivos'] = df['numeros'].apply(lambda x: sum(1 for i in range(len(x)-1) if x[i]+1 == x[i+1]))
        
        # Preencher frequências
        X = np.zeros((len(df), 25))
        for i, nums in enumerate(df['numeros']):
            for n in nums:
                if 1 <= n <= 25:
                    X[i, n-1] = 1
        
        df_bins = pd.DataFrame(X, columns=[f'freq_{i}' for i in range(1, 26)])
        df_rolling = df_bins.rolling(window=self.n_dias, min_periods=1).sum().shift(1).fillna(0)
        
        for col in df_rolling.columns:
            df[col] = df_rolling[col]
        return df

    def calcular_probabilidades(self, df_filtrado, usar_aprendizado=False, salvar_aprendizado=False):
        # 1. Features
        df_feat = self.extrair_features(df_filtrado)
        
        # 2. LSTM
        df_lstm = df_feat.tail(300)
        entradas, saidas = preparar_dados(df_lstm, intervalo=self.n_dias)
        
        if entradas.size == 0:
            raise ValueError("Dados insuficientes para a Janela de Análise selecionada. Aumente o intervalo de datas.")

        if usar_aprendizado and os.path.exists("modelo_treinado.keras"):
            modelo = load_model("modelo_treinado.keras")
        else:
            modelo = treinar_modelo(entradas, saidas)
            if salvar_aprendizado:
                modelo.save("modelo_treinado.keras")
        
        pred_lstm = modelo.predict(entradas[-1][None, ...], verbose=0)[0]
        
        # 3. Ensemble
        modelo_rf = treinar_ensemble(df_filtrado)
        if modelo_rf is not None:
            pred_ensemble = prever_ensemble(modelo_rf, df_filtrado)
        else:
            pred_ensemble = np.zeros(25)
        
        # 4. Frequência Recente (10)
        ultimos_10 = df_filtrado.tail(10)
        freq_contador = Counter()
        for nums in ultimos_10['numeros']:
            freq_contador.update(nums)
        prob_freq = np.zeros(25)
        for num in range(1, 26):
            prob_freq[num-1] = freq_contador.get(num, 0) / 10
            
        # 5. Atrasos
        ultima_rodada_abs = df_filtrado['rodada'].max()
        ultimas_aparicoes = {}
        for idx, row in df_filtrado.iterrows():
            for n in row['numeros']:
                ultimas_aparicoes[n] = row['rodada']
        
        prob_atraso = np.zeros(25)
        for num in range(1, 26):
            if num in ultimas_aparicoes:
                atraso = ultima_rodada_abs - ultimas_aparicoes[num]
                prob_atraso[num-1] = min(atraso * 0.02, 0.2)
            else:
                prob_atraso[num-1] = 0.2
        
        # Fusão Híbrida
        prob_final = (pred_lstm * 0.40) + (pred_ensemble * 0.40) + (prob_freq * 0.10) + (prob_atraso * 0.10)
        
        # Garantir que não temos soma zero
        if np.sum(prob_final) == 0:
            prob_final = np.ones(25) / 25
            
        return prob_final / np.sum(prob_final)

    def simular_jogos(self, probabilidades, qtd_sequencias, qtd_numeros, nums_fixos, nums_excluidos, ultima_rodada):
        # Aplicar Fixos/Excluintes
        prob_ajustada = probabilidades.copy()
        for n in nums_excluidos:
            if 1 <= n <= 25: prob_ajustada[n-1] = 0
        for n in nums_fixos:
            if 1 <= n <= 25: prob_ajustada[n-1] = 100
        
        if np.sum(prob_ajustada) == 0:
             prob_ajustada = np.ones(25)
             for n in nums_excluidos:
                  if 1 <= n <= 25: prob_ajustada[n-1] = 0
        
        prob_final = prob_ajustada / np.sum(prob_ajustada)
        
        pool_size = max(qtd_sequencias * 50, 500)
        candidatos = []
        
        for _ in range(pool_size):
            escolhidos = set(nums_fixos)
            if len(escolhidos) > qtd_numeros: escolhidos = set(list(escolhidos)[:qtd_numeros])
            
            tries = 0
            while len(escolhidos) < qtd_numeros and tries < 100:
                num = np.random.choice(np.arange(1, 26), p=prob_final)
                if num not in nums_excluidos: escolhidos.add(num)
                tries += 1
            
            # Fallback se não preencheu (ex: muitos excluidos)
            if len(escolhidos) < qtd_numeros:
                restante = list(set(range(1, 26)) - escolhidos - nums_excluidos)
                if restante: escolhidos.update(restante[:qtd_numeros - len(escolhidos)])
            
            seq = sorted(list(escolhidos))
            
            # Cálculo de Confiança
            soma_probs = sum(probabilidades[n-1] for n in seq)
            confianca = min(soma_probs * 20 * 100 / qtd_numeros, 100)
            
            # Scoring de Equilíbrio
            score = 0
            impares = sum(1 for x in seq if x % 2 != 0)
            if 7 <= impares <= 9: score += 2
            elif 6 <= impares <= 10: score += 1
            
            primos = sum(1 for x in seq if x in self.PRIMOS)
            if 4 <= primos <= 6: score += 2
            elif 3 <= primos <= 7: score += 1
            
            repetentes = len(set(seq).intersection(ultima_rodada))
            if 8 <= repetentes <= 10: score += 3 
            elif 7 <= repetentes <= 11: score += 1
            
            soma = sum(seq)
            if 180 <= soma <= 220: score += 1
            
            moldura = sum(1 for x in seq if x in self.MOLDURA)
            if 9 <= moldura <= 10: score += 2 
            elif 8 <= moldura <= 11: score += 1
            
            fibo = sum(1 for x in seq if x in self.FIBONACCI)
            if 4 == fibo: score += 2    
            elif 3 <= fibo <= 5: score += 1
            
            candidatos.append({
                'seq': seq, 'score': score, 'confianca': confianca, 
                'metrics': {
                    'impares': impares, 'primos': primos, 'moldura': moldura, 
                    'fibo': fibo, 'repetentes': repetentes, 'soma': soma
                }
            })
            
        candidatos.sort(key=lambda x: x['score'], reverse=True)
        
        if qtd_sequencias > 100:
            return candidatos[:qtd_sequencias]
        else:
            top_cut = max(len(candidatos) // 4, qtd_sequencias)
            melhores = candidatos[:top_cut]
            indices = np.random.choice(len(melhores), min(qtd_sequencias, len(melhores)), replace=False)
            return [melhores[idx] for idx in indices]
