"""Etiqueta de pago tardío del componente B.

Regla: el atraso se mide hasta que entra el dinero a la caja, no hasta que el saldo queda en cero.

- Cierre con RC: el último documento que acreditó la factura es un recibo de caja. El atraso va
  hasta `fecha_cancelacion_registrada`.
- Mixta: la cerró una nota o un ajuste, pero antes el cliente pagó con al menos un RC. El atraso
  va hasta el último RC (`fecha_ultimo_recaudo`).
- Sin RC: la cerró una nota o un ajuste y nunca hubo RC. No describe un pago: queda fuera de la
  etiqueta de B (atraso nulo).
- Mixta con poco RC: si los RC cubren menos del 90 % del valor de la factura, la mayor
  parte se cerró sin dinero, como en las sin RC. También queda fuera de la etiqueta de B.

Pago tardío = atraso mayor que 30 días. La etiqueta de B se arma con `atraso_etiqueta`.

Este módulo no aplica la regla de desenlace conocido ni excluye por fecha de corte: recibe
facturas ya cerradas.
"""

import pandas as pd

UMBRAL_ATRASO = 30
COBERTURA_MIN_RC = 0.9  # parte mínima del valor pagada con RC para que una mixta tenga etiqueta

CIERRE_RC = "RC"
CIERRE_MIXTA = "mixta"
CIERRE_SIN_RC = "sin RC"


def facturas_cerradas(saldos: pd.DataFrame) -> pd.DataFrame:
    """Facturas cerradas con atraso medible.

    Factura (`es_deuda_facturada`), saldo en cero (`SIN_SALDO`), plazo no negativo (un plazo
    negativo es un error de registro) y con `fecha_cancelacion_registrada`.
    """
    return saldos[
        saldos.es_deuda_facturada
        & (saldos.estado_vencimiento_actual == "SIN_SALDO")
        & (saldos.plazo_dias_observado >= 0)
        & saldos.fecha_cancelacion_registrada.notna()
    ].copy()


def tipo_cierre(cerradas: pd.DataFrame) -> pd.Series:
    """Clasifica cada factura cerrada en «RC», «mixta» o «sin RC»."""
    con_rc = cerradas.num_recaudos_rc > 0
    cierre_rc = cerradas.tipo_documento_cierre == "RC"
    tipo = pd.Series(CIERRE_SIN_RC, index=cerradas.index)
    tipo[~cierre_rc & con_rc] = CIERRE_MIXTA
    tipo[cierre_rc] = CIERRE_RC
    return tipo


def cobertura_rc(cerradas: pd.DataFrame, movimientos: pd.DataFrame) -> pd.Series:
    """Fracción del valor de la factura (`total_debitos`) que se pagó con RC (0 si no hubo RC)."""
    pagado_rc = movimientos[movimientos.es_recaudo].groupby("id_saldo").credito.sum()
    return (cerradas.id_saldo.map(pagado_rc).fillna(0) / cerradas.total_debitos).rename("cobertura_rc")


def atraso_hasta_cancelacion(cerradas: pd.DataFrame) -> pd.Series:
    """Atraso hasta que el saldo quedó en cero, sin la regla del RC (definición anterior, sin la regla del RC)."""
    return (cerradas.fecha_cancelacion_registrada.dt.normalize()
            - cerradas.fecha_vencimiento.dt.normalize()).dt.days


def atraso_d16(cerradas: pd.DataFrame) -> pd.Series:
    """Atraso hasta el último RC, en días. Nulo para los cierres sin RC."""
    tipo = tipo_cierre(cerradas)
    fin = cerradas.fecha_cancelacion_registrada.where(tipo == CIERRE_RC,
                                                      cerradas.fecha_ultimo_recaudo)
    fin = fin.where(tipo != CIERRE_SIN_RC)
    return (fin.dt.normalize() - cerradas.fecha_vencimiento.dt.normalize()).dt.days


def atraso_etiqueta(cerradas: pd.DataFrame, movimientos: pd.DataFrame,
                    cobertura_min: float = COBERTURA_MIN_RC) -> pd.Series:
    """Atraso con el que se etiqueta B, en días.

    Igual que `atraso_d16`, pero también es nulo en las mixtas cuyos RC cubren menos de
    `cobertura_min` del valor. El parámetro existe para la prueba de sensibilidad del umbral.
    """
    atraso = atraso_d16(cerradas)
    poco_rc = (tipo_cierre(cerradas) == CIERRE_MIXTA) & (cobertura_rc(cerradas, movimientos) < cobertura_min)
    return atraso.where(~poco_rc)


def pago_tardio(atraso: pd.Series) -> pd.Series:
    """1 si el atraso supera 30 días, 0 si no; nulo donde el atraso es nulo."""
    return (atraso > UMBRAL_ATRASO).astype("Int64").where(atraso.notna())
