import numpy as np
from keras.models import Sequential
from keras.layers import LSTM, Dense
from keras.optimizers import Adam

# Função para preparar os dados para LSTM
# Concatena features simples com vetores de frequências fixos

def preparar_dados(df, intervalo):
    X = []
    y = []

    for i in range(intervalo, len(df)):
        entrada = []

        # Dia par, fim de semana, mês, consecutivos
        entrada.extend([
            int(df.iloc[i - 1]['dia_par']),
            int(df.iloc[i - 1]['fim_de_semana']),
            int(df.iloc[i - 1]['mes']),
            int(df.iloc[i - 1]['consecutivos'])
        ])

        # Frequência dos últimos N dias
        freq_vector = df.iloc[i - 1][[f'freq_{j}' for j in range(1, 26)]].values.tolist()
        entrada.extend(freq_vector)

        X.append(entrada)
        y.append([1 if j in df.iloc[i]['numeros'] else 0 for j in range(1, 26)])

    return np.array(X), np.array(y)

# Função para treinar o modelo

def treinar_modelo(X, y):
    model = Sequential()
    model.add(Dense(64, input_shape=(X.shape[1],), activation='relu'))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(25, activation='sigmoid'))
    model.compile(optimizer=Adam(learning_rate=0.001), loss='binary_crossentropy', metrics=['accuracy'])
    model.fit(X, y, epochs=50, batch_size=16, verbose=0)
    return model

# Função para prever a próxima rodada

def prever_proxima_rodada(model, ultima_entrada, qtd_numeros):
    pred = model.predict(ultima_entrada)[0]
    indices = np.argsort(pred)[-qtd_numeros:][::-1]  # Pega os maiores valores
    return [int(i) + 1 for i in indices]
