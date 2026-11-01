
import gc
import time
from pathlib import Path

import duckdb
import pandas as pd

from xgboost import XGBClassifier

from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    balanced_accuracy_score,
)

from preprocessamento import (
    preprocessador,
    COLUNAS_CATEGORICAS,
    COLUNAS_NUMERICAS,
)


# ============================================================
# 1. CONFIGURACOES
# ============================================================

CAMINHO_BASE = "data/gold/fase3/base_modelagem.parquet"

ALVO = "fl_alfabetizado"
GRUPO = "id_municipio"
RANDOM_STATE = 42

PASTA_RELATORIOS = Path("reports")
PASTA_RELATORIOS.mkdir(parents=True, exist_ok=True)

COLUNAS_PREDITIVAS = (
    COLUNAS_CATEGORICAS + COLUNAS_NUMERICAS
)

COLUNAS_LEITURA = (
    [GRUPO, ALVO] + COLUNAS_PREDITIVAS
)


# ============================================================
# 2. CONFIGURACOES DOS EXPERIMENTOS
# ============================================================

CONFIGURACOES = [
    {
        "nome": "XGBoost - Baseline",
        "n_estimators": 150,
        "max_depth": 6,
        "learning_rate": 0.05,
    },
    {
        "nome": "XGBoost - Menor profundidade",
        "n_estimators": 150,
        "max_depth": 4,
        "learning_rate": 0.05,
    },
    {
        "nome": "XGBoost - Menor profundidade e taxa",
        "n_estimators": 200,
        "max_depth": 4,
        "learning_rate": 0.03,
    },
]


# ============================================================
# 3. CARREGAMENTO DOS DADOS
# ============================================================

print("\nCarregando base de dados...")

con = duckdb.connect()

df = con.execute(
    f"""
    SELECT {", ".join(COLUNAS_LEITURA)}
    FROM read_parquet('{CAMINHO_BASE}')
    """
).df()

con.close()

print(f"Base carregada: {len(df):,} registros.")


# ============================================================
# 4. DIVISAO DOS DADOS
# ============================================================

print("\nReproduzindo divisao original por municipio...")

grupos = df[GRUPO].to_numpy()
y = df[ALVO].astype("int8")
X = df[COLUNAS_PREDITIVAS]

# Primeira divisao: desenvolvimento (80%) e teste (20%)

divisor_teste = GroupShuffleSplit(
    n_splits=1,
    test_size=0.20,
    random_state=RANDOM_STATE,
)

idx_desenvolvimento, idx_teste = next(
    divisor_teste.split(X, y, groups=grupos)
)

X_desenvolvimento = X.iloc[idx_desenvolvimento]
y_desenvolvimento = y.iloc[idx_desenvolvimento]

grupos_desenvolvimento = grupos[idx_desenvolvimento]

# Segunda divisao: treinamento (80%) e validacao (20%)

divisor_validacao = GroupShuffleSplit(
    n_splits=1,
    test_size=0.20,
    random_state=RANDOM_STATE,
)

idx_treino, idx_validacao = next(
    divisor_validacao.split(
        X_desenvolvimento,
        y_desenvolvimento,
        groups=grupos_desenvolvimento,
    )
)

X_treino = X_desenvolvimento.iloc[idx_treino]
y_treino = y_desenvolvimento.iloc[idx_treino]

X_validacao = X_desenvolvimento.iloc[idx_validacao]
y_validacao = y_desenvolvimento.iloc[idx_validacao]

print(f"Treinamento: {len(X_treino):,}")
print(f"Validacao: {len(X_validacao):,}")
print(f"Teste reservado: {len(idx_teste):,}")

del df, X, y, grupos
del X_desenvolvimento, y_desenvolvimento
del grupos_desenvolvimento

gc.collect()


# ============================================================
# 5. PRE-PROCESSAMENTO
# ============================================================

print("\nAjustando pre-processador...")

X_treino_processado = preprocessador.fit_transform(X_treino)

X_validacao_processado = preprocessador.transform(X_validacao)

print("Pre-processamento concluido.")

del X_treino, X_validacao
gc.collect()


# ============================================================
# 6. EXPERIMENTOS DE OTIMIZACAO
# ============================================================

resultados = []

for configuracao in CONFIGURACOES:

    nome = configuracao["nome"]

    print("\n" + "=" * 65)
    print(f"EXPERIMENTO: {nome}")
    print("=" * 65)

    modelo = XGBClassifier(
        n_estimators=configuracao["n_estimators"],
        max_depth=configuracao["max_depth"],
        learning_rate=configuracao["learning_rate"],
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="logloss",
        tree_method="hist",
        n_jobs=2,
        random_state=RANDOM_STATE,
    )

    inicio = time.time()

    modelo.fit(
        X_treino_processado,
        y_treino,
    )

    tempo_treinamento = time.time() - inicio

    # Avaliacao no treinamento
    previsoes_treino = modelo.predict(X_treino_processado)

    # Avaliacao na validacao
    previsoes_validacao = modelo.predict(X_validacao_processado)

    probabilidades_validacao = modelo.predict_proba(
        X_validacao_processado
    )[:, 1]

    metricas = {
        "Modelo": nome,
        "n_estimators": configuracao["n_estimators"],
        "max_depth": configuracao["max_depth"],
        "learning_rate": configuracao["learning_rate"],
        "Tempo_treinamento_segundos": round(tempo_treinamento, 2),

        "F1_macro_treino": f1_score(
            y_treino,
            previsoes_treino,
            average="macro",
        ),

        "F1_macro_validacao": f1_score(
            y_validacao,
            previsoes_validacao,
            average="macro",
        ),

        "Acuracia_validacao": accuracy_score(
            y_validacao,
            previsoes_validacao,
        ),

        "Precisao_validacao": precision_score(
            y_validacao,
            previsoes_validacao,
            zero_division=0,
        ),

        "Recall_validacao": recall_score(
            y_validacao,
            previsoes_validacao,
            zero_division=0,
        ),

        "F1_validacao": f1_score(
            y_validacao,
            previsoes_validacao,
            zero_division=0,
        ),

        "ROC_AUC_validacao": roc_auc_score(
            y_validacao,
            probabilidades_validacao,
        ),

        "Balanced_Accuracy_validacao": balanced_accuracy_score(
            y_validacao,
            previsoes_validacao,
        ),
    }

    resultados.append(metricas)

    print(f"F1 macro treinamento: {metricas['F1_macro_treino']:.4f}")
    print(f"F1 macro validacao:   {metricas['F1_macro_validacao']:.4f}")
    print(f"ROC-AUC validacao:    {metricas['ROC_AUC_validacao']:.4f}")
    print(f"Tempo:                {tempo_treinamento:.2f} segundos")

    del modelo
    del previsoes_treino
    del previsoes_validacao
    del probabilidades_validacao

    gc.collect()


# ============================================================
# 7. COMPARACAO DOS RESULTADOS
# ============================================================

print("\n" + "=" * 90)
print("COMPARACAO DAS CONFIGURACOES XGBOOST")
print("=" * 90)

df_resultados = pd.DataFrame(resultados)

df_resultados = df_resultados.sort_values(
    by=["F1_macro_validacao", "ROC_AUC_validacao"],
    ascending=False,
)

print(
    df_resultados.to_string(
        index=False,
        formatters={
            coluna: "{:.4f}".format
            for coluna in [
                "F1_macro_treino",
                "F1_macro_validacao",
                "Acuracia_validacao",
                "Precisao_validacao",
                "Recall_validacao",
                "F1_validacao",
                "ROC_AUC_validacao",
                "Balanced_Accuracy_validacao",
            ]
        },
    )
)

df_resultados.to_csv(
    PASTA_RELATORIOS / "otimizacao_xgboost.csv",
    index=False,
)

melhor = df_resultados.iloc[0]

print("\nMELHOR CONFIGURACAO")

print(f"Modelo: {melhor['Modelo']}")
print(f"F1 macro: {melhor['F1_macro_validacao']:.4f}")
print(f"ROC-AUC: {melhor['ROC_AUC_validacao']:.4f}")

print("\nResultados salvos em:")
print("reports/otimizacao_xgboost.csv")

print("\nExperimentos finalizados.")
print("O conjunto de teste permaneceu reservado.")
