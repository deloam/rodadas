import json
import os
import hashlib
from datetime import datetime
import pandas as pd
import numpy as np

FILE_PATH = "previsoes.json"

def gerar_hash_sequencia(numeros, timestamp_str):
    """Gera um hash único para a sequência baseado nos números e momento."""
    raw = f"{sorted(numeros)}-{timestamp_str}"
    return hashlib.md5(raw.encode()).hexdigest()

class NumpyEncoder(json.JSONEncoder):
    """Encoder personalizado para resolver problemas de int64 do Numpy no JSON"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

def salvar_previsoes_detalhadas(resultados, df_historico):
    """
    Salva uma lista de previsões com metadados ricos em 'previsoes.json'.
    Args:
        resultados: Lista de dicts {'seq': [], 'score': 0, 'metrics': {}}
        df_historico: DataFrame atual para contexto (último concurso).
    """
    
    # 1. Carregar base existente
    if os.path.exists(FILE_PATH):
        try:
            with open(FILE_PATH, 'r') as f:
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
        # CONVERSÃO CRÍTICA: Garantir tipos nativos do Python (evita erro JSON serializable com numpy)
        seq = [int(n) for n in item['seq']] # Converte numpy.int64 para int
        metrics = {k: int(v) if isinstance(v, (int, np.integer)) else float(v) for k,v in item['metrics'].items()}
        score = float(item['score'])
        
        timestamp = data_geracao.isoformat()
        id_unico = gerar_hash_sequencia(seq, timestamp)
        
        # Contexto Temporal Rico
        dia_semana_en = data_geracao.strftime('%A')
        mapa_dias = {"Monday": "Segunda-feira", "Tuesday": "Terça-feira", "Wednesday": "Quarta-feira", "Thursday": "Quinta-feira", "Friday": "Sexta-feira", "Saturday": "Sábado", "Sunday": "Domingo"}
        dia_semana_pt = mapa_dias.get(dia_semana_en, dia_semana_en)
        
        registro = {
            "id": id_unico,
            "timestamp_geracao": timestamp,
            "concurso_alvo_estimado": int(prox_rodada), # Garante int puro
            "numeros": seq,
            "score_ia": score,
            "metrics_dna": metrics,
            "contexto_temporal": {
                "dia_semana": dia_semana_pt,
                "dia": int(data_geracao.day),
                "mes": int(data_geracao.month),
                "ano": int(data_geracao.year),
                "dia_eh_par": bool(data_geracao.day % 2 == 0),
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
        json.dump(base_previsoes, f, indent=4, cls=NumpyEncoder)
        
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
        # Formatar status
        if msg.get('status_conferencia') == 'conferido':
            hits = msg.get('acertos_futuros', 0)
            badge = f"✅ {hits} acertos" if hits >= 11 else f"❌ {hits} acertos"
        else:
            badge = "⏳ Pendente"

        st.markdown(f"""
        **ID:** `{msg['id'][:8]}...` | 🎯 Alvo: **{msg['concurso_alvo_estimado']}** | {badge} | 📅 {msg['data_visual']}
        <br>Numbers: **{msg['numeros']}** | Score IA: {msg['score_ia']}
        """, unsafe_allow_html=True)
        st.markdown("---")

def executar_retro_analise(df_historico):
    """
    Verifica se os palpites passados já têm resultado oficial.
    Se tiver > 20 palpites conferidos, gera insights de calibragem.
    """
    if not os.path.exists(FILE_PATH): return None

    with open(FILE_PATH, 'r') as f:
        previsoes = json.load(f)
    
    atualizou = False
    conferidos_count = 0
    total_acertos = 0
    
    # Cache dos resultados oficiais para performance
    # Dict: {1234: {1, 2, ...}, 1235: {...}}
    gabaritos = {row['rodada']: set(row['numeros']) for _, row in df_historico.iterrows()}
    max_concurso_oficial = df_historico['rodada'].max()

    for p in previsoes:
        if p.get('status_conferencia') == 'pendente':
            alvo = p.get('concurso_alvo_estimado')
            
            # Se o concurso alvo já aconteceu (está na base)
            if alvo in gabaritos:
                oficial = gabaritos[alvo]
                acertos = len(set(p['numeros']).intersection(oficial))
                
                p['status_conferencia'] = 'conferido'
                p['acertos_futuros'] = acertos
                atualizou = True
            
            # Heurística: Se o alvo é muito antigo (ex: alvo 3000, e já estamos no 3010), 
            # e não achamos o 3000 na base (talvez gap de dados), marcamos como 'expirado' ou tentamos achar o mais proximo?
            # Por enquanto, só conferimos exatos.
        
        if p.get('status_conferencia') == 'conferido':
            conferidos_count += 1
            total_acertos += p.get('acertos_futuros', 0)

    if atualizou:
        with open(FILE_PATH, 'w') as f:
            json.dump(previsoes, f, indent=4)
            
    # --- GERAR RELATÓRIO DE AUTO-CALIBRAGEM ---
    if conferidos_count < 20:
        return f"Calibragem em andamento: {conferidos_count}/20 palpites conferidos."
    
    media_acertos = total_acertos / conferidos_count
    
    # Análise de Viés: Onde a IA acerta mais?
    # Ex: Dias Pares vs Ímpares
    acertos_pares = [p['acertos_futuros'] for p in previsoes if p.get('status_conferencia') == 'conferido' and p['contexto_temporal']['dia_eh_par']]
    acertos_impares = [p['acertos_futuros'] for p in previsoes if p.get('status_conferencia') == 'conferido' and not p['contexto_temporal']['dia_eh_par']]
    
    media_par = sum(acertos_pares)/len(acertos_pares) if acertos_pares else 0
    media_impar = sum(acertos_impares)/len(acertos_impares) if acertos_impares else 0
    
    melhor_dia = "S/D"
    if media_par > media_impar * 1.05: melhor_dia = "Dias PARES"
    elif media_impar > media_par * 1.05: melhor_dia = "Dias ÍMPARES"
    else: melhor_dia = "Neutro"

    return {
        "msg": "✅ Retro-Análise Disponível",
        "media_global": media_acertos,
        "total_analisado": conferidos_count,
        "vies_descoberto": f"A IA está performando melhor em **{melhor_dia}**.",
        "detalhe": f"Média Pares: {media_par:.2f} | Média Ímpares: {media_impar:.2f}"
    }
