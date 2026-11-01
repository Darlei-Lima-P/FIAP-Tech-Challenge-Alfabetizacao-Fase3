
import duckdb
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

CAMINHO = "data/gold/fase3/base_modelagem.parquet"

# Carrega somente as colunas necessárias para avaliar a divisão
con = duckdb.connect()
df = con.execute(
    """
    SELECT
        id_municipio,
        dt_ano,
        fl_alfabetizado
    FROM read_parquet(?)
    """,
    [CAMINHO]
).df()

# Primeira divisão: 80% desenvolvimento e 20% teste
split_teste = GroupShuffleSplit(
    n_splits=1,
    test_size=0.20,
    random_state=42
)

idx_dev, idx_teste = next(
    split_teste.split(df, groups=df["id_municipio"])
)

desenvolvimento = df.iloc[idx_dev].copy()
teste = df.iloc[idx_teste].copy()

# Segunda divisão: 80% treinamento e 20% validação
split_validacao = GroupShuffleSplit(
    n_splits=1,
    test_size=0.20,
    random_state=42
)

idx_treino, idx_validacao = next(
    split_validacao.split(
        desenvolvimento,
        groups=desenvolvimento["id_municipio"]
    )
)

treino = desenvolvimento.iloc[idx_treino]
validacao = desenvolvimento.iloc[idx_validacao]

# Relatório das proporções
conjuntos = {
    "Treinamento": treino,
    "Validação": validacao,
    "Teste": teste
}

print("\nDISTRIBUIÇÃO DOS CONJUNTOS")
for nome, dados in conjuntos.items():
    print(f"\n{nome}")
    print(f"Alunos: {len(dados):,}")
    print(f"Municípios: {dados['id_municipio'].nunique():,}")
    print(
        "Taxa de alfabetização: "
        f"{dados['fl_alfabetizado'].mean():.2%}"
    )

    print("\nDistribuição por ano:")
    print(
        dados.groupby("dt_ano")["fl_alfabetizado"]
        .agg(["count", "mean"])
        .to_string()
    )

# Verifica se algum município aparece em mais de um conjunto
grupos = {
    nome: set(dados["id_municipio"].unique())
    for nome, dados in conjuntos.items()
}

print("\nVERIFICAÇÃO DE SOBREPOSIÇÃO DE MUNICÍPIOS")
print("Treino x Validação:", len(grupos["Treinamento"] & grupos["Validação"]))
print("Treino x Teste:", len(grupos["Treinamento"] & grupos["Teste"]))
print("Validação x Teste:", len(grupos["Validação"] & grupos["Teste"]))
