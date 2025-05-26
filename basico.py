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


# frenquencias
freq = df_long["numero"].value_counts().sort_index()
rel = freq / freq.sum()

print("Frequências absolutas:\n", freq)
print("\nFrequências relativas:\n", rel)
################################################

# jaccard entre conjuntos de números consecutivos
sets = df_wide.set_index("rodada")[[*range(1,26)]].apply(lambda row: set(np.where(row==1)[0]+1), axis=1)
jacc = []
for i in range(2, sets.index.max()+1):
    A, B = sets.loc[i-1], sets.loc[i]
    jacc.append({"rod_prev":i-1, "rod":i, "jaccard": len(A&B)/len(A|B)})
jacc_df = pd.DataFrame(jacc)
print(jacc_df.describe())

# jaccard entre conjuntos de números consecutivos
sets = df_wide.set_index("rodada")[[*range(1,26)]].apply(lambda row: set(np.where(row==1)[0]+1), axis=1)
jacc = []
for i in range(2, sets.index.max()+1):
    A, B = sets.loc[i-1], sets.loc[i]
    jacc.append({"rod_prev":i-1, "rod":i, "jaccard": len(A&B)/len(A|B)})
jacc_df = pd.DataFrame(jacc)
print(jacc_df.describe())
#######################################################################



#Matriz de co-ocorrência (pares de números)
co = np.zeros((25,25), dtype=int)
for s in sets:
    for i in s:
        for j in s:
            co[i-1,j-1] += 1

# transforma em DataFrame
co_df = pd.DataFrame(co, index=range(1,26), columns=range(1,26))
# exemplo: top 10 pares mais frequentes (i<j)
pairs = []
for i in range(25):
    for j in range(i+1,25):
        pairs.append((i+1,j+1, co[i,j]))
top = sorted(pairs, key=lambda x: x[2], reverse=True)[:10]
print("Top 10 pares:", top)
##########################################################

# P(j|i) = co[i,j] / freq[i]
freq_arr = freq.values
cond = co / freq_arr[:,None]  # divisão linha a linha
cond_df = pd.DataFrame(cond, index=range(1,26), columns=range(1,26))
print("P(j|i) exemplo linha 7:\n", cond_df.loc[7].sort_values(ascending=False).head())
#################################

