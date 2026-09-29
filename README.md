# Modelagem Preditiva de Decisões Judiciais nas Varas de Relações de Consumo da Comarca de Salvador com Aprendizado de Máquina

> **Linha Metodológica (Abordagem 2):** Modelagem preditiva com pipelines especializados adaptados à hipótese indutiva de cada família algorítmica (*Regressão Harmônica de Fourier* para modelos lineares e *Representação Densa/Compacta* para árvores de decisão).

Este repositório contém a pesquisa, os datasets, os scripts de coleta da API DataJud (CNJ), os notebooks de experimentação e o artigo em LaTeX (padrão IEEE) referente ao Trabalho de Conclusão de Curso (TCC) no curso de Análise e Desenvolvimento de Sistemas (ADS) do Instituto Federal da Bahia (IFBA - Salvador).

---

## 📁 Estrutura do Repositório

```text
tcc-jurimetria-pipelines-especializados/
├── jurimetria.ipynb                   # NOTEBOOK MESTRE (Pipelines Especializados, Treinamento e Diagnósticos)
├── overleaf_main.tex                  # Artigo científico diagramado em LaTeX (IEEEtran Conference)
├── arvore.png                         # Figura 2 referenciada no artigo científico
├── vies_variancia.png                 # Figura 1 referenciada no artigo científico
├── requirements.txt                   # Dependências e bibliotecas Python
├── README.md                          # Documentação e instruções de execução
├── .env.example                       # Modelo de configuração de variáveis de ambiente
├── .gitignore                         # Regras de exclusão (bibliografia/ e dados sensíveis)
│
├── data/                              # Datasets processuais extraídos da API pública do DataJud
│   ├── dataset_relacoes_consumo.csv   # Base primária consolidada (2020 a 2024)
│   └── dataset_processado.csv         # Base higienizada com filtragem de mérito
│
├── resultados/                        # Gráficos analíticos oficiais exportados em alta resolução (300 DPI)
│   ├── comparacao_feature_importance_3_modelos.png
│   ├── curva_aprendizado_volume_dados.png
│   ├── curva_calibracao_3_modelos.png
│   ├── curva_pr_3_modelos.png
│   ├── curva_roc_3_modelos.png
│   ├── matrizes_confusao_3_modelos.png
│   ├── top15_coeficientes_regressao_logistica.png
│   └── xgboost_curva_aprendizado.png
│
└── scripts/
    └── extrair_datajud.py             # Script de extração automatizada da API pública do DataJud (TJBA)
```

---

## 🏛️ Metodologia e Pipelines Especializados (Abordagem 2)

Em vez de impor uma representação de dados uniforme que fragilize o sorteio de variáveis em árvores ou viole premissas lineares, adotam-se fluxos de engenharia de atributos adaptados à hipótese indutiva de cada família:

1. **Pipeline do Modelo Linear (Regressão Logística ElasticNet):**
   * **Regressão Harmônica de Fourier:** Projeção circular ortogonal dos componentes temporais cíclicos (mês e dia da semana) em termos de seno e cosseno:
     $$\text{mês}_{\sin} = \sin\left(\frac{2\pi \cdot \text{mês}}{12}\right), \quad \text{mês}_{\cos} = \cos\left(\frac{2\pi \cdot \text{mês}}{12}\right)$$
   * Evita a imposição de falsa linearidade ordinal e previne o inchaço dimensional do *One-Hot Encoding*.
   * Padronização contínua via `StandardScaler` e regularização convexa mista $L_1/L_2$ (*ElasticNet*).

2. **Pipeline dos Modelos de Árvore (Random Forest e XGBoost):**
   * **Representação Tabular Densa e Compacta:** Mantém as variáveis temporais em escala ordinal discreta e aplica *Target Encoding Out-of-Fold* (OOF) com suavização bayesiana ($m=20$) para Varas e Assuntos TPU.
   * **Preservação do Ganho de Gini:** Ao eliminar dezenas de colunas binárias esparsas, impede a diluição estatística no sorteio aleatório de atributos candidatos ($m \approx \sqrt{d}$), assegurando que o algoritmo selecione divisões informativas.

3. **Validação Temporal Estrita (Anti-Leakage):**
   * Particionamento cronológico via `TimeSeriesSplit` nas safras de 2020 a 2023.
   * Avaliação final sobre a safra de teste cego de 2024 (*Out-of-Time*).

4. **Fundamentação Teórica e Princípio da Parcimônia:**
   * Mesmo quando submetidos a seus pipelines ideais, os modelos de árvore e a Regressão Logística apresentam **empate técnico** (ROC-AUC $\approx 0,73$).
   * Esse resultado valida empiricamente o limite preditivo postulado pela **Hipótese de Seleção de Litígios de Priest e Klein**, fundamentando a seleção da Regressão Logística sob a ótica da **Navalha de Ockham** (alta explicabilidade jurídica com menor complexidade estrutural).

---

## 🚀 Como Executar o Projeto

### 1. Clonar e Acessar o Repositório
```bash
git clone https://github.com/SEU_USUARIO/tcc-jurimetria-pipelines-especializados.git
cd tcc-jurimetria-pipelines-especializados
```

### 2. Configurar o Ambiente Virtual e Instalar Dependências
```bash
python -m venv .venv
# No Windows:
.venv\Scripts\activate
# No Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Extração da API DataJud (Opcional)
Para executar nova coleta de dados:
1. Copie o arquivo `.env.example` para `.env`:
   ```bash
   cp .env.example .env
   ```
2. Insira sua chave pública da API DataJud no `.env`.
3. Execute o script:
   ```bash
   python scripts/extrair_datajud.py
   ```

### 4. Executar o Notebook
```bash
jupyter notebook jurimetria.ipynb
```

---

## ✒️ Autoria e Afiliação Institucional
* **Autor:** Vinícius Matos dos Santos (`viniciusmatoslyon@gmail.com`)
* **Orientador:** Prof. Pablo Vieira Florentino (`pablovf@ifba.edu.br`)
* **Instituição:** Instituto Federal de Educação, Ciência e Tecnologia da Bahia (IFBA - Campus Salvador)
* **Curso:** Bacharelado em Análise e Desenvolvimento de Sistemas (ADS)
