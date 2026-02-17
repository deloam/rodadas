
import numpy as np
import pandas as pd
import random
from collections import Counter
from smart_clustering import treinar_modelo_clusters, extrair_metricas_avancadas
from caos_exogeno import baixar_dados_financeiros, get_fase_lua_luminosidade, correlacionar_mercado_loteria, calcular_correlacao_exogena, TICKERS
import datetime
import streamlit as st

class EvoEngine:
    def __init__(self, df_historico):
        self.df = df_historico
        self.PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}
        self.MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
        self.FIBONACCI = {1, 2, 3, 5, 8, 13, 21}
        
        # Cache de Sinergia (Quais números saem juntos)
        self.matrix_sinergia = self._calcular_matriz_sinergia()
        
    def _calcular_matriz_sinergia(self):
        """Calcula a frequência com que pares de números aparecem juntos no histórico."""
        matrix = np.zeros((26, 26))
        for nums in self.df.tail(500)['numeros']:
            for i in range(len(nums)):
                for j in range(i + 1, len(nums)):
                    matrix[nums[i], nums[j]] += 1
                    matrix[nums[j], nums[i]] += 1
        return matrix

    def fitness_function(self, individuo, params_alvo, df_corr_exogena=None):
        """
        Calcula o quão 'bom' é um jogo baseado em múltiplos critérios.
        individuo: lista de 15 a 20 números.
        params_alvo: dicionário com metas (Ex: {'impares': 8, 'soma': 200})
        """
        score = 0
        seq = sorted(list(individuo))
        n = len(seq)
        
        # 1. Critérios Matemáticos (Equilíbrio)
        impares = sum(1 for x in seq if x % 2 != 0)
        score += 10 if 7 <= impares <= 9 else (5 if 6 <= impares <= 10 else 0)
        
        primos = sum(1 for x in seq if x in self.PRIMOS)
        score += 10 if 5 <= primos <= 6 else (5 if 4 <= primos <= 7 else 0)
        
        moldura = sum(1 for x in seq if x in self.MOLDURA)
        score += 10 if 9 <= moldura <= 11 else (5 if 8 <= moldura <= 12 else 0)
        
        soma = sum(seq)
        score += 10 if 180 <= soma <= 220 else (5 if 170 <= soma <= 230 else 0)
        
        # 2. Sinergia Histórica (Pares Fortes)
        sinergia_total = 0
        for i in range(len(seq)):
            for j in range(i + 1, len(seq)):
                sinergia_total += self.matrix_sinergia[seq[i], seq[j]]
        score += (sinergia_total / (n * (n-1) / 2)) * 0.5
        
        # 3. Influência Exógena (Mercado Financeiro / Lua)
        if df_corr_exogena is not None and not df_corr_exogena.empty:
            # Pegamos o impacto médio de todos os ativos
            impacto_exogeno = 0
            for num in seq:
                # Soma as correlações positivas desse número
                impacto_exogeno += df_corr_exogena[df_corr_exogena['Dezena'] == num]['Correlação'].sum()
            score += impacto_exogeno * 100
            
        # 4. Repetentes da Última Rodada
        ultima_rodada = set(self.df.iloc[-1]['numeros'])
        repetentes = len(set(seq).intersection(ultima_rodada))
        score += 15 if 8 <= repetentes <= 10 else (7 if 7 <= repetentes <= 11 else -10)
        
        return score

    def evoluir(self, qtd_sequencias=1, qtd_numeros=15, geracoes=50, pop_size=100, mutation_rate=0.1):
        """Executa o Algoritmo Genético para encontrar o melhor jogo."""
        
        # Obter correlações exógenas atuais
        df_corr = pd.DataFrame()
        try:
            data_fim = datetime.datetime.now()
            data_inicio = data_fim - datetime.timedelta(days=365)
            _, df_mercado = baixar_dados_financeiros(data_inicio, data_fim)
            if not df_mercado.empty:
                df_full = correlacionar_mercado_loteria(self.df.tail(200), df_mercado)
                df_corr = calcular_correlacao_exogena(df_full)
        except:
            pass
            
        # 1. População Inicial
        populacao = []
        for _ in range(pop_size):
            populacao.append(random.sample(range(1, 26), qtd_numeros))
            
        historico_fitness = []
        
        for g in range(geracoes):
            # 2. Avaliação
            fitness_scores = [self.fitness_function(ind, {}, df_corr) for ind in populacao]
            historico_fitness.append(max(fitness_scores))
            
            # 3. Seleção (Torneio)
            nova_populacao = []
            for _ in range(pop_size // 2):
                # Selecionar 4 aleatórios e pegar o melhor
                idx1, idx2 = random.sample(range(pop_size), 2)
                idx3, idx4 = random.sample(range(pop_size), 2)
                
                pai1 = populacao[idx1] if fitness_scores[idx1] > fitness_scores[idx2] else populacao[idx2]
                pai2 = populacao[idx3] if fitness_scores[idx3] > fitness_scores[idx4] else populacao[idx4]
                
                # 4. Crossover (Troca de dezenas)
                ponto = random.randint(1, qtd_numeros - 1)
                filho1 = list(set(pai1[:ponto] + pai2[ponto:]))
                filho2 = list(set(pai2[:ponto] + pai1[ponto:]))
                
                # Ajustar tamanho se o set removeu duplicados
                while len(filho1) < qtd_numeros:
                    n = random.randint(1, 25)
                    if n not in filho1: filho1.append(n)
                while len(filho1) > qtd_numeros: filho1.pop()
                
                while len(filho2) < qtd_numeros:
                    n = random.randint(1, 25)
                    if n not in filho2: filho2.append(n)
                while len(filho2) > qtd_numeros: filho2.pop()
                    
                nova_populacao.extend([sorted(filho1), sorted(filho2)])
                
            # 5. Mutação
            for ind in nova_populacao:
                if random.random() < mutation_rate:
                    idx_mut = random.randint(0, qtd_numeros - 1)
                    novo_num = random.randint(1, 25)
                    if novo_num not in ind:
                        ind[idx_mut] = novo_num
            
            populacao = nova_populacao
            
        # Resultados Finais - Diversidade Forçada
        # Vamos usar uma abordagem de 'Seleção por Nichos' para garantir que os jogos sejam diferentes
        unique_pop = []
        seen = set()
        for ind in populacao:
            s = tuple(sorted(ind))
            if s not in seen:
                unique_pop.append(list(s))
                seen.add(s)
        
        # Calcular fitness para únicos
        fitness_unique = [self.fitness_function(ind, {}, df_corr) for ind in unique_pop]
        
        # Seleção iterativa priorizando diversidade
        resultados_finais = []
        indices_restantes = list(range(len(unique_pop)))
        
        for _ in range(min(qtd_sequencias, len(unique_pop))):
            melhor_idx = -1
            melhor_score_ajustado = -float('inf')
            
            for i in indices_restantes:
                base_fitness = fitness_unique[i]
                
                # Penalidade de Similaridade: Reduz fitness se for muito parecido com os já escolhidos
                # Queremos maximizar a distância (números diferentes)
                penalidade = 0
                for escolhido in resultados_finais:
                    interseccao = len(set(unique_pop[i]).intersection(set(escolhido['seq'])))
                    # Se tiver mais de 12 números iguais, a penalidade é alta
                    if interseccao >= 13: penalidade += 50
                    elif interseccao >= 11: penalidade += 20
                    elif interseccao >= 10: penalidade += 10
                
                score_ajustado = base_fitness - penalidade
                
                if score_ajustado > melhor_score_ajustado:
                    melhor_score_ajustado = score_ajustado
                    melhor_idx = i
            
            if melhor_idx == -1: break
            
            indices_restantes.remove(melhor_idx)
            seq = sorted(unique_pop[melhor_idx])
            
            # Métricas
            impares = sum(1 for x in seq if x % 2 != 0)
            primos = sum(1 for x in seq if x in self.PRIMOS)
            moldura = sum(1 for x in seq if x in self.MOLDURA)
            fibo = sum(1 for x in seq if x in self.FIBONACCI)
            soma = sum(seq)
            ultima_rodada = set(self.df.iloc[-1]['numeros'])
            repetentes = len(set(seq).intersection(ultima_rodada))
            
            resultados_finais.append({
                'seq': seq,
                'score': int(fitness_unique[melhor_idx]), # Mostramos o score original
                'confianca': min(fitness_unique[melhor_idx] / 2, 100),
                'metrics': {
                    'impares': impares, 'primos': primos, 
                    'moldura': moldura, 'fibo': fibo,
                    'repetentes': repetentes, 'soma': soma
                }
            })
            
        return resultados_finais, historico_fitness

def renderizar_tab_evolutiva(df):
    st.markdown("## 🧬 IA Evolutiva (Algoritmos Genéticos)")
    st.markdown("""
        Esta IA não tenta apenas 'prever' o próximo número. Ela **evolui** uma população de milhares de jogos 
        em busca do 'DNA Perfeito', cruzando o melhor do histórico com as tendências do mercado financeiro e 
        padrões de sinergia entre dezenas.
    """)
    
    col1, col2, col3 = st.columns(3)
    pop_size = col1.slider("Tamanho da População", 50, 500, 200)
    geracoes = col2.slider("Número de Gerações", 10, 200, 100)
    mut_rate = col3.slider("Taxa de Mutação", 0.01, 0.5, 0.1)
    
    qtd_jogos = st.number_input("Quantidade de Jogos a Gerar", 1, 50, 5)
    
    if st.button("🚀 Iniciar Evolução Digital"):
        with st.status("🧬 Evoluindo gerações...", expanded=True) as status:
            engine = EvoEngine(df)
            resultados, historico = engine.evoluir(
                qtd_sequencias=qtd_jogos, 
                geracoes=geracoes, 
                pop_size=pop_size, 
                mutation_rate=mut_rate
            )
            
            st.write("📈 Convergência da Fitness...")
            st.line_chart(historico)
            
            status.update(label="✨ DNA Extraído com Sucesso!", state="complete")
        
        st.markdown("### 🏆 Melhores Indivíduos (Adaptados)")
        
        for i, item in enumerate(resultados):
            r = item['seq']
            m = item['metrics']
            score = item['score']
            
            st.markdown(f"#### Jogo # {i+1} (Fitness: {score})")
            
            html_bolas = ""
            for num in r:
                html_bolas += f"<span style='color: white; background-color: #8e44ad; width: 35px; height: 35px; line-height: 35px; text-align: center; margin: 3px; border-radius: 50%; font-weight: bold; font-size: 14px; display: inline-block'>{num}</span>"
            st.markdown(html_bolas, unsafe_allow_html=True)
            
            st.caption(f"🧬 **Métricas:** {m['impares']} Ímpares | {m['primos']} Primos | {m['moldura']} Moldura | Σ {m['soma']} | {m['repetentes']} Repetidas")
            st.markdown("---")
