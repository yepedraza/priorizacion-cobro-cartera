"""Facturas con desenlace conocido y variables provisionales (R10 y R11).

Es la muestra de los primeros modelos de referencia. R12 fija la partición y las variables
definitivas; mientras tanto, R10 y R11 usan esta misma función para no copiar código.
"""

import numpy as np
import pandas as pd

from . import etiqueta as et

TOL = 0.01  # saldos entre -0,01 y 0,01 se consideran en cero

# Variables que se conocen al emitir la factura (provisionales hasta R12)
NUM_PROVISIONALES = ["plazo_dias_observado", "log_monto_inicial", "fecha_mes"]
CAT_PROVISIONALES = ["empresa", "unidad_negocio"]


def desenlace_conocido(saldos: pd.DataFrame, movimientos: pd.DataFrame,
                       fecha_corte: pd.Timestamp) -> pd.DataFrame:
    """Facturas cuyo desenlace se conoce a `fecha_corte` (D-17), con la columna `tardia` (0/1).

    - Cerradas: etiqueta de D-16 y D-20; las sin RC y las mixtas con poco RC quedan fuera.
    - Abiertas que ya llevan más de 30 días vencidas: tardia = 1.
    - Solo facturas con `fecha_vencimiento + 30 ≤ fecha_corte`.
    """
    cerradas = et.facturas_cerradas(saldos)
    cerradas["tardia"] = et.pago_tardio(et.atraso_etiqueta(cerradas, movimientos))
    cerradas = cerradas[cerradas.tardia.notna()]

    facturas = saldos[saldos.es_deuda_facturada & (saldos.plazo_dias_observado >= 0)]
    abiertas = facturas[facturas.saldo_neto_actual > TOL].copy()
    abiertas["tardia"] = 1

    muestra = pd.concat([cerradas, abiertas])
    vencio_hace_30 = muestra.fecha_vencimiento + pd.Timedelta(days=et.UMBRAL_ATRASO) <= fecha_corte
    muestra = muestra[vencio_hace_30].copy()
    muestra["tardia"] = muestra.tardia.astype(int)
    return muestra


def agregar_log_monto_inicial(muestra: pd.DataFrame, movimientos: pd.DataFrame) -> pd.DataFrame:
    """Agrega `log_monto_inicial`: logaritmo del débito del primer movimiento de cada factura.

    Se usa el débito inicial y no `total_debitos`, que es un acumulado y puede crecer después de
    la emisión.
    """
    inicial = movimientos[movimientos.orden_movimiento == 1].set_index("id_saldo").debito
    muestra = muestra.copy()
    muestra["log_monto_inicial"] = np.log1p(muestra.id_saldo.map(inicial).clip(lower=0))
    return muestra
