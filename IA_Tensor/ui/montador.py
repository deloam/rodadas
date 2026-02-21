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
            
            if st.button(label, key=f"btn_montador_{i}", width='stretch'):
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
        
        from core.utils import avaliar_qualidade_jogo
        
        # Só mostra validação se tiver entre 15 e 18 numeros (foco principal)
        if 15 <= qtd <= 18:
            score, m = avaliar_qualidade_jogo(selecionados, ultima_rodada)
            
            indicador(m['impares'], 7, 9, "Ímpares")
            indicador(m['primos'], 4, 6, "Primos")
            indicador(m['moldura'], 8, 11, "Moldura")
            indicador(m['fibo'], 3, 5, "Fibonacci")
            indicador(m['repetentes'], 8, 10, "Repetentes")
            indicador(m['soma'], 180, 220, "Soma")
            
            # Ajuste da escala de score para 0-5 (função retorna 0-10)
            score_ajustado = min(5, score // 2)
            
            st.markdown("---")
            st.write(f"**Qualidade Estatística:** {score_ajustado}/5")
            if score_ajustado == 5:
                st.success("🌟 JOGO PERFEITO PADRÃO!")
            elif score_ajustado >= 3:
                st.info("👍 Jogo Equilibrado")
            else:
                st.warning("👎 Jogo Fora dos Padrões")

        elif qtd < 15:
            st.warning(f"Faltam {15-qtd} números para 15.")
        else:
            st.info("Modo Desdobramento (Mais de 18 números selecionados). A validação estatística padrão perde precisão.")
