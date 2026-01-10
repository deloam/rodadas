import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

def renderizar_montador_manual(df):
    st.markdown("## 🏗️ Montador Manual Interativo")
    st.markdown("Construa seu jogo clicando nos números. A **IA e a Estatística** auditam sua aposta em tempo real.")

    # Estado dos botões (usando session state para persistir cliques)
    if 'montador_selecionados' not in st.session_state:
        st.session_state.montador_selecionados = set()
    
    # Grid 5x5 de botões
    # Vamos usar st.columns dentro de loops
    cols = st.columns(5)
    
    # CSS para botões bonitos (toggle)
    # Streamlit nativo não tem toggle button fácil no grid, vamos usar logica de add/remove
    
    for i in range(1, 26):
        col_idx = (i - 1) % 5
        with cols[col_idx]:
            # Verifica se está selecionado
            is_selected = i in st.session_state.montador_selecionados
            
            # Label com indicador visual
            label = f"🟢 {i:02d}" if is_selected else f"{i:02d}"
            
            if st.button(label, key=f"btn_montador_{i}", use_container_width=True):
                if is_selected:
                    st.session_state.montador_selecionados.remove(i)
                else:
                    if len(st.session_state.montador_selecionados) < 20: # Limite seguro para não travar
                        st.session_state.montador_selecionados.add(i)
                st.rerun()

    selecionados = sorted(list(st.session_state.montador_selecionados))
    qtd = len(selecionados)
    
    st.markdown("---")
    
    # --- AUDITORIA EM TEMPO REAL ---
    if qtd == 0:
        st.info("👆 Clique nos números acima para começar a montar seu jogo.")
        return

    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader(f"Jogo Atual ({qtd} dezenas)")
        # Visualização de bolinhas
        html_bolas = ' '.join([f"<span style='color: white; background-color: #2980b9; padding: 5px 10px; margin: 3px; border-radius: 50%; font-weight: bold; font-size: 18px; display: inline-block'>{num}</span>" for num in selecionados])
        st.markdown(html_bolas, unsafe_allow_html=True)
        
        # Botões de Ação
        col_act1, col_act2 = st.columns(2)
        if col_act1.button("🗑️ Limpar Tudo"):
            st.session_state.montador_selecionados = set()
            st.rerun()
            
        if qtd >= 15:
            # Opção de copiar/exportar
            st.text_input("📋 Copiar Jogo:", value=str(selecionados))


    with c2:
        st.subheader("📊 Auditoria (DNA)")
        
        # Constantes
        PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}
        MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
        FIBONACCI = {1, 2, 3, 5, 8, 13, 21}
        
        # Cálculos (baseados em 15 numeros para 'Ideal', ajusta proporcional se for >15?)
        # Vamos auditar como se fosse um jogo de 15. Se for <15 ou >15, avisamos.
        
        impares = sum(1 for x in selecionados if x % 2 != 0)
        primos = sum(1 for x in selecionados if x in PRIMOS)
        moldura = sum(1 for x in selecionados if x in MOLDURA)
        fibo = sum(1 for x in selecionados if x in FIBONACCI)
        soma = sum(selecionados)
        
        # Último concurso para comparar repetentes
        ultima_rodada = set(df.iloc[-1]['numeros'])
        repetentes = len(set(selecionados).intersection(ultima_rodada))

        # Helper de validação visual
        def indicador(valor, ideal_min, ideal_max, label):
            status = "✅" if ideal_min <= valor <= ideal_max else "⚠️"
            st.markdown(f"**{label}:** {valor} {status} <small>(Ideal: {ideal_min}-{ideal_max})</small>", unsafe_allow_html=True)
        
        # Só mostra validação se tiver entre 15 e 18 numeros (foco principal)
        if 15 <= qtd <= 18:
            indicador(impares, 7, 9, "Ímpares")
            indicador(primos, 4, 6, "Primos")
            indicador(moldura, 8, 11, "Moldura")
            indicador(fibo, 3, 5, "Fibonacci")
            indicador(repetentes, 8, 10, "Repetentes")
            indicador(soma, 180, 220, "Soma")
            
            # Análise Final da IA
            score = 0
            if 7 <= impares <= 9: score += 1
            if 4 <= primos <= 6: score += 1
            if 8 <= moldura <= 11: score += 1
            if 3 <= fibo <= 5: score += 1
            if 8 <= repetentes <= 10: score += 1
            
            st.markdown("---")
            st.write(f"**Qualidade Estatística:** {score}/5")
            if score == 5:
                st.success("🌟 JOGO PERFEITO PADRÃO!")
            elif score >= 3:
                st.info("👍 Jogo Equilibrado")
            else:
                st.warning("👎 Jogo Fora dos Padrões")

        elif qtd < 15:
            st.warning(f"Faltam {15-qtd} números para 15.")
        else:
            st.info("Modo Desdobramento (Mais de 18 números selecionados). A validação estatística padrão perde precisão.")
