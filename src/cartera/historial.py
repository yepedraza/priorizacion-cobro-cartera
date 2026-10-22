"""Historial del cliente el día en que se emite cada factura (D-11 y D-24).

Cada variable usa solo hechos ocurridos **antes** del día de emisión *t* (estrictamente antes: lo
del mismo día no cuenta), para que el modelo vea lo mismo que vería el día que se emite la factura.

| Variable | Qué es, el día *t* |
|---|---|
| `atraso_prom_hist` | Atraso promedio (D-16 y D-20) de las facturas del cliente canceladas antes de *t*. Nulo si no hay ninguna |
| `n_pagadas_hist` | Cuántas de esas facturas hay. 0 = cliente sin historial de pago |
| `saldo_abierto_t` | Saldo del cliente en facturas, sumando los movimientos anteriores a *t* |
| `n_abiertas_t` | Facturas del cliente emitidas antes de *t* que no estaban canceladas antes de *t* |
| `n_vencidas_t` | De esas, cuántas ya habían vencido antes de *t* |
| `antiguedad_dias` | Días entre la primera factura del cliente y *t*. 0 si es su primera |

Una factura sin fecha de cancelación se trata como no cancelada.
"""

import numpy as np
import pandas as pd

from . import etiqueta as et

VARIABLES_HISTORIAL = ["atraso_prom_hist", "n_pagadas_hist", "saldo_abierto_t",
                       "n_abiertas_t", "n_vencidas_t", "antiguedad_dias"]


def _dia(serie: pd.Series) -> np.ndarray:
    return serie.dt.normalize().to_numpy()


def _contar_antes(ordenadas: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Cuántos valores de `ordenadas` (ya ordenadas) son estrictamente anteriores a cada t."""
    return np.searchsorted(ordenadas, t, side="left")


def calcular(objetivo: pd.DataFrame, saldos: pd.DataFrame, movimientos: pd.DataFrame) -> pd.DataFrame:
    """Variables de historial para cada fila de `objetivo` (necesita `nit_cliente` y `fecha`).

    Devuelve un DataFrame con el mismo índice que `objetivo` y las columnas de
    `VARIABLES_HISTORIAL`.
    """
    facturas = saldos[saldos.es_deuda_facturada & (saldos.plazo_dias_observado >= 0)]

    pagadas = et.facturas_cerradas(saldos)
    pagadas = pagadas.assign(atraso=et.atraso_etiqueta(pagadas, movimientos)).dropna(subset=["atraso"])

    movs = movimientos[movimientos.id_saldo.isin(facturas.id_saldo)]
    movs = movs.assign(delta=movs.debito - movs.credito)

    salida = pd.DataFrame(index=objetivo.index, columns=VARIABLES_HISTORIAL, dtype=float)
    grupos_fac = facturas.groupby("nit_cliente")
    grupos_pag = pagadas.groupby("nit_cliente")
    grupos_mov = movs.groupby("nit_cliente")

    for cliente, obj in objetivo.groupby("nit_cliente"):
        t = _dia(obj.fecha)

        # Atraso promedio y número de facturas canceladas antes de t
        if cliente in grupos_pag.groups:
            p = grupos_pag.get_group(cliente).sort_values("fecha_cancelacion_registrada")
            k = _contar_antes(_dia(p.fecha_cancelacion_registrada), t)
            suma = np.concatenate([[0.0], np.cumsum(p.atraso.to_numpy(dtype=float))])[k]
            n_pag = k
            atraso_prom = np.where(k > 0, suma / np.maximum(k, 1), np.nan)
        else:
            n_pag = np.zeros(len(t), dtype=int)
            atraso_prom = np.full(len(t), np.nan)

        # Saldo abierto: suma de débitos menos créditos de los movimientos anteriores a t
        if cliente in grupos_mov.groups:
            m = grupos_mov.get_group(cliente).sort_values("fecha_movimiento")
            k = _contar_antes(_dia(m.fecha_movimiento), t)
            saldo = np.concatenate([[0.0], np.cumsum(m.delta.to_numpy(dtype=float))])[k]
        else:
            saldo = np.zeros(len(t))

        # Facturas abiertas y vencidas el día t
        f = grupos_fac.get_group(cliente) if cliente in grupos_fac.groups else facturas.iloc[0:0]
        emision = np.sort(_dia(f.fecha))
        cancel = f.fecha_cancelacion_registrada.dropna()
        vence = np.sort(_dia(f.fecha_vencimiento))
        # Una factura vencida que también se canceló antes de t no está vencida abierta
        f_c = f[f.fecha_cancelacion_registrada.notna()]
        vence_y_cancelada = np.sort(np.maximum(_dia(f_c.fecha_vencimiento), _dia(f_c.fecha_cancelacion_registrada)))
        n_abiertas = _contar_antes(emision, t) - _contar_antes(np.sort(_dia(cancel)), t)
        n_vencidas = _contar_antes(vence, t) - _contar_antes(vence_y_cancelada, t)

        primera = emision[0] if len(emision) else None
        antiguedad = (np.zeros(len(t)) if primera is None
                      else np.maximum((t - primera) / np.timedelta64(1, "D"), 0))

        salida.loc[obj.index] = np.column_stack(
            [atraso_prom, n_pag, saldo, n_abiertas, n_vencidas, antiguedad])

    return salida.astype(float)


def calcular_fuerza_bruta(fila: pd.Series, saldos: pd.DataFrame, movimientos: pd.DataFrame,
                          pagadas: pd.DataFrame) -> dict:
    """Recalcula el historial de una sola factura filtrando explícitamente por fecha.

    Es la prueba de D-11: usa solo filas cuya fecha es anterior a la emisión, escrito de la forma
    más directa posible, para compararlo con `calcular`. `pagadas` son las cerradas con su
    columna `atraso` (etiqueta D-16 y D-20).
    """
    t = fila.fecha.normalize()
    cliente = fila.nit_cliente
    facturas = saldos[saldos.es_deuda_facturada & (saldos.plazo_dias_observado >= 0)
                      & (saldos.nit_cliente == cliente)]

    previas = pagadas[(pagadas.nit_cliente == cliente)
                      & (pagadas.fecha_cancelacion_registrada.dt.normalize() < t)]
    movs = movimientos[movimientos.id_saldo.isin(facturas.id_saldo)
                       & (movimientos.fecha_movimiento.dt.normalize() < t)]
    emitidas = facturas[facturas.fecha.dt.normalize() < t]
    cancelada_antes = emitidas.fecha_cancelacion_registrada.dt.normalize() < t
    abiertas = emitidas[~cancelada_antes.fillna(False)]
    primera = facturas.fecha.dt.normalize().min()

    return {
        "atraso_prom_hist": previas.atraso.mean() if len(previas) else np.nan,
        "n_pagadas_hist": float(len(previas)),
        "saldo_abierto_t": float((movs.debito - movs.credito).sum()),
        "n_abiertas_t": float(len(abiertas)),
        "n_vencidas_t": float((abiertas.fecha_vencimiento.dt.normalize() < t).sum()),
        "antiguedad_dias": float(max((t - primera).days, 0)) if pd.notna(primera) else 0.0,
    }
