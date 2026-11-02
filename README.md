# FIAP Tech Challenge — Avaliação da Alfabetização

## 1. Objetivo

Este projeto tem como objetivo estruturar os dados da Avaliação da
Alfabetização, disponibilizados pela Base dos Dados, utilizando uma arquitetura
de dados em camadas.

A solução implementa um pipeline híbrido, escalável e confiável para integrar
resultados, metas e microdados educacionais, apoiando análises e políticas
públicas baseadas em evidências.

Na etapa analítica, o objetivo é classificar se um aluno é alfabetizado ou não
alfabetizado e interpretar padrões territoriais e escolares associados às
previsões. Os resultados apoiam o diagnóstico das redes de ensino, a
priorização do acompanhamento e a discussão de políticas públicas.

---

## 2. Fonte dos dados

Os dados utilizados são provenientes da Base dos Dados, a partir do conjunto:

**Avaliação da Alfabetização**

A tabela de alunos possui **3.867.999 registros**, referentes aos anos de 2023
e 2024. Os dados de origem foram obtidos em formato CSV e organizados na camada
`RAW` antes da ingestão no data lake.

### Arquivos utilizados

- `alunos.csv`
- `br_inep_avaliacao_alfabetizacao_municipio.csv`
- `br_inep_avaliacao_alfabetizacao_uf.csv`
- `br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_brasil.csv`
- `br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_municipio.csv`
- `br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_uf.csv`

Fonte: Base dos Dados — Avaliação da Alfabetização.

---

## 3. Arquitetura de dados

O projeto utiliza uma organização em camadas seguindo o conceito de arquitetura
de dados em modelo medalhão:

```text
Dados de origem
      ↓
     RAW
      ↓
    BRONZE
      ↓
    SILVER
      ↓
     GOLD
```

A arquitetura contempla ingestão Batch e Streaming simulado, armazenamento no
Amazon S3, catálogo no AWS Glue Data Catalog, consultas no Amazon Athena,
observabilidade e aplicações de inteligência artificial.

### 3.1 Visão completa da solução

![Arquitetura completa da solução](docs/arquitetura-completa.png)

```text
Fontes educacionais
        ↓
Ingestão batch + streaming simulado
        ↓
Amazon S3: Bronze → Silver → Gold
        ↓
Catálogo e consultas analíticas
        ↓
Visualizações, monitoramento e aplicações de IA
```

- **Bronze:** preservação dos dados ingeridos em Parquet Snappy, particionados por ano.
- **Silver:** limpeza, tipagem, padronização, integração e validações de qualidade.
- **Gold:** indicadores por município, UF e Brasil, metas, rankings e evolução temporal.
- **Consumo:** consultas SQL, visualizações, dashboards e aplicações de inteligência artificial.

O fluxo batch processa o histórico completo. O streaming simulado representa a
chegada contínua de eventos, com 500 registros organizados em lotes.

### 3.2 Ingestão Batch

O fluxo Batch carrega os arquivos CSV da camada `RAW` e os converte para
**Parquet** por meio do script:

```text
src/ingest_bronze.py
```

Durante a ingestão:

- os arquivos CSV são carregados;
- os dados são convertidos para Parquet;
- é utilizada compressão Snappy;
- os dados são particionados por ano;
- os arquivos são organizados na camada Bronze.

Ao final da ingestão Batch foram gerados **13 arquivos Parquet**, totalizando
aproximadamente **57,3 MiB**.

#### Base de alunos

- **1.747.439 registros em 2023**
- **2.120.560 registros em 2024**
- **3.867.999 registros no total**

### 3.3 Ingestão Streaming simulada

Como parte da arquitetura híbrida, o script `src/streaming_simulado.py`
processa uma amostra de **500 registros** da tabela de alunos em cinco lotes,
simulando a chegada contínua de eventos.

A validação da simulação confirmou:

- **10 arquivos Parquet**;
- **500 eventos processados**;
- **251 registros de 2023**;
- **249 registros de 2024**.

```text
data/bronze/streaming/
├── ano=2023/
│   ├── lote-001.parquet
│   └── ... lote-005.parquet
└── ano=2024/
    ├── lote-001.parquet
    └── ... lote-005.parquet
```

### 3.4 Organização da camada Bronze

```text
data/bronze/
├── alunos/
│   ├── ano=2023/part-000.parquet
│   └── ano=2024/part-000.parquet
├── municipio/
│   ├── ano=2023/part-000.parquet
│   └── ano=2024/part-000.parquet
├── uf/
│   ├── ano=2023/part-000.parquet
│   └── ano=2024/part-000.parquet
├── meta_brasil/
├── meta_municipio/
├── meta_uf/
└── streaming/
    ├── ano=2023/
    └── ano=2024/
```

A camada Bronze contém **23 objetos**, sendo 13 do processamento Batch e 10 do
Streaming simulado, com aproximadamente **57,4 MiB**.

### 3.5 Armazenamento e consumo na AWS

As camadas do data lake são organizadas no Amazon S3:

- **Bucket:** `fiap-tech-challenge-alfabetizacao-data`
- **Região:** `sa-east-1`

```text
s3://fiap-tech-challenge-alfabetizacao-data/
├── bronze/
├── silver/
└── gold/
```

O AWS Glue Data Catalog mantém os metadados das tabelas e o Amazon Athena
executa consultas SQL diretamente sobre os arquivos Parquet. A separação por
camadas preserva os dados ingeridos, aplica qualidade e integração na Silver e
disponibiliza indicadores prontos para consumo na Gold.

### 3.6 Diagrama inicial da ingestão

O diagrama desenvolvido na primeira fase permanece como visão específica dos
fluxos Batch e Streaming e da construção da camada Bronze:

![Arquitetura inicial da solução](docs/arquitetura-solucao.png)

---

## 4. Resultados das Fases 2 e 3

As três fases técnicas estão concluídas:

| Fase | Entrega | Situação |
|---|---|---|
| 1 | Arquitetura, ingestão híbrida e Bronze | Concluída |
| 2 | Tratamento, integração, Silver e qualidade | Concluída |
| 3 | Gold, consultas, visualizações e IA aplicada | Concluída |

Principais produtos analíticos:

- 10.704 indicadores municipais;
- 54 indicadores por UF;
- 2 indicadores nacionais, referentes a 2023 e 2024;
- cinco visualizações para metas, evolução e desigualdades territoriais.

Em 2024, o indicador nacional foi 59,2%, diante da meta de 59,9%, com evolução
de +3,3 pontos percentuais em relação a 2023.

## 5. Qualidade e governança

O pipeline verifica duplicidades, valores ausentes, chaves de relacionamento e
consistência entre tabelas. Também produz manifestos e relatórios de execução.
A validação final não apresentou erros bloqueantes.

Os dados individuais permanecem nas camadas de processamento. A camada Gold
oferece apenas informações agregadas adequadas ao consumo analítico.

## 6. Monitoramento

A arquitetura prevê o Amazon CloudWatch para acompanhar falhas, duração,
latência e volume processado. EventBridge e Amazon SNS podem distribuir alertas
operacionais. O Amazon Bedrock pode transformar métricas e relatórios de
qualidade em resumos objetivos, sugerindo possíveis causas e próximos passos,
sempre com validação humana.

## 7. Aplicação de inteligência artificial

O Amazon Bedrock pode disponibilizar um assistente analítico sobre a camada
Gold, permitindo perguntas em linguagem natural, geração de resumos para
gestores e apoio à interpretação de alertas. Para modelos preditivos tabulares,
como risco de não atingimento das metas, a camada Gold pode alimentar modelos
no Amazon SageMaker.

Os usos propostos incluem:

- previsão da evolução da alfabetização;
- identificação de municípios com maior risco educacional;
- análise de desigualdades territoriais;
- síntese de indicadores para políticas públicas;
- triagem e contextualização de alertas do pipeline.

Detalhes em [`docs/registro-uso-ia.md`](docs/registro-uso-ia.md).

## 8. Modelagem supervisionada

### 8.1 Objetivo do modelo

Foi desenvolvido um modelo de classificação supervisionada para estimar a classe de alfabetização dos estudantes a partir de indicadores educacionais e características estruturais das redes de ensino.

A variável-alvo utilizada foi `fl_alfabetizado`, com duas classes:

- `0`: Não alfabetizado;
- `1`: Alfabetizado.

A definição do alvo segue o critério aplicado na base de modelagem, derivado da proficiência igual ou superior a 743 pontos. A variável `proficiencia` não foi utilizada como preditora, pois participa diretamente da definição do alvo.

### 8.2 Base de modelagem e pré-processamento

A base utilizada foi `data/gold/fase3/base_modelagem.parquet`, com 3.354.661 registros referentes aos anos de 2023 e 2024.

Foram utilizadas 18 variáveis preditoras: três categóricas (`dt_ano`, `cd_uf` e `cd_rede`) e 15 numéricas relacionadas à estrutura e à infraestrutura escolar.

O pré-processamento foi implementado com `ColumnTransformer` e pipelines do Scikit-learn:

- **Variáveis numéricas:** imputação pela mediana e padronização com `StandardScaler`;
- **Variáveis categóricas:** imputação pela categoria mais frequente e codificação com `OneHotEncoder(handle_unknown="ignore")`.

O pré-processador foi ajustado somente com os dados de treinamento e aplicado aos conjuntos de validação e teste. Identificadores individuais e geográficos não foram utilizados como preditores diretos; `id_municipio` foi utilizado para formar os grupos da divisão dos dados.

### 8.3 Separação dos dados e prevenção de data leakage

Foi utilizado `GroupShuffleSplit`, agrupando os registros por município (`id_municipio`). Assim, um mesmo município não aparece simultaneamente nos conjuntos de treinamento, validação e teste.

A divisão foi realizada em duas etapas:

1. 80% dos registros para desenvolvimento e 20% para teste;
2. dentro do conjunto de desenvolvimento, 80% para treinamento e 20% para validação.

| Conjunto | Registros |
|---|---:|
| Treinamento | 2.169.927 |
| Validação | 512.059 |
| Desenvolvimento total | 2.681.986 |
| Teste reservado | 672.675 |

O conjunto de teste permaneceu reservado durante a comparação e a otimização dos modelos. Após a seleção da configuração, o XGBoost final foi ajustado com todo o conjunto de desenvolvimento e avaliado no teste.

### 8.4 Algoritmos avaliados e seleção

Foram comparados quatro experimentos: Regressão Logística, Random Forest sem balanceamento, Random Forest com balanceamento de classes e XGBoost.

O XGBoost foi selecionado para a avaliação final por apresentar o melhor F1 macro e ROC-AUC na comparação inicial de validação entre as configurações testadas. A escolha não significa superioridade em todas as métricas: o Random Forest balanceado apresentou maior capacidade de identificar a classe não alfabetizado em sua avaliação de validação, sendo uma alternativa relevante caso essa classe tenha prioridade operacional.

### 8.5 Otimização de hiperparâmetros

Foi realizada uma comparação controlada de três configurações do XGBoost, mantendo os mesmos conjuntos de treinamento e validação.

| Configuração | `n_estimators` | `max_depth` | `learning_rate` | F1 macro na validação | ROC-AUC na validação |
|---|---:|---:|---:|---:|---:|
| Baseline | 150 | 6 | 0,05 | **0,5768** | **0,6372** |
| Menor profundidade | 150 | 4 | 0,05 | 0,5477 | 0,6339 |
| Menor profundidade e taxa | 200 | 4 | 0,03 | 0,5429 | 0,6326 |

A configuração baseline apresentou o melhor resultado e foi mantida. Os demais parâmetros foram `subsample=0.8`, `colsample_bytree=0.8`, `objective="binary:logistic"`, `eval_metric="logloss"` e `tree_method="hist"`.

O F1 macro foi 0,5829 no treinamento e 0,5768 na validação, uma diferença de 0,0061. Essa proximidade é um sinal favorável nessa métrica, mas não comprova, isoladamente, ausência de overfitting.

### 8.6 Avaliação final no conjunto de teste

O modelo final foi avaliado em 672.675 registros do conjunto de teste, que não participou da seleção dos hiperparâmetros.

| Métrica | Resultado |
|---|---:|
| Acurácia | 59,67% |
| Precisão | 63,33% |
| Recall | 75,98% |
| F1-score | 69,09% |
| F1 macro | 55,55% |
| ROC-AUC | 0,6220 |
| Balanced Accuracy | 55,95% |

A matriz de confusão, considerando as classes na ordem 0 (não alfabetizado) e 1 (alfabetizado), foi:

| Classe real / prevista | Não alfabetizado | Alfabetizado |
|---|---:|---:|
| Não alfabetizado | 98.315 | 175.465 |
| Alfabetizado | 95.800 | 303.095 |

O recall foi de 35,91% para a classe não alfabetizado e 75,98% para a classe alfabetizado. Portanto, o modelo identifica melhor os estudantes classificados como alfabetizados e apresenta desempenho desigual entre as classes. Esse comportamento deve ser considerado antes de qualquer aplicação prática.

### 8.7 Interpretabilidade: Feature Importance e SHAP

A interpretabilidade foi explorada por meio da importância interna das variáveis no XGBoost e dos valores SHAP. Foram gerados os gráficos de Feature Importance, SHAP Beeswarm, importância global SHAP e SHAP Waterfall.

As categorias de UF apareceram entre as variáveis mais influentes, com destaque para `cd_uf_23`, `cd_uf_29`, `cd_uf_41` e `cd_uf_31`. Entre as variáveis numéricas, destacaram-se `tx_escolas_internet`, `qt_escolas_censo` e `qt_matriculas_censo`.

A análise SHAP foi calculada sobre uma amostra do conjunto de teste. Os valores SHAP representam contribuições das variáveis para as previsões do modelo; não demonstram causalidade. A predominância de categorias geográficas indica que o modelo utiliza diferenças territoriais como sinal preditivo e merece atenção na interpretação.

Os arquivos de resultados foram armazenados em `reports/`, e os gráficos em `reports/images/`.

### 8.8 Limitações da modelagem

- O desempenho é desigual entre as classes, com recall menor para estudantes não alfabetizados.
- A divisão por município avalia a generalização para municípios não vistos, mas municípios de um mesmo estado podem estar nos conjuntos de desenvolvimento e teste. Portanto, não comprova generalização para estados inteiramente desconhecidos.
- A influência elevada das variáveis de UF indica dependência de padrões geográficos; não se deve interpretar essa associação como causalidade.
- A disponibilidade temporal dos indicadores externos, especialmente os provenientes do Censo e de outras fontes, precisa ser verificada antes de utilizar o modelo em um cenário de previsão anterior à avaliação dos estudantes.
- A otimização foi limitada à comparação de três configurações do XGBoost. Não foi realizada busca exaustiva de hiperparâmetros nem validação cruzada.

Assim, o modelo deve ser considerado uma ferramenta experimental de classificação e análise, não um substituto de avaliações educacionais oficiais ou de decisões de políticas públicas.

### 8.9 Principais insights e respostas de negócio

O diagnóstico territorial utiliza os indicadores oficiais agregados de
alfabetização e metas. A modelagem utiliza a base de alunos efetivamente
avaliados, com 3.354.661 registros. As taxas desses dois recortes têm
denominadores e métodos de cálculo diferentes e devem ser interpretadas
separadamente.

| Pergunta de negócio | Evidência e interpretação |
|---|---|
| Quais fatores estão associados à alfabetização? | As previsões dependem fortemente do contexto territorial. Na análise SHAP, também aparecem acesso à internet, quantidade de escolas e matrículas por escola. São associações preditivas, sem demonstração de causalidade. |
| Quais municípios demandam maior atenção? | Em 2024, 2.444 municípios ficaram abaixo de suas metas. Sério/RS, Arroio do Padre/RS e São Vendelino/RS apresentam déficits de 68,9, 61,8 e 55 pontos percentuais, respectivamente. Esses exemplos orientam o aprofundamento do diagnóstico; a prioridade também deve considerar o número de alunos e a participação na avaliação. |
| Quais territórios apresentam resultados semelhantes? | Bahia, Sergipe e Rio Grande do Norte registraram taxas de 35,96%, 38,39% e 39,29%. Paraná, Espírito Santo, Minas Gerais e Goiás ficaram entre 70,42% e 72,74%. A semelhança é descritiva, baseada nas taxas observadas. Não foi realizado clustering nem comprovada equivalência de contexto ou de práticas educacionais. |
| Como apoiar a antecipação de dificuldades para atingir metas futuras? | O uso atual é acompanhar a evolução histórica e a distância para as metas. A previsão temporal de não atingimento de metas municipais é uma evolução proposta, ainda não implementada e validada. O modelo atual classifica alunos. |
| Quais variáveis mais influenciam o modelo? | As categorias de UF, especialmente Ceará, Bahia, Paraná e Minas Gerais, se destacam na importância interna do XGBoost. A análise SHAP complementa essa leitura com contribuições de indicadores escolares. Importância não representa a taxa de alfabetização nem o efeito causal de uma variável. |

Em nível nacional, a alfabetização na rede pública avançou de 55,9% em 2023
para 59,2% em 2024, uma alta de 3,3 pontos percentuais. O resultado ficou 0,7
ponto percentual abaixo da meta de 59,9% para 2024. Em relação ao objetivo
de 80% para 2030, a distância observada em 2024 foi de 20,8 pontos
percentuais. Essa comparação com a meta não constitui uma previsão.

As evidências estão em [`docs/evidencias/fase-3/`](docs/evidencias/fase-3/),
[`reports/`](reports/) e [`reports/images/`](reports/images/).

### 8.10 Aplicação prática para políticas públicas

As recomendações a seguir são propostas da equipe a partir dos resultados.
A análise não testou a eficácia de intervenções específicas e não comprova
que os municípios com maior déficit também apresentem baixa conectividade.

| Uso para a gestão | Ação recomendada | Acompanhamento |
|---|---|---|
| Priorizar o apoio pedagógico | Combinar distância da meta, volume de alunos e participação na avaliação para selecionar redes que demandam atenção. Nessas redes, aprofundar o diagnóstico das habilidades de alfabetização e orientar ações de recuperação da aprendizagem. | Evolução da alfabetização, distância para a meta e cobertura da avaliação. |
| Investigar as condições de conectividade | Cruzar o diagnóstico educacional com a cobertura de internet do Censo Escolar. Nas redes com déficit e baixa cobertura, levantar as escolas sem acesso e avaliar as condições de uso dos recursos digitais antes de direcionar investimentos. | Cobertura de internet nas escolas e evolução dos resultados educacionais. |
| Comparar práticas entre redes | Selecionar redes de porte e contexto semelhantes, com resultados diferentes, para investigar práticas pedagógicas e possibilidades de adaptação local. Taxas próximas, isoladamente, não bastam para definir esses pares. | Evolução das taxas e dos indicadores de contexto das redes comparadas. |

O fluxo de decisão proposto é consultar os indicadores territoriais,
selecionar redes por critérios transparentes, aprofundar o diagnóstico
local, definir as ações e revisar os resultados ao longo do tempo. As
previsões do modelo entram como informação complementar. O baixo recall
para alunos não alfabetizados impede que sejam usadas como critério
exclusivo para selecionar ou excluir estudantes do apoio educacional.

### 8.11 Possíveis evoluções futuras

- Incorporar séries históricas adicionais e validar a generalização temporal
  antes de desenvolver alertas de não atingimento de metas municipais.
- Avaliar o uso das variáveis socioeconômicas já disponíveis na base,
  verificando sua disponibilidade no momento da previsão. População, PIB e
  densidade não integram os 18 preditores atuais.
- Ampliar a validação por grupos e a comparação de modelos, examinando o
  desempenho por território e por classe. Ajustar limiares e balanceamento
  conforme o custo dos erros na aplicação pretendida.
- Avaliar calibração e desempenho das probabilidades agregadas por município
  antes de usá-las em decisões territoriais.
- Aprofundar hipóteses analíticas, relações entre variáveis e comparações
  entre redes de contexto semelhante.
- Automatizar a sequência de preparação, treinamento e avaliação e preservar
  a tabela completa dos experimentos para ampliar a rastreabilidade.

---

## 9. FinOps

As decisões de arquitetura reduzem custo sem comprometer a análise:

- Parquet e compressão Snappy reduzem armazenamento e leitura;
- particionamento por ano evita varreduras desnecessárias;
- consultas sobre a camada Gold reduzem o volume processado;
- serviços gerenciados e execução sob demanda evitam capacidade ociosa;
- métricas de uso permitem acompanhar volume, duração e consumo.

## 10. Decisões de arquitetura e trade-offs

- **Batch e streaming:** batch garante reprocessamento histórico; streaming atende eventos recentes e adiciona complexidade operacional.
- **Data lake e warehouse:** o data lake preserva flexibilidade e baixo custo; a Gold fornece o contrato analítico necessário ao consumo.
- **Custo e performance:** arquivos colunares, partições e agregações antecipadas favorecem consultas rápidas com menor leitura.

## 11. Reprodução e validação

Requer Python 3.11 ou superior e Git LFS para obter os arquivos grandes.
Execute os comandos de processamento e modelagem a partir da raiz do
repositório.

### 11.1 Obter o código e os dados

```bash
git clone https://github.com/Darlei-Lima-P/FIAP-Tech-Challenge-Alfabetizacao-Fase3.git
cd FIAP-Tech-Challenge-Alfabetizacao-Fase3
git checkout feature/modelagem-shap-darlei
git lfs install
git lfs pull
```

A base usada no treinamento está em
`data/gold/fase3/base_modelagem.parquet`. Os arquivos Parquet, CSV e outros
arquivos grandes são gerenciados por Git LFS. Um arquivo de ponteiro LFS
não substitui os dados necessários à execução.

### 11.2 Preparar o ambiente

No Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

No Linux ou macOS, a ativação do ambiente é feita com
`source .venv/bin/activate`.

### 11.3 Executar a engenharia de dados e seus testes

```bash
python -m src.pipeline all
python -m pytest -q
```

Resultado de referência: `9 passed`. Esses testes verificam as camadas de
dados, os indicadores, as regras de qualidade e as visualizações. Eles não
executam o treinamento e a avaliação dos modelos de Machine Learning.

### 11.4 Reproduzir a modelagem e a explicabilidade

Com a base `data/gold/fase3/base_modelagem.parquet` disponível, execute:

```bash
python src/avaliar_split.py
python src/treinar_modelo.py
python src/otimizar_xgboost.py
python src/avaliacao_final_shap.py
```

| Script | Finalidade |
|---|---|
| `src/avaliar_split.py` | Conferir a distribuição dos conjuntos e a ausência de municípios compartilhados. |
| `src/treinar_modelo.py` | Comparar os quatro experimentos de classificação e apresentar os resultados de validação no terminal. |
| `src/otimizar_xgboost.py` | Comparar três configurações e salvar `reports/otimizacao_xgboost.csv`. |
| `src/avaliacao_final_shap.py` | Ajustar o modelo final, avaliar o teste reservado, gerar os gráficos e salvar o modelo com o pré-processador. |

Os resultados ficam em `reports/` e `reports/images/`. O artefato final fica
em `models/modelo_xgboost_final.joblib`. A execução final refaz o treinamento
e substitui os artefatos gerados nesses caminhos. O tempo e o consumo de
memória dependem do equipamento.

O comando `python -m src.pipeline all` cobre a engenharia de dados; a
sequência de Machine Learning acima é executada separadamente.

### 11.5 Regenerar a base enriquecida

Para reconstruir a base de modelagem, utilize
[`notebooks/01_eda_fase3.ipynb`](notebooks/01_eda_fase3.ipynb), com o
diretório de trabalho em `notebooks/`. O notebook utiliza as camadas
Silver, os arquivos externos do Censo Escolar e de área territorial e as
APIs do IBGE.

Além de `requirements.txt`, a execução desse notebook requer `requests`
para as consultas HTTP e `xlrd` para a leitura do arquivo `.xls`:

```bash
pip install requests xlrd
```

Essa reconstrução não é necessária para consumir a base final já
disponibilizada. Consultas e ingestões específicas na AWS dependem da
configuração e das permissões do ambiente correspondente.

## 12. Estrutura e evidências

- [Mapa das pastas](docs/estrutura-do-projeto.md)
- `data/bronze/`: dados de entrada em Parquet
- `data/silver/`: dados tratados, integrados e validados
- `data/gold/`: indicadores e agregações analíticas
- [Implementação técnica das Fases 2 e 3](docs/implementacao-fases-2-3.md)
- [Registro e proposta de uso de IA](docs/registro-uso-ia.md)
- [Visualizações e resumos analíticos](docs/evidencias/fase-3/)

As definições e consultas do Amazon Athena estão em `sql/athena/`. Consultas
complementares de validação estão versionadas em `sql/analytics/`.

## 13. Tecnologias utilizadas

Python, Pandas, DuckDB, PyArrow, Parquet, Scikit-learn,
XGBoost, SHAP, Amazon S3, AWS Glue Data Catalog,
Amazon Athena, Amazon CloudWatch, Amazon Bedrock e Amazon SageMaker.

O código, os testes e a documentação estão versionados em Git. A branch de
continuidade da equipe é `feature/modelagem-shap-darlei`.
