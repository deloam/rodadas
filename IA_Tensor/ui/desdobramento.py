import streamlit as st
from itertools import combinations
import random

def gerar_desdobramentos_inteligentes(numeros_base, num_jogos):
    """
    Gera jogos de 15 números a partir de uma base maior (ex: 18, 20 números).
    Tenta garantir a máxima distribuição.
    """
    jogos = []
    
    # Se a quantidade de combinações totais for pequena, gera todas
    if len(numeros_base) <= 16:
        comb = list(combinations(numeros_base, 15))
        return [sorted(list(c)) for c in comb]
    
    # Se for muita coisa, gera aleatório inteligente (garantindo que todos os números apareçam)
    # 1. Garante que todos os números da base apareçam pelo menos uma vez
    pool = list(numeros_base)
    random.shuffle(pool)
    # Se a base for menor que 15, não dá
    if len(numeros_base) < 15:
        return []
        
    numeros_list = list(numeros_base)
    
    # Controle de frequência de uso de cada número
    uso_numeros = Counter({n: 0 for n in numeros_list})
    
    for _ in range(qtd_jogos):
        # Seleciona os top 15 candidatos (os que foram usados menos vezes)
        # Adiciona um fator aleatório no sort key para não ficar determinístico demais
        candidatos = sorted(numeros_list, key=lambda x: (uso_numeros[x], random.random()))
        
        jogo = sorted(candidatos[:15])
        
        # Atualiza contadores
        for n in jogo:
            uso_numeros[n] += 1
            
        jogos.append(jogo)
        
    return jogos

def renderizar_tab_desdobramento():
    st.markdown("## 🔢 Desdobrador Econômico (Matriz Inteligente)")
    st.markdown("Transforme seus palpites grandes (17, 18, 20 dezenas) em jogos de 15 números **economizando dinheiro** e mantendo **equilíbrio matemático**.")
    
    # Tenta pegar da sessão
    default_nums = ""
    if 'ultima_previsao' in st.session_state and st.session_state.ultima_previsao:
        default_nums = ", ".join(map(str, sorted(st.session_state.ultima_previsao)))
    
    entrada = st.text_area("Digite as dezenas para desdobrar (separadas por vírgula ou espaço):", 
                           value=default_nums,
                           height=100)
    
    qtd_jogos = st.slider("Quantos jogos de 15 dezenas gerar?", 5, 100, 10)
    
    if st.button("Gerar Desdobramento"):
        try:
            # Limpar input
            entrada_limpa = entrada.replace(',', ' ').replace(';', ' ')
            numeros = set()
            for x in entrada_limpa.split():
                if x.isdigit():
                    val = int(x)
                    if 1 <= val <= 25:
                        numeros.add(val)
            
            if len(numeros) < 15:
                st.error(f"Você precisa informar pelo menos 15 números (informou {len(numeros)}).")
            else:
                custo_unitario = 3.50
                custo_total = qtd_jogos * custo_unitario
                
                c1, c2 = st.columns(2)
                c1.success(f"Base: {len(numeros)} dezenas selecionadas.")
                c2.metric("Custo Total", f"R$ {custo_total:,.2f}")
                
                jogos_gerados = gerar_desdobramentos_inteligentes(numeros, qtd_jogos)
                
                # Análise de Cobertura
                all_used = set()
                for j in jogos_gerados: all_used.update(j)
                unused = set(numeros) - all_used
                
                if unused:
                    st.warning(f"Atenção: Os números {sorted(list(unused))} da sua base NÃO entraram em todos os jogos. Aumente a quantidade de jogos para cobrir tudo.")
                else:
                    st.info("💎 Dezenas distribuídas de forma equilibrada (Matriz de Cobertura Total).")
    
                # Preparar texto para download
                txt_export = "--- LotoIA: Desdobramento Inteligente ---\n"
                for j in jogos_gerados:
                    txt_export += str(j) + "\n"
                
                st.download_button(
                    label="📥 Baixar Jogos (.txt)",
                    data=txt_export,
                    file_name="desdobramento_lotoia.txt",
                    mime="text/plain"
                )
                
                st.markdown("### 🎫 Jogos Gerados:")
                for i, jogo in enumerate(jogos_gerados):
                    st.markdown(
                            f"**{i+1}:** " + ' '.join([f"<span style='color: #333; background-color: #fff; border: 1px solid #ccc; width: 30px; height: 30px; line-height: 30px; text-align: center; margin: 2px; border-radius: 4px; display: inline-block'>{num}</span>" for num in jogo]),
                            unsafe_allow_html=True
                        )
                
                # Área de cópia
                txt_export = "\n".join([str(j) for j in jogos_gerados])
                st.text_area("Texto para Copiar (Compatível com Excel/Notepad)", value=txt_export)
                
        except Exception as e:
            st.error(f"Erro ao processar: {e}")
