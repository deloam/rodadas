import numpy as np
from keras.models import Sequential
from keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler

def preparar_dados(df, intervalo=30):
    features = df.drop(columns=['data', 'numeros'])
    scaler = MinMaxScaler()
    X = scaler.fit_transform(features)
    
    entradas = []
    saidas = []

    for i in range(intervalo, len(X)):
        entradas.append(X[i - intervalo:i])
        # Convertendo lista de números sorteados em vetor binário
        y = np.zeros(25)
        for num in df.iloc[i]['numeros']:
            y[num - 1] = 1
        saidas.append(y)

    return np.array(entradas), np.array(saidas)

def treinar_modelo(X, y):
    modelo = Sequential()
    modelo.add(LSTM(64, input_shape=(X.shape[1], X.shape[2]), return_sequences=False))
    modelo.add(Dense(25, activation='sigmoid'))  # 25 números possíveis
    modelo.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    modelo.fit(X, y, epochs=30, batch_size=16, verbose=0)
    return modelo

def prever_proxima_rodada(modelo, entrada, qtd_numeros=15):
    pred = modelo.predict(entrada)[0]
    indices = np.argsort(pred)[-qtd_numeros:]
    return [i + 1 for i in sorted(indices)]
