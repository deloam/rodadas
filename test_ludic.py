import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta

# Carregar base Lotofácil
with open('IA_Tensor/rodadas.json', 'r') as f:
    data = json.load(f)

df_loto = pd.DataFrame(data)
df_loto['data_dt'] = pd.to_datetime(df_loto['data'], format='%d/%m/%Y')
df_loto['soma'] = df_loto['numeros'].apply(sum)

# Carregar DB Financeiro
conn_fin = sqlite3.connect("previsoes.db")
try:
    df_fin = pd.read_sql("SELECT * FROM historico_financeiro WHERE ticker='^BVSP'", conn_fin)
    df_fin['data_dt'] = pd.to_datetime(df_fin['data'])
    df_fin = df_fin.sort_values('data_dt')
except:
    df_fin = pd.DataFrame()

# Carregar DB Futebol
conn_fut = sqlite3.connect("futebol.db")
try:
    df_fut = pd.read_sql("SELECT * FROM historico_futebol", conn_fut)
    df_fut['data_dt'] = pd.to_datetime(df_fut['data'], format='%Y%m%d')
except:
    df_fut = pd.DataFrame()

print("=== TEORIA: A SEMANA SANGRENTA DA BOLSA PADRONIZA OS JOGOS? ===")
if not df_fin.empty:
    # Calcular se a semana anterior fechou negativa
    df_fin['semana'] = df_fin['data_dt'].dt.isocalendar().week
    df_fin['ano'] = df_fin['data_dt'].dt.year
    semanas = df_fin.groupby(['ano', 'semana']).agg(
        abertura=('fechamento', 'first'),
        fechamento_final=('fechamento', 'last')
    ).reset_index()
    semanas['semana_negativa'] = semanas['fechamento_final'] < semanas['abertura']
    
    # Merge loto
    df_loto['semana_anterior'] = (df_loto['data_dt'].dt.isocalendar().week - 1)
    # Tratar virada de ano
    df_loto.loc[df_loto['semana_anterior'] == 0, 'semana_anterior'] = 52
    
    df_cl = pd.merge(df_loto, semanas, left_on=['data_dt', 'semana_anterior'], right_on=['ano', 'semana'], how='left')
    
    stats = df_cl.groupby('semana_negativa')['soma'].mean()
    print("Média de Soma Lotofácil quando a semana ANTERIOR da Bolsa foi:")
    print(stats)
else:
    print("Sem dados locais de bolsa para testar.")

print("\\n=== TEORIA: QUANDO OS GRANDES PERDEM, O JOGO FICA LOUCO? ===")
if not df_fut.empty:
    # Ligar dia do sorteio com o dia anterior do futebol
    df_loto['data_ontem'] = df_loto['data_dt'] - pd.Timedelta(days=1)
    df_cl_fut = pd.merge(df_loto, df_fut, left_on='data_ontem', right_on='data_dt', how='inner')
    
    # A ira flamenguista (1=Ganhou, -1=Perdeu, 0=Empatou)
    if 'fla_status' in df_cl_fut.columns:
        stats_fla = df_cl_fut.groupby('fla_status')['soma'].mean()
        print("Soma Média da Lotofácil no dia SEGUINTE ao jogo do Flamengo:")
        print("Perdeu (-1):", stats_fla.get(-1.0, 0))
        print("Empatou (0):", stats_fla.get(0.0, 0))
        print("Ganhou (1):", stats_fla.get(1.0, 0))
        
        df_cl_fut['impares'] = df_cl_fut['numeros'].apply(lambda x: sum(1 for n in x if n%2!=0))
        stats_fla_i = df_cl_fut.groupby('fla_status')['impares'].mean()
        print("Média de Ímpares:")
        print(stats_fla_i)
else:
    print("Sem dados locais de futebol.")
