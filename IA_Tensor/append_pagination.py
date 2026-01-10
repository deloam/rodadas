
with open("app.py", "a") as f:
    f.write('''
    # --- ÁREA DE VISUALIZAÇÃO DE RESULTADOS (PAGINADA) ---
    st.markdown("---")
    
    # Verifica se existem resultados na sessão (Memória Persistente)
    if 'resultados_ia' in st.session_state and st.session_state.resultados_ia:
        results = st.session_state.resultados_ia
        
        # 1. Conferência (Se houver gabarito selecionado)
        if sequencia_correta_auto is not None:
             correta_set = set(sequencia_correta_auto)
             # Calcular acertos e atualizar score
             for item in results:
                 acertos = len(set(item['seq']).intersection(correta_set))
                 item['acertos_check'] = acertos
             
             # Re-ordenar por ACERTOS (Top) -> Score
             results.sort(key=lambda x: (x.get('acertos_check', 0), x['score']), reverse=True)
             
             st.info(f"🔎 Resultados reordenados por acertos no Concurso {concurso_str}")

        # 2. Paginação
        total_items = len(results)
        page_size = 10
        total_pages = (total_items - 1) // page_size + 1
        
        col_pag1, col_pag2, col_pag3 = st.columns([2, 1, 2])
        with col_pag2:
            st.session_state.pagina_atual = st.number_input(
                f"Página (Total {total_pages})", 
                min_value=1, max_value=total_pages, 
                value=st.session_state.get('pagina_atual', 1)
            )
        
        start_idx = (st.session_state.pagina_atual - 1) * page_size
        end_idx = start_idx + page_size
        subset = results[start_idx:end_idx]
        
        st.markdown(f"**Mostrando {start_idx+1} a {min(end_idx, total_items)} de {total_items} previsões**")
        
        # 3. Renderizar Lista
        for i, item in enumerate(subset):
            real_index = start_idx + i + 1
            r = item['seq']
            m = item['metrics']
            score = item['score']
            
            acertos_label = ""
            correta_set = set(sequencia_correta_auto) if sequencia_correta_auto is not None else None
            
            html_numeros = ""
            if correta_set:
                matches = set(r).intersection(correta_set)
                acertos_cnt = len(matches)
                cor_badge = "green" if acertos_cnt >= 11 else "#666"
                acertos_label = f" <span style='background-color:{cor_badge}; color:white; padding:2px 6px; border-radius:4px; font-size:14px'>{acertos_cnt} ACERTOS</span>"
                
                html_numeros = ' '.join([
                    f"<span style='color: white; background-color: {'#27ae60' if num in correta_set else '#c0392b'}; padding: 4px; margin: 2px; border-radius: 5px; display:inline-block; width:28px; text-align:center'>{num}</span>"
                    for num in r
                ])
            else:
                html_numeros = ' '.join([f"<span style='color: white; background-color: #2980b9; padding: 4px; margin: 2px; border-radius: 5px; display:inline-block; width:28px; text-align:center'>{num}</span>" for num in r])

            st.markdown(f"### #{real_index} <small>(Score: {score}/12){acertos_label}</small>", unsafe_allow_html=True)
            st.markdown(html_numeros, unsafe_allow_html=True)
            st.caption(f"DNA: Ímpares: {m.get('impares')} | Primos: {m.get('primos')} | Moldura: {m.get('moldura')} | Fibo: {m.get('fibo')}")
            st.markdown("---")
''')
