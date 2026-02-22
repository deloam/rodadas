import streamlit as st
from itertools import combinations
import random
from collections import Counter
from core.utils import verificar_ineditismo, avaliar_qualidade_jogo

def gerar_desdobramentos_inteligentes(numeros_base, num_jogos, df=None, aplicar_filtro_inedito=True, aplicar_filtro_dna=True):
    """
    Gera jogos de 15 números a partir de uma base maior (ex: 18, 20 números).
    Tenta garantir a máxima distribuição e aplica filtros de exclusão.
    """
    jogos = []
    
    # Se a quantidade de combinações totais for pequena, gera todas ou até o limite
    if len(numeros_base) <= 16:
        comb = [sorted(list(c)) for c in combinations(numeros_base, 15)]
        random.shuffle(comb)
        for jogo in comb:
            if len(jogos) >= num_jogos:
                break
            
            valido = True
            if aplicar_filtro_inedito and df is not None:
                msg = verificar_ineditismo(df, jogo)
                if msg and "ALERTA" in msg:
                    valido = False
            
            if valido and aplicar_filtro_dna:
                score, _ = avaliar_qualidade_jogo(jogo)
                if score < 4: # Descarta jogos muito mal balanceados
                    valido = False
                    
            if valido:
                jogos.append(jogo)
        return jogos
    
    # Se for muita coisa, gera aleatório inteligente (garantindo que todos os números apareçam)
    pool = list(numeros_base)
    random.shuffle(pool)
    if len(numeros_base) < 15:
        return []
        
    numeros_list = list(numeros_base)
    uso_numeros = Counter({n: 0 for n in numeros_list})
    
    for _ in range(num_jogos):
        tentativas = 0
        jogo_valido = False
        jogo = []
        
        while not jogo_valido and tentativas < 100:
            candidatos = sorted(numeros_list, key=lambda x: (uso_numeros[x], random.random()))
            jogo = sorted(candidatos[:15])
            
            valido = True
            if aplicar_filtro_inedito and df is not None:
                msg = verificar_ineditismo(df, jogo)
                if msg and "ALERTA" in msg:
                    valido = False
            
            if valido and aplicar_filtro_dna:
                score, _ = avaliar_qualidade_jogo(jogo)
                if score < 4: # Score baixo = geometria ou somas extremas
                    valido = False
            
            if valido:
                jogo_valido = True
                for n in jogo:
                    uso_numeros[n] += 1
                jogos.append(jogo)
            
            tentativas += 1
            
        # Fallback caso seja impossivel gerar algo valido em 100 tentativas
        if not jogo_valido:
            # Pega o ultimo gerado e aceita pra não travar loop
            for n in jogo:
                uso_numeros[n] += 1
            jogos.append(jogo)
            
    return jogos

def renderizar_tab_desdobramento(df):
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
    
    st.markdown("### 🛡️ Filtros de Descarte Opcionais")
    c_f1, c_f2 = st.columns(2)
    aplicar_filtro_inedito = c_f1.checkbox("Ativar Ineditismo Histórico", value=True, help="Omitirá combinações que já foram premiadas no passado com 15 pontos.")
    aplicar_filtro_dna = c_f2.checkbox("Aplicar Equilíbrio de DNA (IA)", value=True, help="Exclui jogos estatisticamente inviáveis gerados pela matriz (ex: 12 pares, muitas bordas). Economiza dinheiro.")
    
    if st.button("Gerar Desdobramento"):
        try:
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
                c1, c2 = st.columns(2)
                c1.success(f"Base: {len(numeros)} dezenas selecionadas.")
                
                with st.spinner("Desdobrando matriz e validando filtros..."):
                    jogos_gerados = gerar_desdobramentos_inteligentes(
                        numeros, qtd_jogos, df, 
                        aplicar_filtro_inedito, aplicar_filtro_dna
                    )
                
                jogos_efetivos = len(jogos_gerados)
                custo_unitario = 3.50
                custo_total = jogos_efetivos * custo_unitario
                c2.metric("Custo Total Estimado", f"R$ {custo_total:,.2f}")
                
                if jogos_efetivos < qtd_jogos:
                    st.warning(f"Foram gerados apenas {jogos_efetivos} jogos válidos de {qtd_jogos} solicitados. Os filtros de IA impediram o gasto com jogos inúteis.")
                
                # Análise de Cobertura
                all_used = set()
                for j in jogos_gerados: all_used.update(j)
                unused = set(numeros) - all_used
                
                if unused:
                    st.warning(f"Atenção: Os números {sorted(list(unused))} da sua base NÃO entraram em todos os jogos.")
                elif jogos_efetivos > 0:
                    st.info("💎 Dezenas distribuídas de forma inteligente pela Matriz.")
    
                if jogos_efetivos > 0:
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
                    
                    st.markdown("### 🎫 Jogos Gerados Criteriosos:")
                    for i, jogo in enumerate(jogos_gerados):
                        # Pinte green se for da matriz
                        html_bolas = ' '.join([f"<span style='color: #fff; background-color: #27ae60; width: 32px; height: 32px; line-height: 32px; text-align: center; margin: 2px; border-radius: 6px; font-weight: bold; display: inline-block'>{num:02d}</span>" for num in jogo])
                        
                        st.markdown(f"<div style='margin-bottom: 8px'><strong>Cartão {i+1}:</strong> {html_bolas}</div>", unsafe_allow_html=True)
                    
                    txt_export_pure = "\n".join([str(j) for j in jogos_gerados])
                    st.text_area("Texto para Copiar (Notepad/Excel)", value=txt_export_pure, height=150)
                else:
                    st.error("Não foi possível gerar jogos válidos com os números restritos e filtros aplicados. Tente afrouxar os filtros ou inserir mais dezenas base.")
                
        except Exception as e:
            st.error(f"Erro ao processar: {e}")
