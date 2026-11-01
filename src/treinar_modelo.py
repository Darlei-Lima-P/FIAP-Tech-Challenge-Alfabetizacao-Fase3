
import gc
import duckdb
import pandas as pd

from xgboost import XGBClassifier

from sklearn.model_selection import GroupShuffleSplit
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    balanced_accuracy_score,
    confusion_matrix
)

from preprocessamento import (
    preprocessador,
    COLUNAS_CATEGORICAS,
    COLUNAS_NUMERICAS
)


# ============================================================
# 1. CONFIGURACOES
# ============================================================

CAMINHO_BASE = "data/gold/fase3/base_modelagem.parquet"

ALVO = "fl_alfabetizado"
GRUPO = "id_municipio"

RANDOM_STATE = 42

COLUNAS_PREDITIVAS = (
    COLUNAS_CATEGORICAS + COLUNAS_NUMERICAS
)

COLUNAS_LEITURA = (
    [GRUPO, ALVO] + COLUNAS_PREDITIVAS
)


# ============================================================
# 2. CARREGAMENTO DOS DADOS
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

print("Base carregada.")
print(f"Total de registros: {len(df):,}")


# ============================================================
# 3. DIVISAO DOS DADOS POR MUNICIPIO
# ============================================================

print("\nRealizando divisao dos dados...")

grupos = df[GRUPO].to_numpy()
y = df[ALVO].astype("int8")
X = df[COLUNAS_PREDITIVAS]

# Primeira divisao: desenvolvimento (80%) e teste (20%)

divisor_teste = GroupShuffleSplit(
    n_splits=1,
    test_size=0.20,
    random_state=RANDOM_STATE
)

idx_desenvolvimento, idx_teste = next(
    divisor_teste.split(
        X,
        y,
        groups=grupos
    )
)

X_desenvolvimento = X.iloc[idx_desenvolvimento]
y_desenvolvimento = y.iloc[idx_desenvolvimento]

grupos_desenvolvimento = grupos[idx_desenvolvimento]


# Segunda divisao: treinamento (80%) e validacao (20%)

divisor_validacao = GroupShuffleSplit(
    n_splits=1,
    test_size=0.20,
    random_state=RANDOM_STATE
)

idx_treino, idx_validacao = next(
    divisor_validacao.split(
        X_desenvolvimento,
        y_desenvolvimento,
        groups=grupos_desenvolvimento
    )
)

X_treino = X_desenvolvimento.iloc[idx_treino]
y_treino = y_desenvolvimento.iloc[idx_treino]

X_validacao = X_desenvolvimento.iloc[idx_validacao]
y_validacao = y_desenvolvimento.iloc[idx_validacao]


# Liberando memoria

del df, X, y, grupos
del X_desenvolvimento, y_desenvolvimento
del grupos_desenvolvimento

gc.collect()


print("\nDADOS PREPARADOS")

print(f"Treinamento: {len(X_treino):,}")
print(f"Validacao: {len(X_validacao):,}")

print(
    f"Taxa positiva no treinamento: "
    f"{y_treino.mean():.2%}"
)

print(
    f"Taxa positiva na validacao: "
    f"{y_validacao.mean():.2%}"
)


# ============================================================
# 4. PRE-PROCESSAMENTO
# ============================================================

print("\nAjustando pre-processador...")

X_treino_processado = preprocessador.fit_transform(
    X_treino
)

X_validacao_processado = preprocessador.transform(
    X_validacao
)

print("Pre-processamento concluido.")

del X_treino, X_validacao

gc.collect()


# ============================================================
# 5. FUNCAO DE AVALIACAO DOS MODELOS
# ============================================================

resultados = []


def avaliar_modelo(nome, modelo):

    print("\n" + "=" * 65)
    print(f"INICIANDO: {nome}")
    print("=" * 65)

    modelo.fit(
        X_treino_processado,
        y_treino
    )

    print("Treinamento concluido.")
    print("Gerando previsoes na validacao...")

    previsoes = modelo.predict(
        X_validacao_processado
    )

    probabilidades = modelo.predict_proba(
        X_validacao_processado
    )[:, 1]

    metricas = {
        "Modelo": nome,

        "Acuracia": accuracy_score(
            y_validacao,
            previsoes
        ),

        "Precisao": precision_score(
            y_validacao,
            previsoes,
            zero_division=0
        ),

        "Recall": recall_score(
            y_validacao,
            previsoes,
            zero_division=0
        ),

        "F1-score": f1_score(
            y_validacao,
            previsoes,
            zero_division=0
        ),

        "F1 macro": f1_score(
            y_validacao,
            previsoes,
            average="macro"
        ),

        "ROC-AUC": roc_auc_score(
            y_validacao,
            probabilidades
        ),

        "Balanced Accuracy": balanced_accuracy_score(
            y_validacao,
            previsoes
        )
    }

    resultados.append(metricas)

    print("\nRESULTADOS NA VALIDACAO")

    for nome_metrica, valor in metricas.items():

        if nome_metrica != "Modelo":
            print(f"{nome_metrica:22}: {valor:.4f}")

    print("\nMATRIZ DE CONFUSAO")

    print(
        confusion_matrix(
            y_validacao,
            previsoes
        )
    )

    del modelo
    del previsoes
    del probabilidades

    gc.collect()


# ============================================================
# 6. EXPERIMENTO 1 - REGRESSAO LOGISTICA
# ============================================================

modelo_logistico = LogisticRegression(
    solver="saga",
    max_iter=100,
    tol=1e-3,
    random_state=RANDOM_STATE
)

avaliar_modelo(
    "Regressao Logistica",
    modelo_logistico
)


# ============================================================
# 7. EXPERIMENTO 2 - RANDOM FOREST SEM BALANCEAMENTO
# ============================================================

modelo_rf = RandomForestClassifier(
    n_estimators=100,
    max_depth=12,
    min_samples_leaf=20,
    class_weight=None,
    random_state=RANDOM_STATE,
    n_jobs=1
)

avaliar_modelo(
    "Random Forest sem balanceamento",
    modelo_rf
)


# ============================================================
# 8. EXPERIMENTO 3 - RANDOM FOREST BALANCEADO
# ============================================================

modelo_rf_balanceado = RandomForestClassifier(
    n_estimators=100,
    max_depth=12,
    min_samples_leaf=20,
    class_weight="balanced",
    random_state=RANDOM_STATE,
    n_jobs=1
)

avaliar_modelo(
    "Random Forest balanceado",
    modelo_rf_balanceado
)


# ============================================================
# 9. EXPERIMENTO 4 - XGBOOST
# ============================================================

modelo_xgb = XGBClassifier(
    n_estimators=150,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="binary:logistic",
    eval_metric="logloss",
    tree_method="hist",
    n_jobs=2,
    random_state=RANDOM_STATE
)

avaliar_modelo(
    "XGBoost",
    modelo_xgb
)


# ============================================================
# 10. COMPARACAO FINAL
# ============================================================

print("\n")

print("=" * 90)
print("COMPARACAO FINAL DOS MODELOS")
print("=" * 90)

df_resultados = pd.DataFrame(resultados)

colunas_metricas = [
    "Acuracia",
    "Precisao",
    "Recall",
    "F1-score",
    "F1 macro",
    "ROC-AUC",
    "Balanced Accuracy"
]

print(
    df_resultados.to_string(
        index=False,
        formatters={
            coluna: "{:.4f}".format
            for coluna in colunas_metricas
        }
    )
)


# ============================================================
# 11. ENCERRAMENTO
# ============================================================

print("\nExperimentos finalizados.")

print(
    "Todos os modelos utilizaram "
    "os dados completos de treinamento."
)

print(
    "O conjunto de teste permaneceu reservado."
)
