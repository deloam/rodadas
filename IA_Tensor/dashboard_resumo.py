import streamlit as st
import pandas as pd
from datetime import datetime
from collections import Counter

def renderizar_dashboard_resumo(df):
    """
    Exibe um painel executivo (Briefing) no topo da aplicação com os melhores insights do dia.
    Integra Análise Temporal (Dia da Semana) e Ciclos.
    """
    
    # 1. Determinar o contexto de "Hoje"
    hoje = datetime.now()
    dia_semana_ing = hoje.strftime('%A')
    mapa_dias = {
        "Monday": "Segunda-feira", "Tuesday": "Terça-feira", "Wednesday": "Quarta-feira",
        "Thursday": "Quinta-feira", "Friday": "Sexta-feira", "Saturday": "Sábado", "Sunday": "Domingo"
    }
    dia_semana_pt = mapa_dias.get(dia_semana_ing, dia_semana_ing)
    
    # --- CÁLCULOS DO BRIEFING ---
    
    # A. Análise Temporal (O que é quente HOJE?)
    # Filtrar apenas o dia da semana atual no histórico
    df_temp = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_temp['data']):
         df_temp['data'] = pd.to_datetime(df_temp['data'])
         
    df_temp['dia_semana'] = df_temp['data'].dt.day_name()
    subset_hoje = df_temp[df_temp['dia_semana'] == dia_semana_ing]
    
    top_hoje = []
    if len(subset_hoje) > 10:
        c = Counter()
        for nums in subset_hoje['numeros']: c.update(nums)
        # Pegar os 3 mais frequentes
        common = c.most_common(3)
        top_hoje = [n for n, q in common]
        
    # B. Análise de Ciclo (O que falta sair?)
    # (Lógica simplificada do renderizar_ciclos)
    todas_dezenas = set(range(1, 26))
    numeros_no_ciclo = set()
    df_ciclo = df.sort_values('rodada', ascending=False)
    
    for _, row in df_ciclo.iterrows():
        numeros_no_ciclo.update(row['numeros'])
        if numeros_no_ciclo == todas_dezenas:
            break
            
    faltam_sair = list(todas_dezenas - numeros_no_ciclo) if numeros_no_ciclo != todas_dezenas else []
    
    # --- RENDERIZAR O PAINEL ---
    
    st.markdown("### ☀️ Briefing do Dia")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"**Hoje é {dia_semana_pt}**")
        if top_hoje:
            st.markdown(f"🔥 **Quentes de {dia_semana_pt}:**")
            html = " ".join([f"<span style='color:#d35400; font-weight:bold; background:#fad7a0; padding:2px 6px; border-radius:4px'>{n:02d}</span>" for n in top_hoje])
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.caption("Sem dados suficientes para este dia.")

    with c2:
        st.markdown("**Status do Ciclo**")
        if faltam_sair:
            st.markdown(f"⚠️ **Faltam {len(faltam_sair)} nºs:**")
            html = " ".join([f"<span style='color:#27ae60; font-weight:bold; background:#abebc6; padding:2px 6px; border-radius:4px'>{n:02d}</span>" for n in faltam_sair[:5]]) # Limit to 5
            if len(faltam_sair) > 5: html += " ..."
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.success("✅ Ciclo Fechado (Tudo zerado)")

    with c3:
        st.markdown("**Recomendação IA**")
        # Interseção Quentes + Faltam (Ouro)
        recomendados = list(set(top_hoje).intersection(set(faltam_sair)))
        if recomendados:
            st.markdown(f"💎 **Aposte nestes:**")
            html = " ".join([f"<span style='color:#fff; font-weight:bold; background:#8e44ad; padding:3px 8px; border-radius:4px'>{n:02d}</span>" for n in recomendados])
            st.markdown(html, unsafe_allow_html=True)
        elif faltam_sair:
            st.caption(f"Foque nos que faltam para o ciclo.")
        else:
            st.caption("Siga a intuição + IA Híbrida.")
            
    st.markdown("---")
