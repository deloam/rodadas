# 🧠 LotoIA Pro 2.1 - Sistema de Inteligência Artificial Avançada para Lotofácil

> **A Plataforma Definitiva** que combina Deep Learning, Machine Learning Não-Supervisionado, Análise de Riscos, Sincronicidade Financeira e Visualização Avançada para maximizar suas chances estatísticas.

![Badge Version](https://img.shields.io/badge/version-2.1-purple) ![Badge License](https://img.shields.io/badge/license-MIT-green) ![Badge Python](https://img.shields.io/badge/python-3.11-blue) ![Badge Database](https://img.shields.io/badge/sqlite-integrated-blue)

---

## ✨ O Que Há de Novo na Versão 2.1?

A **LotoIA 2.1** introduz o conceito de **"Caos Exógeno"** e migra para uma arquitetura de dados profissional.

### 🌌 1. Caos Exógeno (Sincronicidade) 🆕
A IA agora analisa o mundo real fora da loteria em busca de correlações ocultas.
- **Mercado Financeiro:** Cruza os sorteios com a alta/baixa da Bolsa (IBOV), Dólar e Ações de Bancos (Itú, Bradesco, Caixa Seguridade).
- **Fases da Lua:** Verifica se a luminosidade lunar influencia a saída de certos números.
- **Termômetro Político:** Monitora o Risco Brasil (EWZ) como proxy de instabilidade.
- **Oráculo Diário:** Simule "Se a Bolsa cair 2% hoje, quais números ganham força?".

### 💾 2. Banco de Dados SQLite (Alta Performance) 🆕
- Migração completa do sistema de arquivos para **SQLite (`previsoes.db`)**.
- **Data Lake Unificado:** Armazena Histórico de Jogos + Dados Financeiros + Previsões da IA no mesmo lugar.
- **Espelhamento Automático:** Sincroniza o `rodadas.json` com o banco a cada inicialização.

### 🛡️ 3. IA Crítica ("Advogado do Diabo")
Chega de apostar no escuro. Para cada palpite gerado, um módulo validador independente entra em ação:
- **Análise de Risco:** Detecta anomalias estatísticas perigosas (ex: "Sequência de 6 números", "Soma muito baixa").
- **Alertas Visuais:** Se a IANeural gostar do jogo, mas a IA Estatística achar arriscado, você recebe um alerta vermelho ⚠️ imediatamente.

### 🔭 4. Radar de Equilíbrio
Visualização gráfica intuitiva para cada palpite gerado.
- **Gráfico de Barras "Equalizador":** Mostra visualmente se o jogo está equilibrado nos 5 pilares fundamentais (Ímpares, Primos, Moldura, Fibonacci, Soma).
- **Leitura Fácil:** Barras Verdes = Jogo Perfeito. Barras Amarelas/Vermelhas = Desequilíbrio.

### 🧬 5. Clusterização Inteligente (Machine Learning)
Usamos algoritmos não-supervisionados (**K-Means**) para mapear a "tabela periódica" dos sorteios.
- **Famílias de Jogos:** O sistema dividiu toda a história em 5 Arquétipos Matemáticos.
- **Dicionário Explicativo:** Agora você sabe exatamente o que significa "Família 2 (Soma Alta)".
- **Previsão de Contexto:** A IA diz a qual família pertence o momento atual do mercado.

### 📡 6. Detector de Tendências (Curto Prazo)
Enquanto a Rede Neural olha padrões profundos, este módulo monitora o "humor" recente do mercado (últimos 20 jogos).
- **Alertas de Viés:** Avisa se está saindo mais Ímpares ou Primos do que o normal estatístico, permitindo ajustes táteis na estratégia.

---

## 🧠 Funcionalidades Core (Mantidas e Melhoradas)

### 🤖 Ensemble AI (Cérebro Híbrido)
- **LSTM (Deep Learning):** Padrões sequenciais longos.
- **Random Forest:** Regras de decisão complexas.
- **Frequência e Atraso:** Pesos dinâmicos baseados no momento.

### 📘 Manual Integrado
- Nova aba dedicada com explicações didáticas sobre cada funcionalidade do sistema.

### ☀️ Dashboard Executivo
- "Briefing do Dia" com as melhores oportunidades e status dos ciclos.

### 🕵️‍♂️ Feedback Loop
- Histórico persistente que salva não só os números, mas o DNA e a Confiança da IA no momento da geração para auditoria futura.

---

## 🛠️ Tecnologias Utilizadas

- **Frontend:** [Streamlit](https://streamlit.io/) (Layout Wide Mode)
- **Deep Learning:** [TensorFlow / Keras](https://www.tensorflow.org/)
- **Machine Learning:** [Scikit-Learn](https://scikit-learn.org/) (KMeans, Random Forest)
- **Data Engineering:** [Pandas](https://pandas.pydata.org/) & [NumPy](https://numpy.org/) & **SQLite**
- **Visualização:** [Altair](https://altair-viz.github.io/) (Radar Charts, Heatmaps)
- **Financeiro:** [yFinance](https://pypi.org/project/yfinance/) (Dados de Mercado)

---

## 🚀 Como Executar

Certifique-se de ter o **Python 3.11** instalado.

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/seususuario/lotoia-pro.git
   cd lotoia-pro/IA_Tensor
   ```

2. **Instale as dependências:**
   ```bash
   pip install streamlit pandas numpy tensorflow scikit-learn altair requests joblib yfinance
   ```

3. **Execute a aplicação:**
   ```bash
   python -m streamlit run app.py
   ```

4. **Acesse:** `http://localhost:8501`

---

## 📸 Estrutura do App

1.  **📘 Manual:** Guia interativo e didático.
2.  **🔮 Previsão:** IA Generativa + Validação de Riscos + Radar.
3.  **📊 Análise:** Clusters, Tendências, Ciclos e Heatmaps.
4.  **🏗️ Montador:** Criação manual assistida.
5.  **🔢 Desdobrador:** Fechamentos matemáticos.
6.  **🧪 Laboratório:** Backtesting financeiro.
7.  **🌌 Caos Exógeno:** Sincronicidade com Mercado Financeiro, Política e Fases da Lua.

---

⚠️ **Aviso Legal:** *Ferramenta de análise estatística para auxiliar na tomada de decisão. Não garante lucros. Jogue com responsabilidade.*
