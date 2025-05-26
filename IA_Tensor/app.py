import streamlit as st
import pandas as pd
import json
from datetime import datetime
from lstm import preparar_dados, treinar_modelo, prever_proxima_rodada
import numpy as np
import os
from keras.models import load_model, save_model

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

st.sidebar.header("Parâmetros")
data_inicial = st.sidebar.date_input("Data Inicial", value=datetime(2022, 1, 1))
data_final = st.sidebar.date_input("Data Final", value=datetime(2024, 12, 31))
qtd_numeros = st.sidebar.slider("Qtd. de Números", 15, 17, 15)
qtd_sequencias = st.sidebar.number_input("Qtd. de Sequências Geradas", min_value=1, value=1)
n_dias = st.sidebar.number_input("Frequência (últimos N dias)", min_value=1, value=30)
sequencia_correta = st.sidebar.text_input("Sequência Correta (separada por vírgula, opcional)")

usar_aprendizado = st.sidebar.checkbox("Usar aprendizado persistente", value=False)
salvar_aprendizado = st.sidebar.checkbox("Salvar aprendizado após execução", value=False)

if st.button("Executar Previsão"):
    try:
        df = carregar_dados_json("rodadas.json")
        df_filtrado = df[(df['data'] >= pd.to_datetime(data_inicial)) & (df['data'] <= pd.to_datetime(data_final))].reset_index(drop=True)

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

            # Obtemos as probabilidades com uma única predição
            pred = modelo.predict(entradas[-1][None, ...])[0]
            probabilidades = pred / np.sum(pred)  # normaliza para somar 1

            resultados = []
            usadas = set()

            for _ in range(qtd_sequencias):
                # Sorteia sem repetição para diversificar entre as sequências
                escolhidos = set()
                tentativa = 0
                while len(escolhidos) < qtd_numeros and tentativa < 50:
                    num = np.random.choice(np.arange(1, 26), p=probabilidades)
                    if num not in escolhidos:
                        escolhidos.add(num)
                    tentativa += 1

                resultados.append(sorted(escolhidos))


            st.success("Previsões geradas com sucesso!")
            for i, r in enumerate(resultados):
                st.markdown(f"### Sequência {i+1}:")
                st.markdown(
                    ' '.join([f"<span style='color: black; background-color: lightgray; padding: 4px; margin: 2px; border-radius: 5px'>{num}</span>" for num in r]),
                    unsafe_allow_html=True
                )

            if sequencia_correta:
                try:
                    correta = sorted(map(int, sequencia_correta.split(',')))
                    st.markdown("### Comparação com Sequência Correta")
                    st.markdown(f"Sequência Correta: {correta}")
                    correta_set = set(correta)
                    for i, r in enumerate(resultados):
                        acertos = set(r).intersection(correta_set)
                        st.markdown(f"**Sequência {i+1} acertou {len(acertos)} números:**")
                        st.markdown(
                            ' '.join([
                                f"<span style='color: white; background-color: green; padding: 4px; margin: 2px; border-radius: 5px'>{num}</span>"
                                if num in correta_set else
                                f"<span style='color: white; background-color: red; padding: 4px; margin: 2px; border-radius: 5px'>{num}</span>"
                                for num in r
                            ]),
                            unsafe_allow_html=True
                        )

                    # Aprendizado contínuo com sequência correta
                    correta_bin = np.zeros(25)
                    for num in correta:
                        correta_bin[num - 1] = 1
                    modelo.fit(entradas[-1][None, ...], correta_bin[None, ...], epochs=3, verbose=0)
                    st.markdown("🧠 Modelo ajustado com a sequência correta.")
                except:
                    st.warning("Sequência correta informada está em formato inválido. Use números separados por vírgula.")

            if salvar_aprendizado:
                save_model(modelo, "modelo_treinado.keras")
                st.success("Modelo salvo com aprendizado persistente.")

    except Exception as e:
        st.error(f"Erro: {str(e)}")
