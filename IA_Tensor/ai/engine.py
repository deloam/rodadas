
import numpy as np
import pandas as pd
from collections import Counter
import os
from ai.lstm import preparar_dados, treinar_modelo
from ai.ensemble import treinar_ensemble, prever_ensemble
from keras.models import load_model

class AIEngine:
    def __init__(self, df_historico, n_dias=30):
        self.df = df_historico
        self.n_dias = n_dias
        from core.constants import PRIMOS, MOLDURA, FIBONACCI
        self.PRIMOS = PRIMOS
        self.MOLDURA = MOLDURA
        self.FIBONACCI = FIBONACCI

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
            
            # --- VERIFICAÇÃO DE INEDITISMO EMBUTIDA NA GERAÇÃO ---
            # Evita gerar jogos que já saíram na história se houver alternativas
            from core.utils import verificar_ineditismo
            if hasattr(self, 'df'):
                 # 1. Filtro: Já Saiu na História?
                 msg = verificar_ineditismo(self.df, seq)
                 
                 # 2. Filtro (Regra de Ouro Temporal): Repeteco do último concurso (8 a 10 permitidos)
                 ultimo_jogo = set(self.df.iloc[-1]['numeros'])
                 repetidas = len(set(seq).intersection(ultimo_jogo))
                 passou_regra_temporal = (8 <= repetidas <= 10)
                 
                 tentativas_correcao = 0
                 
                 # Loop de Mutação Genética Rápida se quebrar regra de Ineditismo OU Regra Temporal
                 while ((msg and "ALERTA" in msg) or not passou_regra_temporal) and tentativas_correcao < 10:
                     nao_fixos = list(set(seq) - set(nums_fixos))
                     if not nao_fixos: break # Impossível corrigir se todos são fixos pelo usuário
                     
                     # Escolhe quem vai morrer 
                     semente_morta = np.random.choice(nao_fixos)
                     seq.remove(semente_morta)
                     
                     # Busca substituto
                     candidatos_vivos = list(set(range(1, 26)) - set(seq) - set(nums_excluidos))
                     if candidatos_vivos:
                         # Tenta puxar da roda de probabilidade original se der, senão aleatório ponderado
                         pesos_candidatos = [prob_final[n-1] for n in candidatos_vivos]
                         soma_pesos = sum(pesos_candidatos)
                         if soma_pesos > 0:
                             pesos_norm = [p/soma_pesos for p in pesos_candidatos]
                             novo_num = np.random.choice(candidatos_vivos, p=pesos_norm)
                         else:
                             novo_num = np.random.choice(candidatos_vivos)
                         
                         seq.append(novo_num)
                     
                     seq = sorted(seq)
                     
                     # Re-testa
                     msg = verificar_ineditismo(self.df, seq)
                     repetidas = len(set(seq).intersection(ultimo_jogo))
                     passou_regra_temporal = (8 <= repetidas <= 10)
                     
                     tentativas_correcao += 1

            
            # Cálculo de Confiança
            soma_probs = sum(probabilidades[n-1] for n in seq)
            confianca = min(soma_probs * 20 * 100 / qtd_numeros, 100)
            
            from core.utils import avaliar_qualidade_jogo
            score, m = avaliar_qualidade_jogo(seq, ultima_rodada)
            
            candidatos.append({
                'seq': seq, 'score': score, 'confianca': confianca, 
                'metrics': m
            })
            
        candidatos.sort(key=lambda x: x['score'], reverse=True)
        
        if qtd_sequencias > 100:
            return candidatos[:qtd_sequencias]
        else:
            top_cut = max(len(candidatos) // 4, qtd_sequencias)
            melhores = candidatos[:top_cut]
            indices = np.random.choice(len(melhores), min(qtd_sequencias, len(melhores)), replace=False)
            return [melhores[idx] for idx in indices]
