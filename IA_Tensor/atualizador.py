import requests
import json
import pandas as pd
from datetime import datetime
import streamlit as st
import time

def atualizar_dados(caminho_arquivo="rodadas.json"):
    """
    Tenta atualizar o arquivo JSON com os últimos concursos.
    Usa uma API pública gratuita (sujeita a disponibilidade).
    """
    status_msg = st.empty()
    bar = st.progress(0)
    
    try:
        with open(caminho_arquivo, 'r') as f:
            dados = json.load(f)
        
        # Achar último concurso salvo
        ultimo_concurso = 0
        if dados:
            ultimo_concurso = max(d['rodada'] for d in dados)
            
        concurso_alvo = ultimo_concurso + 1
        novos = 0
        
        status_msg.info(f"Verificando novos concursos a partir do {concurso_alvo}...")
        
        while True:
            # Tenta API oficial ou mirror pública
            # Usando loteriascaixa-api.herokuapp.com (comum e gratuita)
            url = f"https://loteriascaixa-api.herokuapp.com/api/lotofacil/{concurso_alvo}"
            
            try:
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    
                    # Validar se é o concurso certo
                    if data['concurso'] != concurso_alvo:
                        break # Algo errado ou API retornou anterior
                        
                    # Formatar data DD/MM/YYYY -> YYYY-MM-DD
                    dt_str = data['data']
                    try:
                        dt_obj = datetime.strptime(dt_str, "%d/%m/%Y")
                        dt_fmt = dt_obj.strftime("%Y-%m-%d")
                    except:
                        dt_fmt = dt_str # Fallback
                        
                    numeros = sorted([int(n) for n in data['dezenas']])
                    
                    novo_registro = {
                        "rodada": data['concurso'],
                        "data": dt_fmt,
                        "numeros": numeros
                    }
                    
                    dados.append(novo_registro)
                    concurso_alvo += 1
                    novos += 1
                    
                    status_msg.info(f"Baixando concurso {data['concurso']}...")
                    bar.progress(min(novos % 100, 100))
                    
                    time.sleep(0.5) # Evitar block da API
                else:
                    # Se der 404 ou outro erro, assumimos que chegamos ao fim
                    break
            except Exception as e:
                # Erro de conexão
                break
                
        bar.empty()
        
        if novos > 0:
            with open(caminho_arquivo, 'w') as f:
                json.dump(dados, f, indent=4)
            status_msg.success(f"Base atualizada! {novos} novos concursos adicionados.")
            time.sleep(2)
            status_msg.empty()
            return True # Indica que houve atualização (recarrar DF)
        else:
            status_msg.warning("Nenhum concurso novo encontrado. Sua base já está atualizada.")
            time.sleep(2)
            status_msg.empty()
            return False

    except Exception as e:
        st.error(f"Erro ao atualizar: {e}")
        return False
