"""Segmentación de clientes A (R15 a R17, D-09 y D-31).

Cada cliente se describe por **cómo pagó** sus facturas emitidas de 2022-01 a 2025-06 con desenlace
conocido al 1/07/2025, igual que el entrenamiento de B. Lo que pasó después (2025-07 a 2026-09)
queda como desenlace externo para evaluar la segmentación en R17.
"""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from . import etiqueta as et
from . import muestra as mu
from .diseno import CORTE, DESDE, FECHA_CORTE

MIN_PAGADAS = 5   # D-09
K = 2             # D-32
N_INIT = 50       # reinicios de K-means: con 10, la solución dependía de la semilla (D-32)

VARIABLES = ["atraso_mediano", "atraso_iqr", "pct_tardias", "facturas_por_anio",
             "log_monto_mediano", "pct_varios_abonos", "pct_cierre_nota"]


def perfil(saldos: pd.DataFrame, movimientos: pd.DataFrame, min_pagadas: int = MIN_PAGADAS) -> pd.DataFrame:
    """Una fila por cliente (`nit_cliente`) con al menos `min_pagadas` facturas pagadas en la ventana.

    - Pagadas: cerradas con etiqueta (D-16 y D-20); de ellas salen el atraso y los abonos.
    - % de tardías: sobre todas las facturas con desenlace conocido al 1/07/2025 (cerradas con
      etiqueta y abiertas con más de 30 días vencidas).
    - % cerradas con notas o ajustes: sobre todas las cerradas de la ventana, con o sin RC.
    - Facturas por año: facturas emitidas en la ventana ÷ años entre su primera factura de la
      ventana y el 1/07/2025 (mínimo medio año).
    """
    def ventana(d):
        return d[(d.fecha >= DESDE) & (d.fecha < CORTE)]

    conocidas = ventana(mu.desenlace_conocido(saldos, movimientos, CORTE))
    conocidas = mu.agregar_log_monto_inicial(conocidas, movimientos)
    cerradas = ventana(et.facturas_cerradas(saldos))
    cerradas = cerradas[cerradas.fecha_cancelacion_registrada < CORTE]
    pagadas = cerradas.assign(atraso=et.atraso_etiqueta(cerradas, movimientos)).dropna(subset=["atraso"])
    emitidas = ventana(saldos[saldos.es_deuda_facturada & (saldos.plazo_dias_observado >= 0)])

    g_pag = pagadas.groupby("nit_cliente")
    anios = ((CORTE - emitidas.groupby("nit_cliente").fecha.min()).dt.days / 365.25).clip(lower=0.5)
    p = pd.DataFrame({
        "n_pagadas": g_pag.size(),
        "atraso_mediano": g_pag.atraso.median(),
        "atraso_iqr": g_pag.atraso.quantile(0.75) - g_pag.atraso.quantile(0.25),
        "pct_tardias": conocidas.groupby("nit_cliente").tardia.mean() * 100,
        "facturas_por_anio": emitidas.groupby("nit_cliente").size() / anios,
        "log_monto_mediano": conocidas.groupby("nit_cliente").log_monto_inicial.median(),
        "pct_varios_abonos": g_pag.num_recaudos_rc.apply(lambda s: (s > 1).mean() * 100),
        "pct_cierre_nota": cerradas.groupby("nit_cliente").tipo_documento_cierre.apply(lambda s: (s != "RC").mean() * 100),
    })
    return p[p.n_pagadas >= min_pagadas].dropna(subset=VARIABLES).sort_index()


def desenlace_posterior(saldos: pd.DataFrame, movimientos: pd.DataFrame) -> pd.DataFrame:
    """Facturas de cada cliente emitidas desde el 1/07/2025 con desenlace conocido al 18/10/2026.

    Columnas: `facturas`, `tardias`. Es el desenlace externo de R17: no se usa para formar los
    grupos.
    """
    d = mu.desenlace_conocido(saldos, movimientos, FECHA_CORTE)
    d = d[d.fecha >= CORTE]
    return d.groupby("nit_cliente").tardia.agg(facturas="size", tardias="sum")


class Recorte(BaseEstimator, TransformerMixin):
    """Recorta cada columna a sus percentiles 1 y 99, aprendidos solo con el entrenamiento."""

    def __init__(self, inferior=1, superior=99):
        self.inferior, self.superior = inferior, superior

    def fit(self, X, y=None):
        X = np.asarray(X, dtype=float)
        self.lim_inf_ = np.percentile(X, self.inferior, axis=0)
        self.lim_sup_ = np.percentile(X, self.superior, axis=0)
        return self

    def transform(self, X):
        return np.clip(np.asarray(X, dtype=float), self.lim_inf_, self.lim_sup_)


def particion(p: pd.DataFrame, semilla: int):
    """Clientes al azar: 70 % entrenamiento y 30 % prueba (D-31). Devuelve (entrenamiento, prueba)."""
    from sklearn.model_selection import train_test_split
    return train_test_split(p, test_size=0.3, random_state=semilla)


def preparacion() -> Pipeline:
    """Recorte de extremos y escala estándar (D-31)."""
    return Pipeline([("recorte", Recorte()), ("escala", StandardScaler())])
