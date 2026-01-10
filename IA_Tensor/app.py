import streamlit as st
import pandas as pd
import json
from datetime import datetime
from lstm import preparar_dados, treinar_modelo, prever_proxima_rodada
from analise_padroes import renderizar_analise_padroes, renderizar_ciclos
import numpy as np
import os
from keras.models import load_model, save_model
from collections import Counter
from desdobramento import renderizar_tab_desdobramento
from backtest import renderizar_tab_lab
import altair as alt
from atualizador import atualizar_dados
import random
from ensemble import treinar_ensemble, prever_ensemble # Segundo Cérebro
from analise_temporal import renderizar_analise_temporal
from montador import renderizar_montador_manual
from analise_conexoes import renderizar_mapa_conexoes
from historico_previsoes import salvar_previsoes_detalhadas
from dashboard_resumo import renderizar_dashboard_resumo

# ... (rest of imports/functions) ...

# ... (rest of imports/functions) ...

# ... inside main logic ...
# (Removed misplaced block)

# ... (rest of imports/functions) ...

# ... (rest of imports/functions) ...

# Função para carregar e filtrar os dados por intervalo de datas
def carregar_dados_json(caminho):
    with open(caminho, 'r') as f:
        dados = json.load(f)
    df = pd.DataFrame(dados)
    df['data'] = pd.to_datetime(df['data'])
    return df

# Frequência de números nos últimos N dias
def contar_frequencias(df, idx, n):
    start = max(0, idx - n)
    subset = df.iloc[start:idx]['numeros'].explode()
    freq = subset.value_counts().to_dict()
    return freq

# Preenche colunas freq_1 a freq_25
def preencher_frequencias(df, n_dias):
    for i in range(len(df)):
        freq_dict = contar_frequencias(df, i, n_dias)
        for num in range(1, 26):
            df.at[i, f'freq_{num}'] = freq_dict.get(num, 0)
    return df

# Função para extrair features adicionais
def extrair_features(df, n_dias):
    df = df.copy()
    df['dia_par'] = df['data'].dt.day % 2 == 0
    df['fim_de_semana'] = df['data'].dt.dayofweek >= 5
    df['mes'] = df['data'].dt.month
    df['consecutivos'] = df['numeros'].apply(lambda x: sum(1 for i in range(len(x)-1) if x[i]+1 == x[i+1]))
    df = preencher_frequencias(df, n_dias)
    return df

st.title("IA - Previsão de Rodada")

# Carregar dados inicialmente GLOBALMENTE
df = carregar_dados_json("rodadas.json")

st.sidebar.header("Parâmetros")

if st.sidebar.button("🔄 Atualizar Base de Dados"):
    if atualizar_dados("rodadas.json"):
        st.cache_data.clear() # Limpa cache se houver
        st.rerun()

data_inicial = st.sidebar.date_input("Data Inicial", value=datetime(2022, 1, 1))
data_final = st.sidebar.date_input("Data Final", value=datetime(2024, 12, 31))
qtd_numeros = st.sidebar.slider("Qtd. de Números", 15, 20, 15)
qtd_sequencias = st.sidebar.number_input("Qtd. de Sequências Geradas", min_value=1, value=1)
n_dias = st.sidebar.number_input("Janela de Análise (dias)", min_value=1, value=30, help="Quantos dias para trás a IA deve analisar para identificar tendências recentes.")

st.sidebar.markdown("---")

# Filtros em Expander para limpar visual
with st.sidebar.expander("🎯 Filtros Avançados (Fixar/Excluir)", expanded=False):
    st.caption("Use para **forçar** ou **proibir** números na previsão.")
    nums_fixos_str = st.text_input("Fixar Números (OBRIGATÓRIOS)", placeholder="Ex: 1, 13, 25")
    nums_excluidos_str = st.text_input("Excluir Números (PROIBIDOS)", placeholder="Ex: 4, 8")

# Conferência em Expander
with st.sidebar.expander("✅ Conferir Resultado & Treinar", expanded=False):
    st.caption("Selecione um concurso passado para **comparar** com a previsão e **re-treinar**.")
    
    # Montar lista de opções (ex: "Concurso 3000 - 20/05/2024")
    opcoes_concursos = df.sort_values("rodada", ascending=False).apply(
        lambda x: f"{x['rodada']} - {x['data'].strftime('%d/%m/%Y')}", axis=1
    )
    
    concurso_str = st.selectbox("Escolher Concurso para Validar", ["(Nenhum)"] + list(opcoes_concursos))
    
    sequencia_correta_auto = None
    if concurso_str != "(Nenhum)":
        num_concurso = int(concurso_str.split(" - ")[0])
        # Pegar os números desse concurso
        row_sel = df[df['rodada'] == num_concurso].iloc[0]
        sequencia_correta_auto = row_sel['numeros']
        st.info(f"Gabarito carregado: {sequencia_correta_auto}")


usar_aprendizado = st.sidebar.checkbox("Usar aprendizado persistente", value=False)
salvar_aprendizado = st.sidebar.checkbox("Salvar aprendizado após execução", value=False)

tab_previsao, tab_analise, tab_montador, tab_desdobra, tab_lab = st.tabs(["🔮 Previsão", "📊 Análise", "🏗️ Montador", "🔢 Desdobrador", "🧪 Laboratório"])

# Filtrar dados para análise baseado no sidebar definido acima
df_filtrado_analise = df[(df['data'] >= pd.to_datetime(data_inicial)) & (df['data'] <= pd.to_datetime(data_final))].reset_index(drop=True)

with tab_analise:
    # Passamos o DF completo para a função, pois ela agora tem filtros próprios
    renderizar_analise_padroes(df)
    renderizar_ciclos(df)
    renderizar_analise_temporal(df)
    renderizar_mapa_conexoes(df)

with tab_montador:
    renderizar_montador_manual(df)

with tab_desdobra:
    renderizar_tab_desdobramento()

with tab_lab:
    renderizar_tab_lab(df, int(n_dias))

with tab_previsao:
    renderizar_dashboard_resumo(df)
    
    c1, c2 = st.columns(2)
    btn_ia = c1.button("🔮 Previsão IA")
    btn_random = c2.button("🎲 Gerar 100% Aleatório")

    if btn_random:
        st.markdown("### 🎲 Surpresinha (Aleatória)")
        resultados = []
        # --- CONSTANTES MATEMÁTICAS ---
        PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}
        MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
        FIBONACCI = {1, 2, 3, 5, 8, 13, 21}
        
        ultima_rodada = set(df.iloc[-1]['numeros'])

        for _ in range(qtd_sequencias):
             # Geração puramente aleatória
             seq = sorted(random.sample(range(1, 26), qtd_numeros))
             
             # Métricas
             impares = sum(1 for x in seq if x % 2 != 0)
             primos = sum(1 for x in seq if x in PRIMOS)
             moldura = sum(1 for x in seq if x in MOLDURA)
             fibo = sum(1 for x in seq if x in FIBONACCI)
             soma = sum(seq)
             repetentes = len(set(seq).intersection(ultima_rodada))
             
             resultados.append({
                'seq': seq,
                'score': 0, 
                'metrics': {
                    'impares': impares, 'primos': primos, 
                    'moldura': moldura, 'fibo': fibo,
                    'repetentes': repetentes, 'soma': soma
                }
             })
        
        # --- VISUALIZAÇÃO COM ORDENAÇÃO ---
        correta_set = set(sequencia_correta_auto) if sequencia_correta_auto else None
        
        # Calcular acertos e ordenar se houver gabarito
        if correta_set:
            for item in resultados:
                item['acertos'] = len(set(item['seq']).intersection(correta_set))
            
            # Ordenar: Mais acertos primeiro.
            resultados.sort(key=lambda x: x['acertos'], reverse=True)
            
            st.markdown(f"### 📝 Comparando com Concurso {concurso_str}")
            st.caption(f"Gabarito Oficial: {sorted(sequencia_correta_auto)}")

        for i, item in enumerate(resultados):
            r = item['seq']
            m = item['metrics']
            
            # Label de acertos
            acertos_label = ""
            if correta_set:
                acertos = item.get('acertos', 0)
                acertos_label = f" | 🎯 Acertos: {acertos}/15"
            
            st.markdown(f"### Jogo Aleatório {i+1} <small>{acertos_label}</small>", unsafe_allow_html=True)
            
            # HTML das Bolinhas
            html_bolas = ""
            for num in r:
                if correta_set:
                    style = "color: white; background-color: #2ecc71; border: 1px solid #27ae60" if num in correta_set else "color: white; background-color: #e74c3c; border: 1px solid #c0392b"
                else:
                    style = "color: black; background-color: #f0f2f6; border: 1px solid #d0d0d0"
                
                html_bolas += f"<span style='{style}; width: 40px; height: 40px; line-height: 40px; text-align: center; margin: 4px; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block'>{num}</span>"
            
            st.markdown(html_bolas, unsafe_allow_html=True)
            st.caption(f"🧬 **DNA:** {m['impares']} Ímpares | {m['primos']} Primos | 🖼️ **{m['moldura']} Moldura** | 🌀 **{m['fibo']} Fibonacci** | ♻️ {m['repetentes']} Repetidas | Σ {m['soma']}")
            st.markdown("---")

        # Salvar para desdobrador
        if resultados:
            st.session_state.ultima_previsao = resultados[0]['seq']

    if btn_ia:
        try:
            # Usamos o mesmo df filtrado ou recarregamos se necessário (aqui reusamos)
            df_filtrado = df_filtrado_analise

            if df_filtrado.empty:
                st.error("Nenhuma rodada no intervalo selecionado.")
            else:
                df_feat = extrair_features(df_filtrado, int(n_dias))
                entradas, saidas = preparar_dados(df_feat, intervalo=int(n_dias))

                modelo = None
                if usar_aprendizado and os.path.exists("modelo_treinado.keras"):
                    modelo = load_model("modelo_treinado.keras")
                    st.info("Modelo carregado com aprendizado anterior.")
                else:
                    modelo = treinar_modelo(entradas, saidas)

                # --- CÁLCULO DE PROBABILIDADE HÍBRIDA ---
                
                # --- 1. MODELO LSTM (Deep Learning) ---
                pred_lstm = modelo.predict(entradas[-1][None, ...])[0]
                
                # --- 2. MODELO ENSEMBLE (Random Forest - Segundo Cérebro) ---
                if 'modelo_rf' not in st.session_state or not usar_aprendizado:
                    with st.spinner("🌲 Cultivando Árvore de Decisões (Segundo Cérebro)..."):
                        st.session_state.modelo_rf = treinar_ensemble(df_filtrado)
                
                pred_ensemble = prever_ensemble(st.session_state.modelo_rf, df_filtrado)

                # --- 3. ESTATÍSTICA (Frequência) ---
                # Pega os últimos 10 concursos do dataframe filtrado
                ultimos_10 = df_filtrado.tail(10)
                freq_contador = Counter()
                for nums in ultimos_10['numeros']:
                    freq_contador.update(nums)
                
                # Vetor de frequência normalizado (0 a 1)
                prob_freq = np.zeros(25)
                max_freq = 10 # teorico
                for num in range(1, 26):
                    prob_freq[num-1] = freq_contador.get(num, 0) / max_freq

                # --- 4. ESTATÍSTICA (Atraso) ---
                prob_atraso = np.zeros(25)
                ultima_rodada_abs = df_filtrado['rodada'].max()
                for num in range(1, 26):
                    # Acha a última vez que o numero saiu
                    ocorrencias = df_filtrado[df_filtrado['numeros'].apply(lambda x: num in x)]
                    if not ocorrencias.empty:
                        ultimo_visto = ocorrencias['rodada'].max()
                        atraso = ultima_rodada_abs - ultimo_visto
                        # Sigmoid simples para limitar o boost de atraso (max 0.2)
                        prob_atraso[num-1] = min(atraso * 0.02, 0.2)
                    else:
                        prob_atraso[num-1] = 0.2 # Se nunca saiu, força máxima
                
                # === FUSÃO DE INTELIGÊNCIAS (ENSEMBLE HÍBRIDO) ===
                # Pesos Balanceados:
                # 40% Rede Neural (Padrões Sequenciais Longos)
                # 40% Random Forest (Regras de Decisão Complexas)
                # 10% Frequência Recente (Momento)
                # 10% Atraso (Correção Estatística)
                prob_final = (pred_lstm * 0.40) + (pred_ensemble * 0.40) + (prob_freq * 0.10) + (prob_atraso * 0.10)
                
                # Aplicar Filtros Manuais (Hardware Override)
                nums_fixos = set()
                nums_excluidos = set()
                
                if nums_fixos_str:
                    try:
                        nums_fixos = {int(x.strip()) for x in nums_fixos_str.split(',') if x.strip().isdigit()}
                    except: pass
                    
                if nums_excluidos_str:
                    try:
                        nums_excluidos = {int(x.strip()) for x in nums_excluidos_str.split(',') if x.strip().isdigit()}
                    except: pass
                
                # Zerar probabilidade dos excluídos e boost nos fixos
                for n in nums_excluidos:
                    if 1 <= n <= 25: prob_final[n-1] = 0
                
                for n in nums_fixos:
                     if 1 <= n <= 25: prob_final[n-1] = 100 # Força bruta

                # Normalizar final
                probabilidades = prob_final / np.sum(prob_final)

                # --- HEATMAP VISUAL (Frio vs Quente) ---
                st.markdown("### 🌡️ Mapa de Calor (Previsão da IA)")
                
                # Montar Grid 5x5
                heatmap_data = []
                for i in range(5):
                    for j in range(5):
                        num = i * 5 + j + 1
                        prob = probabilidades[num-1]
                        heatmap_data.append({'x': j, 'y': i, 'Número': num, 'Probabilidade': prob})
                
                df_heat = pd.DataFrame(heatmap_data)
                
                chart_heat = alt.Chart(df_heat).mark_rect().encode(
                    x=alt.X('x:O', axis=None, scale=alt.Scale(padding=0.05)),
                    y=alt.Y('y:O', axis=None, scale=alt.Scale(padding=0.05)),
                    color=alt.Color('Probabilidade:Q', scale=alt.Scale(scheme='turbo'), legend=None),
                    tooltip=['Número', alt.Tooltip('Probabilidade', format='.2%')]
                ).properties(width=300, height=300)
                
                text_heat = chart_heat.mark_text().encode(
                    text='Número:O',
                    color=alt.value('black')
                )
                
                st.altair_chart(chart_heat + text_heat, use_container_width=True)

                # === LÓGICA AVANÇADA DE GERAÇÃO E FILTRAGEM ===
                resultados = []
                candidatos = []
                
                # Constantes para análise
                PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}
                MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
                FIBONACCI = {1, 2, 3, 5, 8, 13, 21}
                ultima_rodada = set(df_filtrado.iloc[-1]['numeros'])
                
                # Gerar um pool grande de candidatos
                pool_size = max(qtd_sequencias * 50, 500) 
                
                status_placeholder = st.empty()
                status_placeholder.info(f"🧠 Processando IA Híbrida + Filtros... Gerando {pool_size} simulações.")
                
                for _ in range(pool_size):
                    escolhidos = set(nums_fixos) # Começa com os fixos
                    
                    # Se fixos já preenchem tudo ou estouram, ajusta
                    if len(escolhidos) > qtd_numeros:
                        escolhidos = set(list(escolhidos)[:qtd_numeros])
                    
                    tries = 0
                    while len(escolhidos) < qtd_numeros and tries < 100:
                        # Sorteio ponderado pelas probabilidades da IA Híbrida
                        num = np.random.choice(np.arange(1, 26), p=probabilidades)
                        if num not in nums_excluidos:
                            escolhidos.add(num)
                        tries += 1
                        
                    # Fallback caso não consiga gerar (ex: muitos excluidos)
                    if len(escolhidos) < qtd_numeros:
                        remaining = list(set(range(1,26)) - escolhidos - nums_excluidos)
                        if remaining:
                            needed = qtd_numeros - len(escolhidos)
                            escolhidos.update(remaining[:needed])
                    
                    seq = sorted(escolhidos)
                    
                    # Calcular Pontuação (Score de Equilíbrio)
                    # Score Máximo Teórico: 8 + 4 (novos) = 12
                    score = 0
                    
                    # 1. Ímpares (Ideal: 7 a 9)
                    impares = sum(1 for x in seq if x % 2 != 0)
                    if 7 <= impares <= 9: score += 2
                    elif 6 <= impares <= 10: score += 1
                    
                    # 2. Primos (Ideal: 4 a 6)
                    primos = sum(1 for x in seq if x in PRIMOS)
                    if 4 <= primos <= 6: score += 2
                    elif 3 <= primos <= 7: score += 1
                    
                    # 3. Repetentes do Anterior (Ideal: 8 a 10)
                    repetentes = len(set(seq).intersection(ultima_rodada))
                    if 8 <= repetentes <= 10: score += 3 # Peso maior para repetentes
                    elif 7 <= repetentes <= 11: score += 1
                    
                    # 4. Soma (Ideal: 180 a 220, aproximado para 15 numeros)
                    soma = sum(seq)
                    if 180 <= soma <= 220: score += 1

                    # 5. Moldura (Ideal: 8 a 11)
                    moldura = sum(1 for x in seq if x in MOLDURA)
                    if 9 <= moldura <= 10: score += 2 # Ouro
                    elif 8 <= moldura <= 11: score += 1

                    # 6. Fibonacci (Ideal: 3 a 5)
                    fibo = sum(1 for x in seq if x in FIBONACCI)
                    if 4 == fibo: score += 2    # Ouro
                    elif 3 <= fibo <= 5: score += 1
                    
                    candidatos.append({
                        'seq': seq, 
                        'score': score, 
                        'metrics': {
                            'impares': impares, 'primos': primos, 
                            'moldura': moldura, 'fibo': fibo,
                            'repetentes': repetentes, 'soma': soma
                        }
                    })
                
                status_placeholder.empty()

                # Ordenar pelos melhores scores
                candidatos.sort(key=lambda x: x['score'], reverse=True)
                
                # Pegar os top 25% melhores para manter variedade
                top_cut = max(len(candidatos) // 4, qtd_sequencias)
                melhores_candidatos = candidatos[:top_cut]
                
                # Selecionar aleatoriamente dentre os melhores
                indices_finais = np.random.choice(len(melhores_candidatos), qtd_sequencias, replace=False)
                
                for idx in indices_finais:
                    resultados.append(melhores_candidatos[idx]) # Guarda o objeto completo com métricas

                st.success(f"Previsões geradas com sucesso! (Selecionadas as melhores de {pool_size} simulações)")
                
                # --- MEMÓRIA DA IA (Salvar para aprendizado futuro) ---
                try:
                    qtd_salva = salvar_previsoes_detalhadas(resultados, df)
                    st.toast(f"💾 {qtd_salva} palpites memorizados no Histórico com Meta-Dados Completos!")
                except Exception as e:
                    st.error(f"Erro ao salvar histórico: {e}")
                
                # Salvar a melhor sequência (primeira) na sessão para o desdobrador
                if resultados:
                    st.session_state.ultima_previsao = resultados[0]['seq']

                # Se tiver gabarito, prepara conjunto para comparação
                correta_set = set(sequencia_correta_auto) if sequencia_correta_auto else None
                
                # Calcular acertos e ordenar se houver gabarito
                if correta_set:
                    for item in resultados:
                        item['acertos'] = len(set(item['seq']).intersection(correta_set))
                    
                    # Ordenar IA: Mais acertos primeiro, depois maior Score.
                    resultados.sort(key=lambda x: (x['acertos'], x['score']), reverse=True)
                    
                    st.markdown(f"### 📝 Comparando com Concurso {concurso_str}")
                    st.caption(f"Gabarito Oficial: {sorted(sequencia_correta_auto)}")
                
                for i, item in enumerate(resultados):
                    r = item['seq']
                    m = item['metrics']
                    score = item['score']
                    
                    # Título da Sequência
                    acertos_label = ""
                    if correta_set:
                        acertos = item.get('acertos', 0)
                        acertos_label = f" | 🎯 Acertos: {acertos}/15"
                    
                    st.markdown(f"### Sequência {i+1} <small>(Score: {score}/13{acertos_label})</small>", unsafe_allow_html=True)
                    
                    # HTML das Bolinhas
                    html_bolas = ""
                    for num in r:
                        if correta_set:
                            if num in correta_set:
                                # Acertou (Verde)
                                style = "color: white; background-color: #2ecc71; border: 1px solid #27ae60"
                            else:
                                # Errou (Vermelho)
                                style = "color: white; background-color: #e74c3c; border: 1px solid #c0392b"
                        else:
                            # Padrão (Cinza Claro)
                            style = "color: black; background-color: #f0f2f6; border: 1px solid #d0d0d0"
                        
                        html_bolas += f"<span style='{style}; width: 40px; height: 40px; line-height: 40px; text-align: center; margin: 4px; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block'>{num}</span>"
                    
                    st.markdown(html_bolas, unsafe_allow_html=True)
                    
                    # Exibir métricas da sequência
                    st.caption(f"🧬 **DNA:** {m['impares']} Ímpares | {m['primos']} Primos | 🖼️ **{m['moldura']} Moldura** | 🌀 **{m['fibo']} Fibonacci** | ♻️ {m['repetentes']} Repetidas | Σ {m['soma']}")
                    st.markdown("---")

                # Aprendizado contínuo (fica fora do loop visual)
                if sequencia_correta_auto:
                    try:
                        # Treinar apenas uma vez com o gabarito
                        correta = sorted(sequencia_correta_auto)
                        correta_bin = np.zeros(25)
                        for num in correta:
                            correta_bin[num - 1] = 1
                        
                        # Treino rápido
                        modelo.fit(entradas[-1][None, ...], correta_bin[None, ...], epochs=3, verbose=0)
                        st.success(f"🧠 Modelo re-treinado com o resultado do concurso {concurso_str}!")
                    except Exception as e:
                        st.error(f"Erro no treino online: {e}")

                if salvar_aprendizado:
                    save_model(modelo, "modelo_treinado.keras")
                    st.success("Modelo salvo com aprendizado persistente.")
        except Exception as e:
            st.error(f"Erro: {str(e)}")
