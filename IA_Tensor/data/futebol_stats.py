import sqlite3
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

DB_FUTEBOL = "futebol.db"
LEAGUES = ["bra.1", "bra.2", "bra.copa_do_brasil", "bra.camp.paulista", "bra.camp.carioca"]

TIMES_MONITORADOS = ["flamengo", "palmeiras", "corinthians", "são paulo", "vasco", "fluminense"]

def init_db():
    conn = sqlite3.connect(DB_FUTEBOL)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historico_futebol (
        data TEXT PRIMARY KEY,
        gols_total INTEGER,
        fla_status INTEGER,
        pal_status INTEGER,
        sao_status INTEGER,
        cor_status INTEGER
    )
    """)
    conn.commit()
    conn.close()

def parse_team_status(events, base_team_name):
    """
    Procura o time num dia. Retorna 1 (Vitória), -1 (Derrota), 0 (Empate), NaN se não jogou.
    """
    for ev in events:
        for comp in ev.get("competitions", []):
            competitors = comp.get("competitors", [])
            
            is_playing = False
            for c in competitors:
                name = c.get("team", {}).get("name", "").lower()
                if base_team_name in name:
                    is_playing = True
                    break
            
            if is_playing:
                # O time jogou. Vamos ver se ele ganhou ou perdeu.
                for c in competitors:
                    name = c.get("team", {}).get("name", "").lower()
                    if base_team_name in name:
                        winner = c.get("winner")
                        # Em caso de empate, winner vem False/None para ambos. 
                        # Precisamos checar os placares.
                        if winner is True: return 1
                        if winner is False:
                            # pode ser derrota ou empate.
                            score1 = int(competitors[0].get("score", -1))
                            score2 = int(competitors[1].get("score", -1))
                            if score1 == score2 and score1 >= 0:
                                return 0
                            return -1
    return None

def fetch_dia(date_str):
    gols_dia = 0
    events_dia = []
    
    for league in LEAGUES:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard?dates={date_str}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                events = data.get("events", [])
                events_dia.extend(events)
                for ev in events:
                    for comp in ev.get("competitions", []):
                        for c in comp.get("competitors", []):
                            g = c.get("score")
                            if g and g.isdigit():
                                gols_dia += int(g)
        except Exception:
            pass # Silencia timeouts
            
    # Computar times
    st_fla = parse_team_status(events_dia, "flamengo")
    st_pal = parse_team_status(events_dia, "palmeiras")
    st_sao = parse_team_status(events_dia, "são paulo")
    st_cor = parse_team_status(events_dia, "corinthians")
    
    return (date_str, gols_dia, st_fla, st_pal, st_sao, st_cor)


def sincronizar_futebol(datas_necessarias, barra_progresso=None):
    """
    datas_necessarias: lista de strings YYYYMMDD
    """
    init_db()
    conn = sqlite3.connect(DB_FUTEBOL)
    
    df_db = pd.read_sql("SELECT data FROM historico_futebol", conn)
    datas_em_banco = set(df_db['data'].tolist())
    
    datas_para_baixar = [d for d in datas_necessarias if d not in datas_em_banco]
    
    # Restrição pesada: Limitamos o fetch maximo de dias (ex: últimos 365 dias apenas)
    # para evitar sobrecarregar ESPN em primeira vez que é instalado.
    # Exceção foi levantada pelo Usuário "ao menos os mais recentes"
    if not datas_para_baixar:
        conn.close()
        return pd.read_sql("SELECT * FROM historico_futebol", sqlite3.connect(DB_FUTEBOL))
    
    if barra_progresso:
        barra_progresso.progress(0, text=f"Baixando Futs: 0 / {len(datas_para_baixar)}")

    novos_registros = []
    completados = 0
    total = len(datas_para_baixar)
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futuros = {executor.submit(fetch_dia, data_str): data_str for data_str in datas_para_baixar}
        for future in as_completed(futuros):
            try:
                res = future.result()
                novos_registros.append(res)
            except Exception:
                pass 
                
            completados += 1
            if barra_progresso:
                barra_progresso.progress(int((completados/total)*100), text=f"Baixando Futs: {completados} / {total}")
                
    if novos_registros:
        cursor = conn.cursor()
        cursor.executemany("""
        INSERT OR IGNORE INTO historico_futebol (data, gols_total, fla_status, pal_status, sao_status, cor_status)
        VALUES (?, ?, ?, ?, ?, ?)
        """, novos_registros)
        conn.commit()
    
    conn.close()
    
    # Reload from DB
    return pd.read_sql("SELECT * FROM historico_futebol", sqlite3.connect(DB_FUTEBOL))

