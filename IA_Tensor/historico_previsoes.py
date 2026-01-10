import json
import os
import hashlib
from datetime import datetime
import pandas as pd

FILE_PATH = "previsoes.json"

def gerar_hash_sequencia(numeros, timestamp_str):
    """Gera um hash único para a sequência baseado nos números e momento."""
    raw = f"{sorted(numeros)}-{timestamp_str}"
    return hashlib.md5(raw.encode()).hexdigest()

def salvar_previsoes_detalhadas(resultados, df_historico):
    """
    Salva uma lista de previsões com metadados ricos em 'previsoes.json'.
    Args:
        resultados: Lista de dicts {'seq': [], 'score': 0, 'metrics': {}}
        df_historico: DataFrame atual para contexto (último concurso).
    """
    
    # 1. Carregar base existente
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, 'r') as f:
            try:
                base_previsoes = json.load(f)
            except:
                base_previsoes = []
    else:
        base_previsoes = []

    # 2. Contexto do Próximo Concurso (Estimado)
    if not df_historico.empty:
        ultimo_concurso = df_historico.iloc[-1]
        prox_rodada = int(ultimo_concurso['rodada']) + 1
        
        # Tenta estimar data do próximo (apenas heurística, pega data atual de geração)
        data_geracao = datetime.now()
    else:
        prox_rodada = 1
        data_geracao = datetime.now()

    # 3. Processar cada previsão
    novos_registros = []
    
    for item in resultados:
        seq = item['seq']
        metrics = item['metrics']
        score = item['score']
        
        timestamp = data_geracao.isoformat()
        id_unico = gerar_hash_sequencia(seq, timestamp)
        
        # Contexto Temporal Rico
        dia_semana_en = data_geracao.strftime('%A')
        mapa_dias = {"Monday": "Segunda-feira", "Tuesday": "Terça-feira", "Wednesday": "Quarta-feira", "Thursday": "Quinta-feira", "Friday": "Sexta-feira", "Saturday": "Sábado", "Sunday": "Domingo"}
        dia_semana_pt = mapa_dias.get(dia_semana_en, dia_semana_en)
        
        registro = {
            "id": id_unico,
            "timestamp_geracao": timestamp,
            "concurso_alvo_estimado": prox_rodada,
            "numeros": seq,
            "score_ia": score,
            "metrics_dna": metrics,
            "contexto_temporal": {
                "dia_semana": dia_semana_pt,
                "dia": data_geracao.day,
                "mes": data_geracao.month,
                "ano": data_geracao.year,
                "dia_eh_par": data_geracao.day % 2 == 0,
                "semestre": 1 if data_geracao.month <= 6 else 2,
                "trimestre": (data_geracao.month - 1) // 3 + 1
            },
            "status_conferencia": "pendente", # Será atualizado quando sair o resultado real
            "acertos_futuros": None
        }
        
        novos_registros.append(registro)
        
    # 4. Salvar (Append)
    base_previsoes.extend(novos_registros)
    
    with open(FILE_PATH, 'w') as f:
        json.dump(base_previsoes, f, indent=4)
        
    return len(novos_registros)

def renderizar_historico_previsoes_tab():
    import streamlit as st
    st.markdown("## 📜 Memória da IA (Histórico de Previsões)")
    
    if not os.path.exists(FILE_PATH):
        st.info("Nenhuma previsão salva ainda. Gere previsões na aba principal primeiro.")
        return

    with open(FILE_PATH, 'r') as f:
        data = json.load(f)
    
    if not data:
        st.info("Histórico vazio.")
        return
        
    # Converter para DF para facilitar visualização
    df_prev = pd.DataFrame(data)
    df_prev['data_visual'] = pd.to_datetime(df_prev['timestamp_geracao']).dt.strftime('%d/%m/%Y %H:%M')
    
    st.write(f"Total de palpites memorizados: {len(df_prev)}")
    
    # Mostrar os últimos 5
    st.markdown("### Últimas 5 Previsões Geradas")
    for msg in df_prev.tail(5).iloc[::-1].to_dict('records'):
        st.markdown(f"""
        **ID:** `{msg['id'][:8]}...` | 🎯 Alvo: **{msg['concurso_alvo_estimado']}** | 📅 {msg['data_visual']} ({msg['contexto_temporal']['dia_semana']})
        <br>Numbers: **{msg['numeros']}** | Score IA: {msg['score_ia']}
        """, unsafe_allow_html=True)
        st.markdown("---")
