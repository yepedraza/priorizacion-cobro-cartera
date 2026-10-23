"""Genera los cinco gráficos de validación del anexo del informe en entrega/figuras/.

Se calculan con los datos de la compañía (`datos_crudos/`), **sin la prueba**: solo con facturas
emitidas antes del corte del 1/07/2025 y con desenlaces conocidos a esa fecha. El conjunto de prueba
se descarta apenas se arma la partición y no se usa. El 38,6 % de la prueba que aparece en A1 es la
cifra ya reportada en `evaluacion_B.ipynb` §3, no un cálculo nuevo.

Al final imprime cifras de control que deben coincidir con los cuadernos.

Uso:  ../.venv/bin/python scripts/figuras_anexo.py   (entorno del kernel «Python (ML1)»)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_recall_curve
from sklearn.pipeline import Pipeline

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ / "src"), str(RAIZ / "scripts")]

import figuras_informe as fi  # estilo y paleta comunes  # noqa: E402
from cartera import backtest as bt  # noqa: E402
from cartera import datos  # noqa: E402
from cartera import diseno as dis  # noqa: E402
from cartera import etiqueta as et  # noqa: E402
from cartera import historial as hi  # noqa: E402
from cartera import muestra as mu  # noqa: E402
from cartera import segmentacion as sg  # noqa: E402
from cartera.config import SEMILLA  # noqa: E402
from cartera.diseno import CAT, CORTE, DESDE, NUM  # noqa: E402

plt = fi.plt
TARDIAS_PRUEBA = 38.6  # evaluacion_B.ipynb §3, ya reportado
NOMBRES_VARIABLES = {"atraso_prom_hist": "Atraso promedio histórico", "n_vencidas_t": "Facturas vencidas al emitir",
                     "n_pagadas_hist": "Facturas pagadas antes", "plazo_dias_observado": "Plazo (días)",
                     "log_monto_inicial": "Monto inicial (log)", "fecha_mes": "Mes de emisión"}
MESES = "ene feb mar abr may jun jul ago sep oct nov dic".split()


def legible(nombre):
    if nombre in NOMBRES_VARIABLES:
        return NOMBRES_VARIABLES[nombre]
    for prefijo, texto in (("tipo_cliente_", "Tipo de cliente: "), ("unidad_negocio_", "")):
        if nombre.startswith(prefijo):
            return texto + nombre[len(prefijo):].replace("_", " ").capitalize()
    return nombre.replace("_", " ")


def calibrada(datos_ent):
    """Modelo de la lista diaria: logística sin class_weight, como en evaluacion_B.ipynb."""
    return Pipeline([("prep", dis.prep_lineal()), ("est", LogisticRegression(class_weight=None, max_iter=2000))]
                    ).fit(datos_ent[NUM + CAT], datos_ent.tardia)


def tardias_por_trimestre(ent, control):
    """A1 · Proporción de tardías por trimestre de emisión, entrenamiento completo."""
    t = ent.groupby(ent.fecha.dt.to_period("Q")).tardia.agg(["mean", "size"])
    fig, ax = plt.subplots(figsize=(7.2, 2.6))
    x = range(len(t))
    ax.axhspan(31, 34, color=fi.REJILLA, label="Rango de referencia anual (31–34 %)")
    ax.plot(x, t["mean"] * 100, "-o", color=fi.AZUL, lw=2, ms=4, label="Entrenamiento, por trimestre")
    ax.axhline(TARDIAS_PRUEBA, color=fi.NARANJA, lw=1.5, ls="--", label=f"Prueba, total ({fi.coma(TARDIAS_PRUEBA)} %)")
    ax.set_xticks(list(x)[::2], [str(p).replace("Q", "-T") for p in t.index][::2], rotation=0)
    ax.set_ylabel("% de facturas tardías"); ax.set_ylim(0, 60); ax.grid(axis="x", visible=False)
    ax.legend(loc="lower left", fontsize=7, ncol=3)
    fi.guardar(fig, "anexo1_tardias_trimestre.png")
    control["A1 · facturas de entrenamiento"] = int(t["size"].sum())


def curva_pr(subent, val, control):
    """A2 · Curva PR en validación: modelo entrenado con el subentrenamiento."""
    p = calibrada(subent).predict_proba(val[NUM + CAT])[:, 1]
    precision, recall, _ = precision_recall_curve(val.tardia, p)
    ap, base = average_precision_score(val.tardia, p), val.tardia.mean()
    fig, ax = plt.subplots(figsize=(3.6, 3.2))
    ax.plot(recall, precision, color=fi.AZUL, lw=2, label=f"Regresión logística (AUC-PR {fi.coma(ap, 3)})")
    ax.axhline(base, color=fi.GRIS, lw=1, ls="--", label=f"Línea base ({fi.coma(base, 3)})")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.02)
    ax.xaxis.set_major_formatter(fi.EJE_COMA); ax.yaxis.set_major_formatter(fi.EJE_COMA)
    ax.set_xlabel("Exhaustividad (recall)"); ax.set_ylabel("Precisión")
    ax.legend(loc="upper right", fontsize=7)
    fi.guardar(fig, "anexo2_curva_pr_validacion.png")
    control["A2 · AUC-PR en validación (cuaderno: 0,723)"] = round(ap, 3)


def coeficientes(ent, control):
    """A3 · Coeficientes de la logística final, entrenada con el entrenamiento completo (variables escaladas)."""
    modelo = calibrada(ent)
    nombres = [n.split("__", 1)[1] for n in modelo.named_steps["prep"].get_feature_names_out()]
    coef = pd.Series(modelo.named_steps["est"].coef_[0], index=nombres)
    top = coef.reindex(coef.abs().sort_values(ascending=False).index[:12])[::-1]
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    ax.barh(range(len(top)), top.values, color=[fi.NARANJA if v > 0 else fi.AZUL for v in top.values], height=0.6)
    ax.axvline(0, color=fi.TINTA_2, lw=0.8)
    ax.set_yticks(range(len(top)), [legible(n) for n in top.index]); ax.xaxis.set_major_formatter(fi.EJE_COMA)
    ax.set_xlabel("Coeficiente (naranja: sube el riesgo; azul: lo baja)"); ax.grid(axis="y", visible=False)
    fi.guardar(fig, "anexo3_coeficientes.png")
    control["A3 · variable de mayor coeficiente"] = coef.abs().idxmax()


def capturado_por_dia(saldos, movs, subent, control):
    """A4 · Ensayo del backtest en validación (evaluacion_B.ipynb §2), K = 20, día a día."""
    facturas = saldos[saldos.es_deuda_facturada & (saldos.plazo_dias_observado >= 0) & (saldos.fecha >= "2021-06-01")]
    facturas = mu.agregar_log_monto_inicial(facturas, movs)
    facturas = facturas.join(hi.calcular(facturas, saldos, movs))
    prob = pd.Series(calibrada(subent).predict_proba(facturas[NUM + CAT])[:, 1], index=facturas.id_saldo)
    sim = bt.simular(bt.Cartera(saldos, movs), pd.bdate_range("2024-07-01", "2025-05-30"), prob,
                     bt.desenlace_final(saldos, movs, CORTE), ks=(20,))
    diario = sim.assign(pct=sim.capturado / sim.riesgo * 100).pivot(index="dia", columns="lista", values="pct")
    total = sim.groupby("lista").capturado.sum() / sim.groupby("lista").riesgo.sum() * 100
    fig, ax = plt.subplots(figsize=(7.2, 2.7))
    colores = [fi.AZUL, fi.AGUA, fi.NARANJA]
    orden = sorted(diario.columns, key=lambda c: -total[c])
    for lista, color in zip(orden, colores):
        ax.plot(diario.index, diario[lista].rolling(20, min_periods=5).mean(), color=color, lw=2,
                label=f"{lista} (total {fi.coma(total[lista])} %)")
    ax.set_ylabel("% del dinero en duda tardío\nen la lista (media móvil 20 días)"); ax.set_ylim(0, 100)
    marcas = pd.date_range("2024-07-01", "2025-05-01", freq="2MS")
    ax.set_xticks(marcas, [f"{MESES[m.month - 1]} {m.year}" for m in marcas])
    ax.legend(loc="lower left", fontsize=7, ncol=3); ax.grid(axis="x", visible=False)
    fi.guardar(fig, "anexo4_capturado_diario_validacion.png")
    for lista in orden:
        control[f"A4 · total K = 20, {lista}"] = round(total[lista], 1)
    control["A4 · días ganados por el modelo frente a cada lista"] = {
        c: int((diario[orden[0]] > diario[c]).sum()) for c in orden[1:]}


def dias_hasta_pago(saldos, movs, control):
    """A5 · Días desde la emisión hasta el pago por segmento (plazo_C.ipynb §2), hasta junio de 2025."""
    perfil = sg.perfil(saldos, movs)
    ent_c, prueba_c = sg.particion(perfil, SEMILLA)   # partición de clientes de A, no la prueba temporal
    prep = sg.preparacion().fit(ent_c[sg.VARIABLES])
    km = KMeans(sg.K, n_init=sg.N_INIT, random_state=SEMILLA).fit(prep.transform(ent_c[sg.VARIABLES]))
    orden = np.argsort([np.median(ent_c.atraso_mediano.to_numpy()[km.labels_ == g]) for g in range(sg.K)])
    renum = np.argsort(orden)
    nombres = {0: "Paga a tiempo o casi", 1: "Paga tarde"}
    segmento = pd.concat([pd.Series(renum[km.labels_], index=ent_c.index),
                          pd.Series(renum[km.predict(prep.transform(prueba_c[sg.VARIABLES]))], index=prueba_c.index)]
                         ).map(nombres).rename("segmento")
    cerradas = et.facturas_cerradas(saldos)
    cerradas = cerradas[(cerradas.fecha >= DESDE) & (cerradas.fecha < CORTE)
                        & (cerradas.fecha_cancelacion_registrada < CORTE) & (cerradas.plazo_dias_observado >= 0)]
    pag = cerradas.assign(atraso=et.atraso_etiqueta(cerradas, movs)).dropna(subset=["atraso"])
    pag = pag.assign(dias_pago=pag.plazo_dias_observado + pag.atraso).join(segmento, on="nit_cliente", how="inner")
    fig, ax = plt.subplots(figsize=(7.2, 2.4))
    for i, (seg, color) in enumerate(zip(nombres.values(), [fi.AZUL, fi.NARANJA])):
        d = pag.loc[pag.segmento == seg, "dias_pago"]
        ax.boxplot(d, positions=[i], orientation="horizontal", widths=0.5, showfliers=False, patch_artist=True,
                   boxprops=dict(facecolor=color, edgecolor=color, alpha=0.85),
                   medianprops=dict(color="white", lw=2), whiskerprops=dict(color=color), capprops=dict(color=color))
        ax.text(d.median(), i + 0.36, f"mediana {fi.coma(d.median())} días", ha="center", fontsize=7.5, color=fi.TINTA)
        control[f"A5 · mediana de días hasta el pago, {seg}"] = float(d.median())
    ax.axvline(15, color=fi.TINTA_2, lw=1, ls="--")
    ax.text(18, 1.62, "plazo pactado mediano: 15 días", fontsize=7.5, color=fi.TINTA_2, va="center")
    ax.set_yticks([0, 1], list(nombres.values())); ax.set_ylim(-0.6, 1.8)
    ax.set_xlabel("Días desde la emisión hasta el último recibo de caja (sin valores extremos)")
    ax.grid(axis="y", visible=False)
    fi.guardar(fig, "anexo5_dias_pago_segmento.png")


if __name__ == "__main__":
    np.random.seed(SEMILLA)
    fi.SALIDA.mkdir(parents=True, exist_ok=True)
    saldos, movs = datos.leer_todo()
    conj = dis.conjuntos(saldos, movs)
    subent, val, ent = conj["subentrenamiento"], conj["validación"], conj["entrenamiento completo"]
    del conj  # la prueba no se usa
    assert ent.fecha.max() < CORTE and val.fecha.max() < CORTE, "un conjunto pasa del corte"
    control = {}
    print("Gráficos del anexo en entrega/figuras:")
    tardias_por_trimestre(ent, control)
    curva_pr(subent, val, control)
    coeficientes(ent, control)
    capturado_por_dia(saldos, movs, subent, control)
    dias_hasta_pago(saldos, movs, control)
    print("\nCifras de control:")
    for k, v in control.items():
        print(f"   {k}: {v}")
