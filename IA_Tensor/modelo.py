import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split

# Parâmetros
SEQUENCIA = 10  # usar 10 rodadas anteriores para prever a próxima
TOTAL_NUMEROS = 25

# Cria uma matriz de shape (n amostras, 10, 25) com one-hot dos últimos 10 sorteios
def preparar_sequencias(df):
    X = []
    y = []

    for i in range(SEQUENCIA, len(df)):
        ultimos_sorteios = df.iloc[i-SEQUENCIA:i, -15:]
        proximo_sorteio = df.iloc[i, -15:]

        x_seq = np.zeros((SEQUENCIA, TOTAL_NUMEROS))
        y_seq = np.zeros(TOTAL_NUMEROS)

        for t, linha in enumerate(ultimos_sorteios.values):
            for n in linha:
                x_seq[t, n-1] = 1

        for n in proximo_sorteio:
            y_seq[n-1] = 1

        X.append(x_seq)
        y.append(y_seq)

    return np.array(X), np.array(y)

X, y = preparar_sequencias(df)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# Modelo LSTM
model = Sequential([
    LSTM(64, return_sequences=False, input_shape=(SEQUENCIA, TOTAL_NUMEROS)),
    Dropout(0.2),
    Dense(64, activation='relu'),
    Dense(TOTAL_NUMEROS, activation='sigmoid')  # saída de probabilidade para os 25 números
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

model.fit(X_train, y_train, epochs=20, batch_size=32, validation_split=0.1)
