
import gc
from pathlib import Path

import duckdb
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

from scipy import sparse
from xgboost import XGBClassifier

from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    balanced_accuracy_score,
    confusion_matrix,
    classification_report,
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

PASTA_MODELOS = Path("models")
PASTA_RELATORIOS = Path("reports")
PASTA_IMAGENS = PASTA_RELATORIOS / "images"

for pasta in [PASTA_MODELOS, PASTA_RELATORIOS, PASTA_IMAGENS]:
    pasta.mkdir(parents=True, exist_ok=True)

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

print(f"Base carregada: {len(df):,} registros.")


# ============================================================
# 3. DIVISAO ENTRE DESENVOLVIMENTO E TESTE
# ============================================================

print("\nRealizando divisao por municipio...")

grupos = df[GRUPO].to_numpy()
y = df[ALVO].astype("int8")
X = df[COLUNAS_PREDITIVAS]

divisor = GroupShuffleSplit(
    n_splits=1,
    test_size=0.20,
    random_state=RANDOM_STATE,
)

idx_desenvolvimento, idx_teste = next(
    divisor.split(
        X,
        y,
        groups=grupos,
    )
)

X_desenvolvimento = X.iloc[idx_desenvolvimento].copy()
y_desenvolvimento = y.iloc[idx_desenvolvimento].copy()

X_teste = X.iloc[idx_teste].copy()
y_teste = y.iloc[idx_teste].copy()

grupos_desenvolvimento = set(grupos[idx_desenvolvimento])
grupos_teste = set(grupos[idx_teste])

assert grupos_desenvolvimento.isdisjoint(grupos_teste), (
    "Erro: existem municipios compartilhados entre desenvolvimento e teste."
)

print(f"Desenvolvimento: {len(X_desenvolvimento):,}")
print(f"Teste: {len(X_teste):,}")
print(f"Municipios no desenvolvimento: {len(grupos_desenvolvimento):,}")
print(f"Municipios no teste: {len(grupos_teste):,}")

print(f"Taxa positiva no desenvolvimento: {y_desenvolvimento.mean():.2%}")
print(f"Taxa positiva no teste: {y_teste.mean():.2%}")

del df, X, y, grupos
del grupos_desenvolvimento, grupos_teste

gc.collect()


# ============================================================
# 4. PRE-PROCESSAMENTO
# ============================================================

print("\nAjustando pre-processador...")

X_desenvolvimento_processado = preprocessador.fit_transform(
    X_desenvolvimento
)

nomes_features = preprocessador.get_feature_names_out()

print("Pre-processamento concluido.")
print(f"Total de features apos codificacao: {len(nomes_features)}")

# Liberando os dados brutos de desenvolvimento
del X_desenvolvimento
gc.collect()


# ============================================================
# 5. TREINAMENTO DO MODELO FINAL
# ============================================================

print("\nTreinando modelo XGBoost final...")

modelo_final = XGBClassifier(
    n_estimators=150,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="binary:logistic",
    eval_metric="logloss",
    tree_method="hist",
    n_jobs=2,
    random_state=RANDOM_STATE,
)

modelo_final.fit(
    X_desenvolvimento_processado,
    y_desenvolvimento,
)

print("Treinamento final concluido.")

del X_desenvolvimento_processado, y_desenvolvimento
gc.collect()


# ============================================================
# 6. AVALIACAO NO CONJUNTO DE TESTE
# ============================================================

print("\nAvaliando modelo no conjunto de teste...")

X_teste_processado = preprocessador.transform(X_teste)

previsoes = modelo_final.predict(X_teste_processado)

probabilidades = modelo_final.predict_proba(
    X_teste_processado
)[:, 1]

metricas = {
    "Modelo": "XGBoost",
    "Acuracia": accuracy_score(y_teste, previsoes),
    "Precisao": precision_score(
        y_teste, previsoes, zero_division=0
    ),
    "Recall": recall_score(
        y_teste, previsoes, zero_division=0
    ),
    "F1-score": f1_score(
        y_teste, previsoes, zero_division=0
    ),
    "F1 macro": f1_score(
        y_teste, previsoes, average="macro"
    ),
    "ROC-AUC": roc_auc_score(
        y_teste, probabilidades
    ),
    "Balanced Accuracy": balanced_accuracy_score(
        y_teste, previsoes
    ),
}

df_metricas = pd.DataFrame([metricas])

print("\nRESULTADOS FINAIS - TESTE")

for nome, valor in metricas.items():
    if nome != "Modelo":
        print(f"{nome:22}: {valor:.4f}")

df_metricas.to_csv(
    PASTA_RELATORIOS / "metricas_teste_xgboost.csv",
    index=False,
)


# ============================================================
# 7. RELATORIO E MATRIZ DE CONFUSAO
# ============================================================

print("\nRelatorio de classificacao:")

relatorio = classification_report(
    y_teste,
    previsoes,
    labels=[0, 1],
    target_names=["Nao alfabetizado", "Alfabetizado"],
    output_dict=True,
    zero_division=0,
)

df_relatorio = pd.DataFrame(relatorio).transpose()

print(df_relatorio)

df_relatorio.to_csv(
    PASTA_RELATORIOS / "relatorio_classificacao_xgboost.csv"
)

matriz = confusion_matrix(
    y_teste,
    previsoes,
    labels=[0, 1],
)

print("\nMatriz de confusao:")
print(matriz)

pd.DataFrame(
    matriz,
    index=["Real_nao_alfabetizado", "Real_alfabetizado"],
    columns=["Previsto_nao_alfabetizado", "Previsto_alfabetizado"],
).to_csv(
    PASTA_RELATORIOS / "matriz_confusao_xgboost.csv"
)

# Gráfico da matriz de confusão
fig, ax = plt.subplots(figsize=(7, 5))

imagem = ax.imshow(matriz)

ax.set_title("Matriz de Confusao - XGBoost")
ax.set_xlabel("Classe prevista")
ax.set_ylabel("Classe real")

ax.set_xticks([0, 1])
ax.set_yticks([0, 1])

ax.set_xticklabels(["Nao alfabetizado", "Alfabetizado"])
ax.set_yticklabels(["Nao alfabetizado", "Alfabetizado"])

for i in range(2):
    for j in range(2):
        ax.text(
            j,
            i,
            f"{matriz[i, j]:,}",
            ha="center",
            va="center",
        )

fig.colorbar(imagem, ax=ax)
fig.tight_layout()

fig.savefig(
    PASTA_IMAGENS / "matriz_confusao_xgboost.png",
    dpi=150,
)

plt.close(fig)

del X_teste_processado, previsoes, probabilidades
gc.collect()


# ============================================================
# 8. FEATURE IMPORTANCE
# ============================================================

print("\nGerando Feature Importance...")

importancias = modelo_final.feature_importances_

df_importancia = pd.DataFrame({
    "variavel": nomes_features,
    "importancia": importancias,
}).sort_values(
    "importancia",
    ascending=False,
)

df_importancia.to_csv(
    PASTA_RELATORIOS / "feature_importance_xgboost.csv",
    index=False,
)

top_importancias = df_importancia.head(20).sort_values(
    "importancia",
    ascending=True,
)

fig, ax = plt.subplots(figsize=(10, 8))

ax.barh(
    top_importancias["variavel"],
    top_importancias["importancia"],
)

ax.set_title("Top 20 - Feature Importance XGBoost")
ax.set_xlabel("Importancia")
ax.set_ylabel("Variaveis")

fig.tight_layout()

fig.savefig(
    PASTA_IMAGENS / "feature_importance_xgboost.png",
    dpi=150,
)

plt.close(fig)

print("Feature Importance salva.")


# ============================================================
# 9. EXPLICABILIDADE SHAP
# ============================================================

print("\nPreparando analise SHAP...")

# Amostra do conjunto de teste para reduzir consumo de memoria
TAMANHO_AMOSTRA_SHAP = min(500, len(X_teste))

X_shap_bruto = X_teste.sample(
    n=TAMANHO_AMOSTRA_SHAP,
    random_state=RANDOM_STATE,
)

X_shap_processado = preprocessador.transform(X_shap_bruto)

# SHAP trabalha com uma matriz densa nesta amostra reduzida
if sparse.issparse(X_shap_processado):
    X_shap_denso = X_shap_processado.toarray()
else:
    X_shap_denso = np.asarray(X_shap_processado)

X_shap_df = pd.DataFrame(
    X_shap_denso,
    columns=nomes_features,
)

print("Calculando valores SHAP...")

explainer = shap.TreeExplainer(modelo_final)

valores_shap = explainer(X_shap_df)

print("Valores SHAP calculados.")


# ============================================================
# 10. GRAFICO SHAP - BEESWARM
# ============================================================

print("\nGerando grafico SHAP Beeswarm...")

shap.plots.beeswarm(
    valores_shap,
    max_display=20,
    show=False,
)

plt.gcf().savefig(
    PASTA_IMAGENS / "shap_beeswarm_xgboost.png",
    dpi=150,
    bbox_inches="tight",
)

plt.close("all")


# ============================================================
# 11. GRAFICO SHAP - IMPORTANCIA GLOBAL
# ============================================================

print("Gerando grafico SHAP de importancia global...")

shap.plots.bar(
    valores_shap,
    max_display=20,
    show=False,
)

plt.gcf().savefig(
    PASTA_IMAGENS / "shap_importancia_global_xgboost.png",
    dpi=150,
    bbox_inches="tight",
)

plt.close("all")


# ============================================================
# 12. GRAFICO SHAP - WATERFALL
# ============================================================

print("Gerando grafico SHAP Waterfall...")

shap.plots.waterfall(
    valores_shap[0],
    max_display=15,
    show=False,
)

plt.gcf().savefig(
    PASTA_IMAGENS / "shap_waterfall_xgboost.png",
    dpi=150,
    bbox_inches="tight",
)

plt.close("all")


# ============================================================
# 13. SALVAMENTO DO MODELO
# ============================================================

print("\nSalvando modelo e pre-processador...")

joblib.dump(
    {
        "modelo": modelo_final,
        "preprocessador": preprocessador,
        "colunas_categoricas": COLUNAS_CATEGORICAS,
        "colunas_numericas": COLUNAS_NUMERICAS,
        "colunas_preditivas": COLUNAS_PREDITIVAS,
        "alvo": ALVO,
        "random_state": RANDOM_STATE,
    },
    PASTA_MODELOS / "modelo_xgboost_final.joblib",
)

print("Modelo salvo.")


# ============================================================
# 14. ENCERRAMENTO
# ============================================================

print("\n" + "=" * 65)
print("AVALIACAO FINAL CONCLUIDA")
print("=" * 65)

print("\nArquivos gerados:")

print("- models/modelo_xgboost_final.joblib")
print("- reports/metricas_teste_xgboost.csv")
print("- reports/relatorio_classificacao_xgboost.csv")
print("- reports/matriz_confusao_xgboost.csv")
print("- reports/feature_importance_xgboost.csv")

print("\nGraficos:")
print("- reports/images/matriz_confusao_xgboost.png")
print("- reports/images/feature_importance_xgboost.png")
print("- reports/images/shap_beeswarm_xgboost.png")
print("- reports/images/shap_importancia_global_xgboost.png")
print("- reports/images/shap_waterfall_xgboost.png")

print("\nProcesso finalizado com sucesso.")
