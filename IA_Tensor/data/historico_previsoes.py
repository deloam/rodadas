import sqlite3
import json
import os
import hashlib
from datetime import datetime
import pandas as pd
import numpy as np

DB_PATH = "previsoes.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS previsoes (
        id TEXT PRIMARY KEY,
        timestamp_geracao TEXT,
        concurso_alvo INTEGER,
        numeros TEXT,
        score_ia REAL,
        metrics_dna TEXT,
        contexto_temporal TEXT,
        status_conferencia TEXT,
        acertos_futuros INTEGER
    )
    """)
    
    # Nova Tabela para Dados Exógenos (Data Lake Financeiro)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historico_financeiro (
        data TEXT,
        ticker TEXT,
        fechamento REAL,
        variacao REAL,
        PRIMARY KEY (data, ticker)
    )
    """)

    # Nova Tabela de Espelhamento (Resultados Oficiais)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resultados_oficiais (
        rodada INTEGER PRIMARY KEY,
        data TEXT,
        numeros TEXT, -- JSON Array
        soma INTEGER
    )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_concurso ON previsoes (concurso_alvo)")
    conn.commit()
    conn.close()

def sincronizar_resultados(df):
    """Espelha o rodadas.json para o SQLite (Tabela resultados_oficiais)."""
    init_db() # Garante tabela criada
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Otimização: Pegar qual o último salvo para não tentar inserir tudo
    try:
        cursor.execute("SELECT MAX(rodada) FROM resultados_oficiais")
        ultimo_salvo = cursor.fetchone()[0]
    except:
        ultimo_salvo = 0
        
    if ultimo_salvo is None: ultimo_salvo = 0
    
    # Filtrar apenas novos (assumindo que df tem coluna 'rodada')
    # Se rodadas.json mudar indices, garantir que rodada é int
    
    # Performance: Se df é pequeno, itera. 
    # Mas aqui vamos filtrar no Pandas primeiro.
    novos = df[df['rodada'] > ultimo_salvo]
    
    if novos.empty:
        conn.close()
        return 0
        
    count = 0
    for idx, row in novos.iterrows():
        # Converter Numeros para JSON string
        nums_json = json.dumps(row['numeros'])
        # Garantir data string
        data_str = pd.to_datetime(row['data']).strftime('%Y-%m-%d')
        soma = int(sum(row['numeros']))
        
        cursor.execute("INSERT INTO resultados_oficiais (rodada, data, numeros, soma) VALUES (?, ?, ?, ?)", 
                       (int(row['rodada']), data_str, nums_json, soma))
        count += 1
        
    conn.commit()
    conn.close()
    return count

def gerar_hash_sequencia(numeros, timestamp_str):
    """Gera um hash único para a sequência baseado nos números e momento."""
    raw = f"{sorted(numeros)}-{timestamp_str}"
    return hashlib.md5(raw.encode()).hexdigest()

def salvar_previsoes_detalhadas(resultados, df_historico):
    """
    Salva uma lista de previsões com metadados ricos em 'previsoes.db'.
    """
    init_db()
    
    # 1. Contexto do Próximo Concurso (Estimado)
    if not df_historico.empty:
        ultimo_concurso = df_historico.iloc[-1]
        prox_rodada = int(ultimo_concurso['rodada']) + 1
        data_geracao = datetime.now()
    else:
        prox_rodada = 1
        data_geracao = datetime.now()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    novos_registros = []
    count_salvos = 0
    
    for item in resultados:
        # CONVERSÃO CRÍTICA
        seq = [int(n) for n in item['seq']] 
        metrics = {k: int(v) if isinstance(v, (int, np.integer)) else float(v) for k,v in item['metrics'].items()}
        score = float(item['score'])
        
        timestamp = data_geracao.isoformat()
        id_unico = gerar_hash_sequencia(seq, timestamp)
        
        # Contexto Temporal Rico
        dia_semana_en = data_geracao.strftime('%A')
        mapa_dias = {"Monday": "Segunda-feira", "Tuesday": "Terça-feira", "Wednesday": "Quarta-feira", "Thursday": "Quinta-feira", "Friday": "Sexta-feira", "Saturday": "Sábado", "Sunday": "Domingo"}
        dia_semana_pt = mapa_dias.get(dia_semana_en, dia_semana_en)
        
        contexto = {
            "origem": item.get('origem', '🤖 IA Padrão (Estatística Pura)'),
            "dia_semana": dia_semana_pt,
            "dia": int(data_geracao.day),
            "mes": int(data_geracao.month),
            "ano": int(data_geracao.year),
            "dia_eh_par": bool(data_geracao.day % 2 == 0),
            "semestre": 1 if data_geracao.month <= 6 else 2,
            "trimestre": (data_geracao.month - 1) // 3 + 1
        }
        
        # Verificar duplicidade se necessário (o ID hash já previne, mas o INSERT OR IGNORE resolve)
        try:
            cursor.execute("""
            INSERT OR IGNORE INTO previsoes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                id_unico,
                timestamp,
                prox_rodada,
                json.dumps(seq),
                score,
                json.dumps(metrics),
                json.dumps(contexto),
                "pendente",
                0
            ))
            if cursor.rowcount > 0:
                count_salvos += 1
        except Exception as e:
            print(f"Erro ao salvar previsão {id_unico}: {e}")

    conn.commit()
    conn.close()
        
    return count_salvos

def renderizar_historico_previsoes_tab():
    import streamlit as st
    
    st.markdown("## 📜 Memória da IA (Histórico de Previsões - SQLite)")
    
    if not os.path.exists(DB_PATH):
        st.info("Nenhuma previsão salva ainda. As tabelas serão criadas no primeiro uso.")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        query = "SELECT * FROM previsoes ORDER BY timestamp_geracao DESC"
        df_prev = pd.read_sql_query(query, conn)
    except:
        st.info("Histórico vazio ou banco inexistente.")
        conn.close()
        return
    conn.close()
    
    if df_prev.empty:
        st.info("Histórico vazio.")
        return

    # Desserializar JSONs para exibição bonita se necessário, ou manter string para performance
    # Vamos converter apenas o 'numeros' para lista real para exibir
    df_prev['numeros_list'] = df_prev['numeros'].apply(json.loads)
    df_prev['data_visual'] = pd.to_datetime(df_prev['timestamp_geracao']).dt.strftime('%d/%m/%Y %H:%M')
    
    st.write(f"Total de palpites memorizados: {len(df_prev)}")
    
    # Mostrar os últimos 5
    st.markdown("### Últimas 5 Previsões Geradas")
    
    # Iterar sobre os top 5 (já ordenado DESC na query)
    for index, row in df_prev.head(5).iterrows():
        # Formatar status
        if row['status_conferencia'] == 'conferido':
            hits = row['acertos_futuros']
            badge = f"✅ {hits} acertos" if hits >= 11 else f"❌ {hits} acertos"
        else:
            badge = "⏳ Pendente"

        st.markdown(f"""
        **ID:** `{row['id'][:8]}...` | 🎯 Alvo: **{row['concurso_alvo']}** | {badge} | 📅 {row['data_visual']}
        <br>Numbers: **{row['numeros_list']}** | Score IA: {row['score_ia']:.2f}
        """, unsafe_allow_html=True)
        st.markdown("---")

def executar_retro_analise(df_historico):
    """
    Verifica se os palpites passados ('pendente') já têm resultado oficial.
    Atualiza o SQLite e gera relatório.
    """
    if not os.path.exists(DB_PATH): return None

    # Cache dos resultados oficiais para performance
    # Dict: {1234: {1, 2, ...}, 1235: {...}}
    gabaritos = {row['rodada']: set(row['numeros']) for _, row in df_historico.iterrows()}
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Permite acesso por nome de coluna
    cursor = conn.cursor()
    
    # Buscar apenas Pendentes
    cursor.execute("SELECT id, concurso_alvo, numeros FROM previsoes WHERE status_conferencia = 'pendente'")
    pendentes = cursor.fetchall()
    
    atualizou_count = 0
    
    for p in pendentes:
        alvo = p['concurso_alvo']
        
        # Se o concurso alvo já aconteceu
        if alvo in gabaritos:
            oficial = gabaritos[alvo]
            numeros_apostados = set(json.loads(p['numeros']))
            acertos = len(numeros_apostados.intersection(oficial))
            
            # Update
            cursor.execute("""
            UPDATE previsoes 
            SET status_conferencia = 'conferido', acertos_futuros = ? 
            WHERE id = ?
            """, (acertos, p['id']))
            atualizou_count += 1
            
    conn.commit()
    
    # --- GERAR RELATÓRIO DE AUTO-CALIBRAGEM ---
    # Query agregada para performance
    cursor.execute("SELECT COUNT(*), AVG(acertos_futuros) FROM previsoes WHERE status_conferencia = 'conferido'")
    res = cursor.fetchone()
    conferidos_count = res[0]
    media_acertos = res[1] if res[1] else 0
    
    relatorio = None
    
    if conferidos_count >= 20:
        # Análise de Viés Complexa (precisa ler o JSON contexto)
        # SQLite nativo não parseia JSON fácil em versões antigas. Vamos puxar para Python.
        cursor.execute("SELECT acertos_futuros, contexto_temporal FROM previsoes WHERE status_conferencia = 'conferido'")
        rows = cursor.fetchall()
        
        acertos_ia = []
        acertos_mercado = []
        
        for r in rows:
            ctx = json.loads(r['contexto_temporal'])
            hits = r['acertos_futuros']
            origem = ctx.get('origem', '')
            
            if 'Mercado' in origem or 'Sincronicidade' in origem:
                acertos_mercado.append(hits)
            else:
                acertos_ia.append(hits)
        
        media_ia = sum(acertos_ia)/len(acertos_ia) if acertos_ia else 0
        media_mercado = sum(acertos_mercado)/len(acertos_mercado) if acertos_mercado else 0
        
        if media_mercado == 0 and media_ia > 0:
            melhor_motor = "Apenas IA Padrão testada"
            detalhe_vies = f"Média IA Pura: {media_ia:.2f}"
        elif media_mercado > media_ia: 
            melhor_motor = "🌌 IA + Mercado (Sincronicidade está Vencendo!)"
            detalhe_vies = f"A influência da Bolsa/Dólar está gerando em média **{media_mercado:.2f} acertos**, contra **{media_ia:.2f}** da IA Padrão."
        elif media_ia > media_mercado: 
            melhor_motor = "🤖 IA Padrão (Estatística Pura está Vencendo!)"
            detalhe_vies = f"Jogar puro com a Matemática (Média {media_ia:.2f}) está batendo o Caos de Mercado (Média {media_mercado:.2f})."
        else:
            melhor_motor = "⚔️ Empate Técnico"
            detalhe_vies = f"Ambos os motores cravam média de {media_ia:.2f} acertos."

        relatorio = {
            "msg": "✅ Calibragem de Motores Disponível",
            "media_global": media_acertos,
            "total_analisado": conferidos_count,
            "vies_descoberto": f"Motor mais lucrativo recente: **{melhor_motor}**",
            "detalhe": detalhe_vies
        }
    else:
        relatorio = f"Calibragem em andamento: {conferidos_count}/20 palpites conferidos."

    conn.close()
    return relatorio
