import streamlit as st
import pandas as pd
import altair as alt
import sqlite3
import datetime

def calcular_dna(numeros):
    impares = sum(1 for x in numeros if x % 2 != 0)
    primos = sum(1 for x in numeros if x in [2, 3, 5, 7, 11, 13, 17, 19, 23])
    moldura = sum(1 for x in numeros if x in [1,2,3,4,5,6,10,11,15,16,20,21,22,23,24,25])
    soma = sum(numeros)
    return impares, primos, moldura, soma

@st.cache_data
def carregar_dados_ludicos(df_loto):
    # Processar loto
    records = []
    for idx, row in df_loto.iterrows():
        nums = row['numeros']
        i, p, m, s = calcular_dna(nums)
        records.append({
            'data': pd.to_datetime(row['data']),
            'soma': s,
            'impares': i,
            'primos': p,
            'moldura': m,
            'numeros': nums
        })
    df_l = pd.DataFrame(records)
    
    # Futebol
    try:
        conn = sqlite3.connect("futebol.db")
        df_fut = pd.read_sql("SELECT * FROM historico_futebol", conn)
        df_fut['data_dt'] = pd.to_datetime(df_fut['data'], format='%Y%m%d')
        conn.close()
    except:
        df_fut = pd.DataFrame()
        
    return df_l, df_fut

def renderizar_tab_teorias_ludicas(df_loto):
    st.markdown("## 🎭 Laboratório de Teorias Lúdicas")
    st.markdown("Você já reparou que o universo é feito de padrões estranhos? Aqui nós conectamos eventos da vida real aos resultados da Lotofácil.")
    
    df_l, df_fut = carregar_dados_ludicos(df_loto)
    
    teoria = st.selectbox(
        "Selecione uma Teoria para Investigar:",
        [
            "⚽ Efeito Maracanã (A Ira das Torcidas)",
            "📅 Maldição da Segunda-Feira (Semanal)",
            "🎲 Sequências Completas: O que Sai Depois do Caos?"
        ]
    )
    
    st.markdown("---")
    
    if "Efeito Maracanã" in teoria:
        if df_fut.empty:
            st.warning("⚠️ O Banco de Dados de Futebol está vazio. Vá na aba 'Caos Exógeno' primeiro para que a IA sincronize o histórico de partidas com a ESPN!")
            return
            
        st.subheader("⚽ A Ira das Grandes Torcidas")
        st.write("Quando grandes times perdem na véspera do sorteio, o 'humor coletivo' desaba. Será que isso altera a entropia de escolhas dos amadores ou o peso das bolas?")
        
        # Merge: Data Loto = Data_Fut + 1 dia (jogou ontem, sorteia hoje)
        df_l['data_ontem'] = df_l['data'] - pd.Timedelta(days=1)
        df_cl = pd.merge(df_l, df_fut, left_on='data_ontem', right_on='data_dt', how='inner')
        
        times = {
            'Flamengo': 'fla_status',
            'Palmeiras': 'pal_status',
            'Corinthians': 'cor_status',
            'São Paulo': 'sao_status'
        }
        
        time_sel = st.selectbox("Escolha o Time para Análise:", list(times.keys()))
        col_status = times[time_sel]
        
        # Agrupar (-1 Perdeu, 0 Empate, 1 Ganhou)
        status_map = {-1.0: '❌ Derrota (-1)', 0.0: '➖ Empate (0)', 1.0: '✅ Vitória (1)'}
        df_cl['Status_Time'] = df_cl[col_status].map(status_map)
        df_valid = df_cl.dropna(subset=['Status_Time'])
        
        if df_valid.empty:
            st.info(f"O sistema ainda não baixou o histórico de jogos do {time_sel}.")
            return
            
        c1, c2 = st.columns(2)
        
        # Tabela 1: Tendência de Soma
        stats_soma = df_valid.groupby('Status_Time')['soma'].mean().reset_index()
        
        bar_soma = alt.Chart(stats_soma).mark_bar(opacity=0.8).encode(
            x=alt.X('Status_Time:N', title='Resultado do Time Ontem', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('soma:Q', title='Soma Média do Sorteio', scale=alt.Scale(domain=[185, 205])),
            color='Status_Time',
            tooltip=['Status_Time', alt.Tooltip('soma', format='.1f')]
        ).properties(title="Impacto na SOMA das Dezenas", height=300)
        
        with c1: st.altair_chart(bar_soma, use_container_width=True)
            
        # Tabela 2: Qual a bola MAIS quente quando ele perde?
        # Extrair frequencia
        df_perdeu = df_valid[df_valid[col_status] == -1.0]
        if not df_perdeu.empty:
             freq = {i: 0 for i in range(1, 26)}
             for nums in df_perdeu['numeros']:
                 for n in nums: freq[n] += 1
                 
             top_balls = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
             with c2:
                 st.markdown(f"#### 🔮 Bolas da 'Vingança' ({time_sel})")
                 st.caption(f"Quando o {time_sel} perdeu, estas foram as dezenas que mais pularam ativamente da máquina lotérica no dia seguinte:")
                 
                 for bola, qtd in top_balls:
                      pct = (qtd / len(df_perdeu)) * 100
                      st.metric(label=f"Dezena {bola:02d}", value=f"{pct:.1f}% de chance", delta=f"{qtd}x sorteadas")
        else:
            with c2: st.info(f"O {time_sel} não perdeu nos dias em que o banco rastreou.")

    elif "Maldição da Segunda-Feira" in teoria:
        st.subheader("📅 O Peso Semanal (Segunda vs Sexta)")
        st.write("Dizem as teorias físicas que a máquina da Lotofácil começa 'fria' na segunda-feira após limpar no final de semana, gerando agrupamentos anômalos que se dissipam na Sexta.")
        
        dias_map = {0: '2ª Feira', 1: '3ª Feira', 2: '4ª Feira', 3: '5ª Feira', 4: '6ª Feira', 5: 'Sábado', 6: 'Domingo'}
        df_l['dia_da_semana'] = df_l['data'].dt.dayofweek.map(dias_map)
        
        ordem_dias = ['2ª Feira', '3ª Feira', '4ª Feira', '5ª Feira', '6ª Feira', 'Sábado']
        
        # Evolução da "Sujeira" na Máquina ao longo da semana (Quantos buracos aparecem?)
        # Vamos calcular "Linhas Vazias" médias
        def calc_linhas_vazias(nums):
             linhas_vazias = 0
             for r in range(5):
                 inicio = r * 5 + 1
                 fim = inicio + 4
                 if not any(inicio <= n <= fim for n in nums):
                     linhas_vazias += 1
             return linhas_vazias
             
        df_l['Buracos_na_Cartela'] = df_l['numeros'].apply(calc_linhas_vazias)
        
        stats_dia = df_l.groupby('dia_da_semana').agg(
             Media_Soma=('soma', 'mean'),
             Buracos_Anomalos=('Buracos_na_Cartela', 'mean')
        ).reset_index()
        
        # Filtra e ordena
        stats_dia = stats_dia[stats_dia['dia_da_semana'].isin(ordem_dias)]
        stats_dia['Ordem'] = stats_dia['dia_da_semana'].apply(lambda x: ordem_dias.index(x))
        stats_dia = stats_dia.sort_values('Ordem')
        
        c1, c2 = st.columns(2)
        
        with c1:
             st.markdown("**Gravidade: Somas ao longo da Semana**")
             line_soma = alt.Chart(stats_dia).mark_line(point=True, color='red').encode(
                 x=alt.X('dia_da_semana:N', sort=ordem_dias, title='Dia da Semana', axis=alt.Axis(labelAngle=0)),
                 y=alt.Y('Media_Soma:Q', scale=alt.Scale(domain=[193, 197]), title='Soma Média das Bolas'),
                 tooltip=['dia_da_semana', alt.Tooltip('Media_Soma', format='.2f')]
             ).properties(height=300)
             st.altair_chart(line_soma, use_container_width=True)
             
        with c2:
             st.markdown("**Anomalia: 'Buracos' no Volante (Linhas Vazias)**")
             bar_buraco = alt.Chart(stats_dia).mark_bar(color='purple', opacity=0.7).encode(
                 x=alt.X('dia_da_semana:N', sort=ordem_dias, title='Dia da Semana', axis=alt.Axis(labelAngle=0)),
                 y=alt.Y('Buracos_Anomalos:Q', title='Média de Linhas em Branco'),
                 tooltip=['dia_da_semana', alt.Tooltip('Buracos_Anomalos', format='.3f')]
             ).properties(height=300)
             st.altair_chart(bar_buraco, use_container_width=True)

        st.info("💡 **A Teoria é Real?** Observe se as bolinhas pesam mais na Segunda (Soma < 195) comparadas à Sexta-Feira. Quando a máquina esquenta, os números mais pesados (alta gravidade 20-25) demoram mais para subir no duto.")

    elif "Sequências Completas" in teoria:
        st.subheader("🎲 O Caos Gera Ordem? (Repetições Assassinas)")
        st.write("Vamos investigar o que acontece com O JOGO INTEIRO quando encontramos sequências lógicas de 6 dezenas seguidas (ex: 20, 21, 22, 23, 24, 25). Quando isso acontece, o jogo seguinte tenta consertar essa 'anomalia' matando aquele bloco?")
        
        def max_consec_len(nums):
             max_len = 1
             curr_len = 1
             for i in range(len(nums)-1):
                 if nums[i+1] == nums[i] + 1:
                     curr_len += 1
                 else:
                     max_len = max(max_len, curr_len)
                     curr_len = 1
             return max(max_len, curr_len)
             
        df_l['Max_Sequencia'] = df_l['numeros'].apply(max_consec_len)
        
        st.markdown("Quantas vezes uma anomalia extrema (6+ dezenas coladas juntas) ocorreu na história?")
        stats_seq = df_l['Max_Sequencia'].value_counts().sort_index().reset_index()
        stats_seq.columns = ['Tamanho da Sequência Seguidas', 'Qtd Ocorrências']
        
        c1, c2 = st.columns([1,2])
        with c1:
            st.dataframe(stats_seq, use_container_width=True)
            
        with c2:
            st.markdown("### A Reação da Matriz")
            st.write("Um evento lúdico diz que se no jogo de ontem nós tivemos 6 dezenas seguidas no volante (Ex: 01,02,03,04,05,06), no jogo de HOJE o universo espalha as dezenas e o jogo fica com cara de 'xadrez'.")
            
            # Checar se no jogo N tinha anomalia (>=6) e ver métrica do jogo N+1
            df_l['Anomalo_Ontem'] = df_l['Max_Sequencia'] >= 6
            df_l['Anomalo_Ontem_Shift'] = df_l['Anomalo_Ontem'].shift(1).fillna(False)
            
            if df_l[df_l['Anomalo_Ontem_Shift'] == True].empty:
                st.warning("Sem dados históricos suficientes para provar essa quebra.")
            else:
                soma_reacao = df_l[df_l['Anomalo_Ontem_Shift'] == True]['soma'].mean()
                soma_normal = df_l[df_l['Anomalo_Ontem_Shift'] == False]['soma'].mean()
                
                # Para saber se a máquina "espalhou" mais
                df_l['Buracos'] = df_l['numeros'].apply(lambda n: 25 - len(set(n))) # Apenas placeholder
                st.metric("Soma Média PÓS dia de Anomalia (6+ Seguidas)", f"{soma_reacao:.1f}")
                st.metric("Soma Média em Dias Adjacentes Normais", f"{soma_normal:.1f}")
                
                if soma_reacao < soma_normal:
                    st.success("A Teoria Confirma: Quando um jogo forma cobrinhas muito grandes, o sorteio seguinte PUXA AS SOMAS PARA BAIXO para compensar forçando dezenas no início do volante.")
                else:
                    st.error("A Teoria Falha: A máquina não sente o peso matemático da anomalia de ontem. A soma se mantém estável ou maior.")
