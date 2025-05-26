from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.metrics import jaccard_score
import json
import pandas as pd
import numpy as np
from datetime import datetime

# carrega JSON já normalizado
with open("rodadas_normalizadas.json","r",encoding="utf-8") as f:
    dados = json.load(f)

# dataframe “long”: cada linha = um número numa rodada
rows = []
for d in dados:
    for num in d["numeros"]:
        rows.append({
            "rodada": d["rodada"],
            "data":  datetime.strptime(d["data"],"%Y-%m-%d"),
            "numero": num
        })
df_long = pd.DataFrame(rows)

# dataframe “wide”: colunas 1…25 = 0/1 presença do número
df_wide = (df_long
           .assign(valor=1)
           .pivot_table(index=["rodada","data"], columns="numero", values="valor", fill_value=0)
           .reset_index()
          )



# features X = presença rodada-1; y = presença rodada atual
df_feat = df_wide.sort_values("rodada")
X = df_feat[[*range(1,26)]].shift(1).fillna(0).astype(int).values
y = df_feat[[*range(1,26)]].values

# descarta primeira linha (sem lag)
X, y = X[1:], y[1:]

Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)

clf = MultiOutputClassifier(RandomForestClassifier(n_estimators=100, random_state=42))
clf.fit(Xtr, ytr)
y_pred = clf.predict(Xte)

print("Jaccard média:", jaccard_score(yte, y_pred, average="samples"))


from sklearn.linear_model import LogisticRegression
clf2 = MultiOutputClassifier(LogisticRegression(max_iter=1000))
clf2.fit(Xtr, ytr)
y_prob = clf2.predict_proba(Xte)  # lista de 25 arrays
# P(número i sai) = y_prob[i][:,1]
probs = np.array([p[:,1] for p in y_prob]).T  # shape (n_amostras,25)
print("Prob média saída do nº 1:", probs[:,0].mean())
print("Prob média saída do nº 2:", probs[:,1].mean())