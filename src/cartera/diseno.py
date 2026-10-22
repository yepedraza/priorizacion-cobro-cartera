"""Diseño experimental de B: partición, variables y preparación (R12, D-18, D-23 y D-24).

Lo usan R12, R13 y lo que sigue, para que todos vean exactamente la misma partición y las mismas
columnas.
"""

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from . import etiqueta as et
from . import historial as hi
from . import muestra as mu

FECHA_CORTE = pd.Timestamp("2026-10-18")   # corte de los datos
CORTE = pd.Timestamp("2025-07-01")         # entrenamiento | prueba (D-23)
CORTE_VAL = pd.Timestamp("2024-07-01")     # subentrenamiento | validación (D-23)
DESDE = pd.Timestamp("2022-01-01")         # periodo de estudio (anteproyecto §7.3)
BLOQUE = "Q"                               # trimestre de emisión (D-23)

# Predictoras (D-24, sin `empresa` desde D-27: el grupo se trata como una sola empresa)
NUM = mu.NUM_PROVISIONALES + hi.VARIABLES_HISTORIAL
CAT = ["unidad_negocio", "tipo_cliente"]


def _conocidas_a(saldos, movimientos, fecha):
    d = mu.desenlace_conocido(saldos, movimientos, fecha)
    return d[d.fecha >= DESDE]


def conjuntos(saldos: pd.DataFrame, movimientos: pd.DataFrame) -> dict:
    """Subentrenamiento, validación, entrenamiento completo y prueba, con sus predictoras.

    En cada conjunto solo entran facturas cuyo desenlace ya se conocía en la fecha en que termina
    (D-17): `vencimiento + 30 ≤` 2024-07-01, 2025-07-01, 2025-07-01 y 2026-10-18.
    """
    hasta_corte = _conocidas_a(saldos, movimientos, CORTE)
    sub = _conocidas_a(saldos, movimientos, CORTE_VAL)
    salida = {
        "subentrenamiento": sub[sub.fecha < CORTE_VAL],
        "validación": hasta_corte[(hasta_corte.fecha >= CORTE_VAL) & (hasta_corte.fecha < CORTE)],
        "entrenamiento completo": hasta_corte[hasta_corte.fecha < CORTE],
    }
    prueba = _conocidas_a(saldos, movimientos, FECHA_CORTE)
    salida["prueba"] = prueba[prueba.fecha >= CORTE]

    def preparar(d):
        d = mu.agregar_log_monto_inicial(d, movimientos)
        return d.join(hi.calcular(d, saldos, movimientos))

    return {nombre: preparar(d) for nombre, d in salida.items()}


def pliegues(ent: pd.DataFrame, n: int = 5) -> list:
    """CV agrupada por trimestre, de ventana creciente (D-18, D-26).

    Cada pliegue valida uno de los últimos `n` trimestres de `ent` y entrena con los trimestres
    anteriores, solo con facturas cuyo `vencimiento + 30` cae antes de que empiece el trimestre
    validado (D-17 en cada corte). Devuelve posiciones (no etiquetas de índice), como espera
    scikit-learn.
    """
    trimestre = ent.fecha.dt.to_period(BLOQUE).to_numpy()
    orden = sorted(set(trimestre))
    resultado = []
    for b in orden[-n:]:
        inicio = b.start_time
        en_val = trimestre == b
        en_ent = (trimestre < b) & (ent.fecha_vencimiento + pd.Timedelta(days=et.UMBRAL_ATRASO) <= inicio).to_numpy()
        resultado.append((en_ent.nonzero()[0], en_val.nonzero()[0]))
    return resultado


def prep_lineal(num=None, cat=None) -> ColumnTransformer:
    """Imputa (mediana, con indicador de faltante), escala y codifica: para logística, SVM, KNN."""
    num, cat = num or NUM, cat or CAT
    return ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median", add_indicator=True)),
                          ("esc", StandardScaler())]), num),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
    ])


def prep_arbol(num=None, cat=None) -> ColumnTransformer:
    """Sin escalar ni imputar (los árboles manejan el faltante): para árboles y ensambles."""
    num, cat = num or NUM, cat or CAT
    return ColumnTransformer([
        ("num", "passthrough", num),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat),
    ], verbose_feature_names_out=False)
