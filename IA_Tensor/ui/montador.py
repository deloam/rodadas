import streamlit as st
from core.utils import avaliar_qualidade_jogo, verificar_ineditismo, calcular_backtest_rapido, calcular_afinidades
from core.stats_montador import (
    calcular_estado_ciclo,
    calcular_forca_dezenas,
    analisar_desenho_5x5
)

def indicador(valor, min_id, max_id, label):
    cor = "green" if min_id <= valor <= max_id else "red"
    icone = "✅" if min_id <= valor <= max_id else "⚠️"
    st.markdown(f"<span style='color:{cor}'>{icone} **{label}:** {valor}</span>", unsafe_allow_html=True)

def renderizar_montador_manual(df):
    st.markdown("## 🏗️ Montador Manual Interativo")
    st.markdown("Construa seu jogo clicando nos números. A **IA e a Estatística** auditam sua aposta em tempo real.")

    # 1. MONITOR DE CICLO (Feature 4)
    # Calculando estado do ciclo
    if 'ciclo_info' not in st.session_state:
        st.session_state.ciclo_info = calcular_estado_ciclo(df)
        st.session_state.forca_dezenas = calcular_forca_dezenas(df)
        
    ciclo = st.session_state.ciclo_info
    
    with st.expander("🔄 Status do Ciclo das Dezenas", expanded=False):
        st.write(f"Estamos no sorteio **{ciclo['sorteio_atual_do_ciclo']}** deste ciclo. O progresso é de {ciclo['progresso_percentual']:.1f}%")
        if ciclo['dezenas_faltantes']:
            faltam_bolas = ' '.join([f"<span style='color: white; background-color: #e67e22; padding: 4px; border-radius: 5px; margin: 2px'>{x:02d}</span>" for x in ciclo['dezenas_faltantes']])
            st.markdown(f"Dezenas Faltam: {faltam_bolas}", unsafe_allow_html=True)
            st.caption("A IA recomenda fortemente incluir as dezenas que faltam para fechar o ciclo.")
        else:
            st.success("O Ciclo fechou no último sorteio!")

    # Estado dos botões (usando session state para persistir cliques)
    if 'montador_selecionados' not in st.session_state:
        st.session_state.montador_selecionados = set()
    
    selecionados = sorted(list(st.session_state.montador_selecionados))
    qtd = len(selecionados)
    
    # Afinidades (Feature 1) calculadas em tempo real se qtd <= 4
    afinidades_info = []
    if 1 <= qtd <= 4:
        afinidades_info = calcular_afinidades(df, selecionados)

    # Grid 5x5 de botões via HTML/CSS Customizado para simular o Quadrado da Lotofácil (Volante)
    st.markdown("### Selecione suas Dezenas")
    
    # CSS Customizado Global para os botões do montador
    st.markdown("""
    <style>
    /* Estilizando o grid vizinho ao marcador */
    .element-container:has(#loto-grid-marker) + .element-container div[data-testid="stButton"] button {
        border-radius: 8px !important;
        font-size: 20px !important;
        font-weight: bold !important;
        height: 60px !important;
        transition: all 0.2s ease-in-out !important;
        border: 2px solid #d0d0d0 !important;
        background-color: #f0f2f6 !important;
        color: #31333F !important;
    }
    .element-container:has(#loto-grid-marker) + .element-container div[data-testid="stButton"] button:hover {
        border-color: #27ae60 !important;
        transform: scale(1.05);
    }
    /* Estilo para Botões Selecionados (Primary) */
    .element-container:has(#loto-grid-marker) + .element-container div[data-testid="stButton"] button[kind="primary"],
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #27ae60 !important;
        color: white !important;
        border-color: #219a52 !important;
        box-shadow: 0px 4px 6px rgba(39, 174, 96, 0.4) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Marca o início do grid para o CSS
    st.markdown('<span id="loto-grid-marker"></span>', unsafe_allow_html=True)
    
    # Lógica de Botões do Streamlit usando colunas
    cols = st.columns(5)
    
    for i in range(1, 26):
        col_idx = (i - 1) % 5
        with cols[col_idx]:
            is_selected = i in st.session_state.montador_selecionados
            
            # Power Score
            score_forca = st.session_state.forca_dezenas.get(i, 0)
            
            # Label
            label_text = f"{i:02d}"
            
            # Afinidade
            tem_afinidade = False
            for aff, pct in afinidades_info:
                if aff == i:
                    tem_afinidade = True
                    label_text += " 🔥"
            
            # Use 'primary' para selecionados e 'secondary' para o resto
            tipo_btn = "primary" if is_selected else "secondary"
            
            if st.button(label_text, key=f"btn_montador_{i}", type=tipo_btn, width='stretch', help=f"Score da IA: {score_forca}/100 - Clique para marcar"):
                if is_selected:
                    st.session_state.montador_selecionados.remove(i)
                else:
                    if len(st.session_state.montador_selecionados) < 20:
                        st.session_state.montador_selecionados.add(i)
                st.rerun()

    if 1 <= qtd <= 4 and afinidades_info:
        st.caption("🔥 **Afinidade:** Baseado na sua seleção, essas outras fortes costumam sair junto: " + ", ".join([f"{a:02d} ({p:.0f}%)" for a, p in afinidades_info]))

    st.markdown("---")
    
    # --- AUDITORIA EM TEMPO REAL ---
    if qtd == 0:
        st.info("👆 Clique nos números acima para começar a montar seu jogo.")
        return

    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader(f"Jogo Atual ({qtd} dezenas)")
        html_bolas = ' '.join([f"<span style='color: white; background-color: #27ae60; padding: 10px; margin: 4px; border-radius: 8px; font-weight: bold; font-size: 18px; display: inline-block; width: 44px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.2)'>{num:02d}</span>" for num in selecionados])
        st.markdown(html_bolas, unsafe_allow_html=True)
        
        col_act1, col_act2 = st.columns(2)
        if col_act1.button("🗑️ Limpar Tudo"):
            st.session_state.montador_selecionados = set()
            st.rerun()
            
        if qtd >= 15:
            st.text_input("📋 Copiar Jogo:", value=str(selecionados))

        # 5. Máquina do Tempo / Backtest (Feature 5) & 3. Filtro de Ineditismo (Feature 3)
        if qtd >= 15:
            st.markdown("### ⏱️ Máquina do Tempo (Instant Backtest)")
            bt = calcular_backtest_rapido(df, selecionados[:15]) # Usar primeiros 15 pra teste estrito
            if bt:
                st.write(f"Se você tivesse jogado essas exatas 15 dezenas em TODOS os sorteios da história:")
                bt_str = f"🏆 **15 Acertos:** {bt['15']}x | 🥈 **14 Acertos:** {bt['14']}x | 🥉 **13 Acertos:** {bt['13']}x | 🎯 **12:** {bt['12']}x | 🎯 **11:** {bt['11']}x"
                st.markdown(bt_str)
                cor_roi = "green" if bt['roi'] > 0 else "red"
                st.markdown(f"**ROI Histórico deste jogo:** <span style='color:{cor_roi}'>**{bt['roi']:.2f}%**</span>", unsafe_allow_html=True)
            
            ineditismo_msg = verificar_ineditismo(df, selecionados[:15])
            if ineditismo_msg:
                if "ALERTA VERMELHO" in ineditismo_msg:
                    st.error(ineditismo_msg)
                else:
                    st.success(ineditismo_msg)
                
        # 2. Análise Espacial e Formas Geométricas (Feature 4 - Desenho 5x5)
        st.markdown("### 🎨 Análise Visual do Volante 5x5")
        insights_desenho = analisar_desenho_5x5(selecionados)
        if insights_desenho:
            for insight in insights_desenho:
                st.warning(insight)
        else:
            st.info("Padrão de distribuição espacial equilibrado (nenhuma anomalia severa no desenho).")

    with c2:
        st.subheader("📊 Auditoria (DNA)")
        
        ultima_rodada = set(df.iloc[-1]['numeros'])
        
        if 15 <= qtd <= 18:
            score, m = avaliar_qualidade_jogo(selecionados, ultima_rodada)
            
            indicador(m['impares'], 7, 9, "Ímpares")
            indicador(m['primos'], 4, 6, "Primos")
            indicador(m['moldura'], 8, 11, "Moldura")
            indicador(m['fibo'], 3, 5, "Fibonacci")
            indicador(m['repetentes'], 8, 10, "Repetentes")
            indicador(m['soma'], 180, 220, "Soma")
            
            score_ajustado = min(5, score // 2)
            
            st.markdown("---")
            
            try:
                from analysis.smart_clustering import treinar_modelo_clusters, extrair_metricas_avancadas
                numeros_tuple = tuple(tuple(x) for x in df['numeros'])
                model, scaler, _, nomes_familias, _ = treinar_modelo_clusters(numeros_tuple)
                
                features_jogo = extrair_metricas_avancadas(selecionados[:15])
                features_scaled = scaler.transform([features_jogo])
                cluster_jogo = model.predict(features_scaled)[0]
                familia_jogo = nomes_familias[cluster_jogo]
                
                st.write(f"🧬 **Arquétipo:** {familia_jogo}")
            except Exception as e:
                pass
                
            st.write(f"⭐ **Qualidade Estatística:** {score_ajustado}/5")
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
