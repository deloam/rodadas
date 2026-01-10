# 🧠 LotoIA - Inteligência Artificial para Lotofácil

> **Sistema de Alta Performance** que combina Deep Learning (LSTM), Estatística Híbrida e Backtesting Financeiro para maximizar suas chances.

![Badge License](https://img.shields.io/badge/license-MIT-green) ![Badge Python](https://img.shields.io/badge/python-3.11-blue) ![Badge Tensorflow](https://img.shields.io/badge/tensorflow-keras-orange) ![Badge Status](https://img.shields.io/badge/status-active-success)

---

## ✨ Funcionalidades Principais

O **LotoIA** não é apenas um gerador de números aleatórios. É uma plataforma completa de análise quantitativa:

### 🔮 1. Previsão Híbrida (AI + Stat)
Utilizamos um "Cérebro Triplo" para gerar palpites:
- **🤖 Rede Neural LSTM:** Aprende padrões sequenciais complexos de longo prazo.
- **📈 Tendência de Frequência:** Analisa o "momento" dos números nos últimos 10 concursos.
- **⏱️ Fator de Atraso:** Identifica matematicamente números "maduros" para sair.
- **🎯 Filtros Manuais:** Permite ao usuário **Fixar** ou **Excluir** números específicos.

### 📊 2. Análise de Padrões (DNA do Jogo)
Visualizações ricas para entender a estrutura dos sorteios:
- **Métricas de Equilíbrio:** Gráficos de Ímpares vs Pares, Primos e Soma Total.
- **Estatísticas de Gaps:** Tempo médio que duplas e trios demoram para sair novamente.
- **Top Recorrências:** As combinações que mais saem juntas na história.

### 🧪 3. Laboratório de Backtest & Financeiro
Não confie cegamente. Teste!
- **Simulação Real:** "Viaje no tempo" e rode a IA em concursos passados (ex: últimos 50).
- **IA vs Sorte:** Gráfico comparativo mostrando o desempenho da IA contra jogos aleatórios.
- **Relatório Financeiro:** Cálculo automático de **Investimento**, **Retorno** e **Lucro Líquido** real.

### 🔢 4. Desdobrador Econômico
- Transforme previsões caras (16, 17, 20 números) em múltiplos jogos simples de **R$ 3,50**.
- **Download Automático:** Baixe seus jogos prontos em `.txt`.

---

## 🛠️ Tecnologias Utilizadas

Este projeto foi construído com uma stack moderna de Data Science:

- **Frontend:** [Streamlit](https://streamlit.io/) (Interface Reativa e Moderna)
- **Core AI:** [TensorFlow / Keras](https://www.tensorflow.org/) (Modelos LSTM)
- **Data:** [Pandas](https://pandas.pydata.org/) & [NumPy](https://numpy.org/)
- **Viz:** [Altair](https://altair-viz.github.io/) (Gráficos Interativos)

---

## 🚀 Como Executar

Certifique-se de ter o **Python 3.11** instalado.

1. **Clone o repositório e entre na pasta:**
   ```bash
   cd IA_Tensor
   ```

2. **Instale as dependências:**
   ```bash
   pip install streamlit pandas numpy tensorflow altair
   ```

3. **Execute a aplicação:**
   ```bash
   python -m streamlit run app.py
   ```

4. **Acesse no navegador:**
   O sistema abrirá automaticamente em `http://localhost:8501`.

---

## 📸 Screenshots

### Painel de Previsão & Heatmap
Visualize as "zonas quentes" do volante antes de jogar.

### Laboratório de Backtest
Valide se a estratégia está lucrando antes de gastar dinheiro real.

---

⚠️ **Aviso Legal:** *Este software é uma ferramenta de análise estatística e educacional. Não garantimos lucros. Jogos de loteria envolvem risco de perda financeira. Jogue com responsabilidade.*
