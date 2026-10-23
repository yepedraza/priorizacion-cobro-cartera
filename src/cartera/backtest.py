"""Backtest de la lista diaria (diseno_experimental.md §7; D-07, D-15, D-17, D-19 y D-29).

Para cada día hábil *t* se reconstruye la cartera de facturas abiertas, con su saldo calculado con
los movimientos anteriores a *t*, y se arman tres listas de K clientes:

- **Regla actual (D-07):** mayor saldo vencido.
- **Segunda línea base (D-19):** mayor saldo en facturas de 1 a 30 días de mora.
- **Modelo (D-29):** entre los clientes con alguna factura vencida, mayor suma de
  probabilidad × saldo en sus facturas con dinero en duda.

**Dinero en duda (D-15):** facturas no vencidas o vencidas hace 30 días o menos el día *t*. La
métrica principal es qué parte del dinero en duda que terminó tardío estaba en la lista.
"""

import numpy as np
import pandas as pd

from . import muestra as mu

TOL = mu.TOL
LISTAS = ["regla actual (D-07)", "saldo de 1 a 30 días (D-19)", "modelo"]


def desenlace_final(saldos: pd.DataFrame, movimientos: pd.DataFrame, fecha_corte: pd.Timestamp) -> pd.Series:
    """`tardia` final de cada factura (1/0), indexada por `id_saldo`.

    Las facturas que no aparecen tienen desenlace desconocido a `fecha_corte` o quedaron sin
    etiqueta (cierres sin pago, D-16 y D-20).
    """
    d = mu.desenlace_conocido(saldos, movimientos, fecha_corte)
    return d.set_index("id_saldo").tardia


class Cartera:
    """Reconstruye la cartera de facturas abiertas en cualquier día pasado."""

    def __init__(self, saldos: pd.DataFrame, movimientos: pd.DataFrame):
        fac = saldos[saldos.es_deuda_facturada & (saldos.plazo_dias_observado >= 0)]
        self.fac = fac[["id_saldo", "nit_cliente", "fecha", "fecha_vencimiento"]].reset_index(drop=True)
        self._emision = self.fac.fecha.dt.normalize().to_numpy()
        self._vence = self.fac.fecha_vencimiento.dt.normalize().to_numpy()
        codigo = pd.Series(np.arange(len(self.fac)), index=self.fac.id_saldo)
        m = movimientos[movimientos.id_saldo.isin(self.fac.id_saldo)].sort_values("fecha_movimiento")
        self._m_fecha = m.fecha_movimiento.dt.normalize().to_numpy()
        self._m_codigo = codigo.loc[m.id_saldo].to_numpy()
        self._m_delta = (m.debito - m.credito).to_numpy(dtype=float)

    def dia(self, t: pd.Timestamp) -> pd.DataFrame:
        """Facturas emitidas antes de *t* con saldo mayor que 0,01 según los movimientos anteriores a *t*.

        Columnas: `id_saldo`, `nit_cliente`, `saldo`, `mora` (días desde el vencimiento; ≤ 0 si
        aún no vence).
        """
        t = np.datetime64(pd.Timestamp(t).normalize())
        k = np.searchsorted(self._m_fecha, t, side="left")
        saldo = np.bincount(self._m_codigo[:k], weights=self._m_delta[:k], minlength=len(self.fac))
        abierta = (self._emision < t) & (saldo > TOL)
        mora = ((t - self._vence[abierta]) / np.timedelta64(1, "D")).astype(int)
        return pd.DataFrame({"id_saldo": self.fac.id_saldo.to_numpy()[abierta],
                             "nit_cliente": self.fac.nit_cliente.to_numpy()[abierta],
                             "saldo": saldo[abierta], "mora": mora})


def listas_del_dia(cartera_t: pd.DataFrame, probabilidad: pd.Series, k: int) -> dict:
    """Los K clientes de cada lista para un día."""
    vencidas = cartera_t[cartera_t.mora >= 1]
    candidatos = vencidas.nit_cliente.unique()
    duda = cartera_t[cartera_t.mora <= 30]
    riesgo = (duda.saldo * duda.id_saldo.map(probabilidad).to_numpy()).groupby(duda.nit_cliente.to_numpy()).sum()
    riesgo = riesgo.reindex(candidatos).fillna(0)
    return {
        LISTAS[0]: set(vencidas.groupby("nit_cliente").saldo.sum().nlargest(k).index),
        LISTAS[1]: set(vencidas[vencidas.mora <= 30].groupby("nit_cliente").saldo.sum().nlargest(k).index),
        LISTAS[2]: set(riesgo.nlargest(k).index),
    }


def simular(cartera: Cartera, dias, probabilidad: pd.Series, final: pd.Series,
            ks=(10, 20, 40)) -> pd.DataFrame:
    """Una fila por día, cupo y lista, con los montos que hacen falta para las métricas.

    `probabilidad`: probabilidad de pago tardío por `id_saldo` (calculada al emitir la factura).
    `final`: desenlace final por `id_saldo` (ver `desenlace_final`).
    """
    filas = []
    for t in dias:
        c = cartera.dia(t)
        y = c.id_saldo.map(final)
        duda = c.mora <= 30
        tardia = y == 1
        base = {
            "dia": t,
            "duda_total": c.saldo[duda].sum(),
            "duda_desconocido": c.saldo[duda & y.isna()].sum(),
            "riesgo": c.saldo[duda & tardia].sum(),              # dinero en duda que terminó tardío
            "tardio_todo": c.saldo[tardia].sum(),                # todo el dinero abierto que terminó tardío
        }
        for k in ks:
            for nombre, clientes in listas_del_dia(c, probabilidad, k).items():
                en_lista = c.nit_cliente.isin(clientes)
                filas.append({**base, "k": k, "lista": nombre,
                              "capturado": c.saldo[duda & tardia & en_lista].sum(),
                              "capturado_todo": c.saldo[tardia & en_lista].sum(),
                              "ya_tardio_en_lista": c.saldo[(c.mora > 30) & en_lista].sum(),
                              "saldo_en_lista": c.saldo[en_lista].sum()})
    return pd.DataFrame(filas)


def resumir(sim: pd.DataFrame) -> pd.DataFrame:
    """Métrica principal y tabla complementaria, sumando todos los días."""
    g = sim.groupby(["k", "lista"])
    return pd.DataFrame({
        "monto en riesgo capturado (%)": g.capturado.sum() / g.riesgo.sum() * 100,
        "complementaria: todo el dinero tardío capturado (%)": g.capturado_todo.sum() / g.tardio_todo.sum() * 100,
        "complementaria: dinero ya tardío en la lista (% del saldo de la lista)": g.ya_tardio_en_lista.sum() / g.saldo_en_lista.sum() * 100,
    }).round(1)
