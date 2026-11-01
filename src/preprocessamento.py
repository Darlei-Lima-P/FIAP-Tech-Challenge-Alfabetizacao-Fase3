
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer


# Variáveis categóricas
COLUNAS_CATEGORICAS = [
    "dt_ano",
    "cd_uf",
    "cd_rede",
]

# Variáveis numéricas
COLUNAS_NUMERICAS = [
    "qt_escolas_censo",
    "qt_matriculas_censo",
    "qt_docentes_censo",
    "qt_salas_utilizadas_censo",
    "nr_alunos_por_docente",
    "nr_matriculas_por_escola",
    "nr_salas_por_escola",
    "tx_escolas_rurais",
    "tx_escolas_urbanas",
    "tx_escolas_internet",
    "tx_escolas_biblioteca_sala_leitura",
    "tx_escolas_lab_informatica",
    "tx_escolas_quadra",
    "tx_escolas_agua_potavel",
    "tx_escolas_energia_rede_publica",
]

# Tratamento das variáveis numéricas
pipeline_numerico = Pipeline(
    steps=[
        ("imputacao", SimpleImputer(strategy="median")),
        ("escalonamento", StandardScaler()),
    ]
)

# Tratamento das variáveis categóricas
pipeline_categorico = Pipeline(
    steps=[
        ("imputacao", SimpleImputer(strategy="most_frequent")),
        ("codificacao", OneHotEncoder(handle_unknown="ignore")),
    ]
)

# Combinação dos tratamentos
preprocessador = ColumnTransformer(
    transformers=[
        ("numericas", pipeline_numerico, COLUNAS_NUMERICAS),
        ("categoricas", pipeline_categorico, COLUNAS_CATEGORICAS),
    ],
    remainder="drop",
)

if __name__ == "__main__":
    print("Pipeline de pré-processamento configurado.")
    print(f"Variáveis numéricas: {len(COLUNAS_NUMERICAS)}")
    print(f"Variáveis categóricas: {len(COLUNAS_CATEGORICAS)}")
    print(f"Total de preditores: {len(COLUNAS_NUMERICAS) + len(COLUNAS_CATEGORICAS)}")
