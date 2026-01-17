import streamlit as st

def renderizar_manual_instrucoes():
    st.markdown("""
    ## 📘 Manual do Usuário - IA Lotofácil Pro

    Bem-vindo ao sistema de inteligência artificial mais avançado para análise e previsão de loterias.
    Este guia explica cada módulo para você tirar o máximo proveito.

    ---

    ### 🔮 1. Aba "Previsão" (O Coração do Sistema)
    Aqui é onde a mágica acontece. A IA usa **Redes Neurais (LSTM)** e **Florestas Aleatórias** para prever o futuro.

    *   **Botão "Gerar Palpites com IA":** Ao clicar, o sistema simula milhares de jogos e escolhe os melhores.
    *   **Os Palpites (Cartões):**
        *   **Confiança IA (Barra Amarela/Verde):** Quanto a rede neural "gosta" matematicamente daquele jogo específico.
        *   **Badges (Etiquetas):** Mostram o DNA do jogo (Ex: "Ímpares: 8", "Primos: 5").
            *   ✅ **Verde:** O jogo está equilibrado e segue os padrões históricos.
            *   ⚠️ **Vermelho:** O jogo é "ousado" e foge do padrão comum.
        *   **Advogado do Diabo (Texto Vermelho):** Se aparecer um texto vermelho embaixo dos números, cuidado! A IA detectou um risco grave (ex: sequência de 6 números seguidos).
        *   **Radar de Equilíbrio (Botão Expansível):** Clique para ver um gráfico que mostra se o jogo é "perfeito" ou "torto".

    ---

    ### 📊 2. Aba "Análise" (O Cérebro Estatístico)
    Ferramentas para você entender o comportamento do mercado.

    *   **📡 Detector de Tendências (Beta):**
        *   Analisa os últimos 20 jogos.
        *   Diz se está saindo **muitos** ou **poucos** Ímpares, Primos, etc.
        *   **Dica:** Se diz "Tendência de ALTA em Ímpares", prefira jogar com 9 ou 10 ímpares nos seus jogos.
    
    *   **🧬 Clusterização Inteligente (Famílias):**
        *   A IA dividiu todos os sorteios da história em 5 "Famílias" (Ex: Família dos Pares, Família da Soma Alta).
        *   Mostra a qual família pertenceu o último jogo. Isso ajuda a entender o "humor" do momento.
    
    *   **Padrões Recentes & Ciclos:**
        *   **Ciclo:** Mostra quais números faltam sair para fechar o ciclo atual (todos os 25 números serem sorteados).
        *   **Repetentes:** Mostra quantos números costumam repetir do concurso anterior (a média é 9).

    ---

    ### 🏗️ 3. Aba "Montador" (Controle Manual)
    Para quando você quer montar seu jogo, mas com ajuda da máquina.
    *   Você clica nos números que quer incluir ou excluir.
    *   A IA completa o resto para você, garantindo que o jogo fique equilibrado matematicamente.

    ---

    ### 🔢 4. Aba "Desdobrador" (Jogos Econômicos)
    *   Permite jogar com mais números (ex: 18 ou 20 números) sem pagar uma fortuna.
    *   Ele cria "Desdobramentos Inteligentes" que garantem prêmios menores (13 ou 14 pontos) se você acertar os números escolhidos.

    ---

    ### 🧪 5. Aba "Laboratório" (Backtest)
    *   **Máquina do Tempo:** Permite testar a IA no passado.
    *   Exemplo: "Se eu tivesse usado essa IA nos últimos 10 concursos, quanto eu teria ganho?"
    *   Essencial para validar se a estratégia está funcionando antes de apostar dinheiro real.

    ---

    ### 🌌 6. Aba "Caos Exógeno" (Inédito)
    *   **Oráculo Financeiro & Natural:** Analisa correlações ocultas entre os sorteios e fatores externos.
    *   **Heatmap:** Descubra se números específicos da loteria "gostam" quando a Bolsa sobe ou quando é Lua Cheia.
    *   **Simulador:** Simule o cenário de hoje (ex: Dólar caiu) para ver quais números ganham força.
    
    > **Nota Técnica:** O sistema agora salva automaticamente todos os dados em um Banco de Dados ultrarrápido (`previsoes.db`) para aprender mais a cada dia.

    ---

    ### 💡 Dicas de Ouro
    1.  **Não jogue apenas por jogar.** Olhe sempre as **Badges** e o **Radar**. Jogos equilibrados ganham mais.
    2.  **Use os Filtros:** Na barra lateral à esquerda, você pode "Obrigatório" (Fixar) números que você tem certeza que vão sair.
    3.  **Atenção aos Riscos:** Se o "Advogado do Diabo" der um alerta vermelho, pense duas vezes.
    """)
