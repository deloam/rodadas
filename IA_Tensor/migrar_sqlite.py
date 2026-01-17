import sqlite3
import json
import os
import time

def migrar_para_sqlite():
    print("🚀 Iniciando migração para SQLite...")
    
    caminho_json = "previsoes.json"
    caminho_db = "previsoes.db"
    
    # 1. Carregar JSON existente
    if not os.path.exists(caminho_json):
        print("❌ Arquivo previsoes.json não encontrado!")
        return
        
    try:
        with open(caminho_json, 'r') as f:
            dados = json.load(f)
        print(f"📂 Carregados {len(dados)} registros do JSON.")
    except Exception as e:
        print(f"❌ Erro ao ler JSON: {e}")
        return

    # 2. Conectar ao Banco e Criar Tabela
    conn = sqlite3.connect(caminho_db)
    cursor = conn.cursor()
    
    # Schema Otimizado
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS previsoes (
        id TEXT PRIMARY KEY,
        timestamp_geracao TEXT,
        concurso_alvo INTEGER,
        numeros TEXT, -- Armazenado como JSON string '[1, 2, ...]'
        score_ia REAL,
        metrics_dna TEXT, -- JSON string
        contexto_temporal TEXT, -- JSON string
        status_conferencia TEXT,
        acertos_futuros INTEGER
    )
    """)
    
    # Index para buscas rápidas
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_concurso ON previsoes (concurso_alvo)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_score ON previsoes (score_ia)")
    
    print("🛠️ Banco de dados e tabela criados.")
    
    # 3. Inserir Dados em Lote (Batch Insert)
    registros = []
    ids_existentes = set()
    
    # Verificar IDs já existentes no banco para evitar duplicata em re-execução
    cursor.execute("SELECT id FROM previsoes")
    ids_existentes = set(row[0] for row in cursor.fetchall())
    
    for item in dados:
        if item['id'] in ids_existentes:
            continue
            
        # Converter listas/dicts para JSON String para armazenamento
        numeros_str = json.dumps(item.get('numeros', []))
        dna_str = json.dumps(item.get('metrics_dna', {}))
        contexto_str = json.dumps(item.get('contexto_temporal', {}))
        
        registros.append((
            item.get('id'),
            item.get('timestamp_geracao'),
            item.get('concurso_alvo_estimado'),
            numeros_str,
            item.get('score_ia'),
            dna_str,
            contexto_str,
            item.get('status_conferencia', 'pendente'),
            item.get('acertos_futuros', 0)
        ))
    
    if registros:
        print(f"💾 Inserindo {len(registros)} novos registros...")
        cursor.executemany("""
        INSERT INTO previsoes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, registros)
        conn.commit()
        print("✅ Migração concluída com sucesso!")
    else:
        print("⚠️ Nenhum registro novo para migrar.")
        
    conn.close()
    
    print(f"\n🎉 Tudo pronto! Seus dados agora estão em '{caminho_db}'.")
    print("Uma cópia segura e performática.")

if __name__ == "__main__":
    migrar_para_sqlite()
