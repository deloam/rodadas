from preprocessamento import carregar_dados, preparar_sequencias, normalizar
from modelo_lstm import construir_modelo
from sklearn.metrics import accuracy_score
import numpy as np

# parâmetros configuráveis
ANO_TREINO = 2025
DATA_LIMITE = "2025-12-31"

# carregar e preparar dados
numeros = carregar_dados("rodadas.csv", ano=ANO_TREINO)
X, y = preparar_sequencias(numeros)
X, scaler = normalizar(X)   

# treinar
modelo = construir_modelo((X.shape[1],))
modelo.fit(X, y, epochs=50, batch_size=16)

# prever próxima
entrada = X[-1].reshape(1, -1)
predicao = modelo.predict(entrada)[0]
preditos = np.round(predicao).astype(int)
preditos = np.clip(preditos, 1, 25)
print("Números previstos:", np.unique(preditos))
