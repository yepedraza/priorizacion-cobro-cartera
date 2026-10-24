"""Elige los casos nuevos de la demostración en vivo y los guarda en `datos_crudos/casos_demo.json`.

Se corre en el computador del equipo:

    .venv/bin/python app/preparar_casos.py

Los archivos quedan en `datos_crudos/`, que Git ignora y que la imagen Docker no recibe: aunque no
llevan `id_saldo` ni NIT, son datos de la compañía.

- `casos_demo.json`: el cuerpo de cada llamada, para `/docs` o para `probar_servicio.py`.
- `casos_demo.md`: los mismos casos con los valores tal como los pide el formulario de `/demo`
  (valor en pesos en lugar de su logaritmo), para escribirlos en vivo.

Regla de selección, fijada antes de ver la predicción:

- **B, prueba (2025-07 a 2026-09):** una factura que terminó tardía y una que no. En cada grupo, la
  de probabilidad más cercana a la mediana de ese grupo: un caso típico, no el más favorable.
- **B, reciente:** de las facturas emitidas desde el 1/07/2025 que todavía no tienen desenlace
  conocido (vencimiento + 30 días después del 18/10/2026), la más reciente con historial de pago
  (`n_pagadas_hist > 0`).
- **A:** del 30 % de clientes de prueba de la segmentación, el más cercano al centro de cada
  segmento.

Ningún caso se usó para ajustar los modelos: B se ajustó con facturas de 2022-01 a 2025-06, y el
K-means con el 70 % de clientes de entrenamiento.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "app"))

from cartera import datos  # noqa: E402
from cartera import diseno as dis  # noqa: E402
from cartera import historial as hi  # noqa: E402
from cartera import muestra as mu  # noqa: E402
from cartera import segmentacion as sg  # noqa: E402
from cartera.diseno import CAT, CORTE, FECHA_CORTE, NUM  # noqa: E402
from cartera.etiqueta import UMBRAL_ATRASO  # noqa: E402
from guardar_segmentacion import NOMBRES, segmentos_del_cuaderno  # noqa: E402
from probar_servicio import a_json  # noqa: E402

DESTINO = RAIZ / "datos_crudos" / "casos_demo.json"
HOJA = RAIZ / "datos_crudos" / "casos_demo.md"
MODELO_B = RAIZ / "modelos" / "modelo_B.joblib"


def factura(fila, referencia):
    """Cuerpo para /predecir, con el valor inicial como saldo (para mostrar probabilidad × saldo)."""
    return a_json(fila) | {"referencia": referencia,
                           "saldo": round(float(np.expm1(fila.log_monto_inicial)), 2)}


def hoja(casos_b, casos_a):
    """Los casos con los campos y unidades del formulario de /demo, en el mismo orden."""
    def n(x, dec=0):
        # Sin separador de miles: se escribe tal cual en el formulario
        if x is None:
            return "—"
        return f"{x:.{dec}f}" if round(x, dec) != 0 else f"{0:.{dec}f}"  # sin «-0.00»

    filas_b = [
        ("Valor de la factura ($)", lambda f: n(f["saldo"])),
        ("Plazo pactado (días)", lambda f: n(f["plazo_dias_observado"])),
        ("Mes de emisión", lambda f: n(f["fecha_mes"])),
        ("Unidad de negocio", lambda f: f["unidad_negocio"]),
        ("Tipo de cliente", lambda f: f["tipo_cliente"]),
        ("Facturas pagadas antes", lambda f: n(f["n_pagadas_hist"])),
        ("Atraso promedio de esas facturas (días)", lambda f: n(f["atraso_prom_hist"], 4)),
        ("Saldo abierto del cliente ($)", lambda f: n(f["saldo_abierto_t"], 2)),
        ("Facturas abiertas", lambda f: n(f["n_abiertas_t"])),
        ("De ellas, ya vencidas", lambda f: n(f["n_vencidas_t"])),
        ("Antigüedad del cliente (días)", lambda f: n(f["antiguedad_dias"])),
    ]
    facs = [c["cuerpo"]["facturas"][0] for c in casos_b]
    lineas = ["# Casos de la demostración (confidencial: no sale de datos_crudos/)", "",
              "Generado por `app/preparar_casos.py`. Valores para escribir en el formulario de `/demo`.", "",
              "## Factura · riesgo de pago tardío", "",
              "| Campo | " + " | ".join(f["referencia"] for f in facs) + " |",
              "|---|" + "---|" * len(facs)]
    lineas += [f"| {nombre} | " + " | ".join(fun(f) for f in facs) + " |" for nombre, fun in filas_b]
    lineas += ["| **Resultado esperado** | " + " | ".join(pct(c["probabilidad_esperada"]) for c in casos_b) + " |",
               "| Desenlace real | " + " | ".join(c["desenlace_real"] for c in casos_b) + " |", ""]
    cls = [c["cuerpo"]["clientes"][0] for c in casos_a]
    filas_a = [("Atraso mediano (días)", lambda c: n(c["atraso_mediano"], 4)),
               ("Rango intercuartílico del atraso (días)", lambda c: n(c["atraso_iqr"], 4)),
               ("% de facturas con más de 30 días", lambda c: n(c["pct_tardias"], 4)),
               ("Facturas por año", lambda c: n(c["facturas_por_anio"], 4)),
               ("Monto mediano de sus facturas ($)", lambda c: n(float(np.expm1(c["log_monto_mediano"])), 2)),
               ("% pagadas con varios abonos", lambda c: n(c["pct_varios_abonos"], 4)),
               ("% cerradas con notas o ajustes", lambda c: n(c["pct_cierre_nota"], 4))]
    lineas += ["## Cliente · segmento y gestión", "",
               "| Campo | " + " | ".join(c["referencia"] for c in cls) + " |", "|---|" + "---|" * len(cls)]
    lineas += [f"| {nombre} | " + " | ".join(fun(c) for c in cls) + " |" for nombre, fun in filas_a]
    lineas += ["| **Resultado esperado** | " + " | ".join(c["segmento_esperado"] for c in casos_a) + " |",
               "| Después de 2025-06 | " + " | ".join(
                   f'{c["despues_de_2025_06"]["pct_tardias"]} % tardías en {c["despues_de_2025_06"]["facturas_con_desenlace"]} facturas'
                   if c["despues_de_2025_06"] else "sin facturas" for c in casos_a) + " |", ""]
    return "\n".join(lineas)


def pct(p):
    return f"{p * 100:.1f} %"


def main():
    import joblib
    modelo = joblib.load(MODELO_B)
    saldos, movs = datos.leer_todo()
    prueba = dis.conjuntos(saldos, movs)["prueba"]

    # B · prueba: la factura más típica de cada desenlace
    prueba = prueba.assign(p=modelo.predict_proba(prueba[NUM + CAT])[:, 1])
    casos_b = []
    for tardia, nombre in [(1, "terminó tardía"), (0, "se pagó a tiempo o con 30 días o menos de atraso")]:
        g = prueba[prueba.tardia == tardia]
        elegida = g.loc[(g.p - g.p.median()).abs().sort_values(kind="stable").index[0]]
        casos_b.append({
            "caso": f"B · prueba · {nombre}",
            "por_que_es_nuevo": "Factura del periodo de prueba (emitida desde el 1/07/2025); el modelo "
                                "se ajustó solo con facturas de 2022-01 a 2025-06.",
            "emitida": elegida.fecha.strftime("%Y-%m"),
            "desenlace_real": nombre,
            "probabilidad_esperada": round(float(elegida.p), 4),
            "mediana_de_su_grupo": round(float(g.p.median()), 4),
            "cuerpo": {"facturas": [factura(elegida, f"prueba {'tardía' if tardia else 'a tiempo'}")]},
        })

    # B · reciente: sin desenlace conocido al corte de los datos
    facturas = saldos[saldos.es_deuda_facturada & (saldos.plazo_dias_observado >= 0)
                      & (saldos.fecha >= CORTE)
                      & (saldos.fecha_vencimiento + pd.Timedelta(days=UMBRAL_ATRASO) > FECHA_CORTE)]
    facturas = mu.agregar_log_monto_inicial(facturas, movs)
    facturas = facturas.join(hi.calcular(facturas, saldos, movs))
    con_historial = facturas[facturas.n_pagadas_hist > 0].sort_values(["fecha", "id_saldo"], kind="stable")
    reciente = con_historial.iloc[-1]
    p_rec = float(modelo.predict_proba(con_historial.iloc[[-1]][NUM + CAT])[:, 1][0])
    casos_b.append({
        "caso": "B · reciente · desenlace todavía desconocido",
        "por_que_es_nuevo": "Emitida después del periodo de prueba; vence + 30 días después del "
                            "18/10/2026, así que no está en ningún conjunto (ni entrenamiento ni prueba).",
        "emitida": reciente.fecha.strftime("%Y-%m-%d"),
        "desenlace_real": "desconocido: es el caso de operación",
        "probabilidad_esperada": round(p_rec, 4),
        "facturas_candidatas": len(facturas),
        "cuerpo": {"facturas": [factura(reciente, "reciente")]},
    })

    # Lista de las tres juntas, para mostrar el orden por probabilidad × saldo
    lista = {"facturas": [c["cuerpo"]["facturas"][0] for c in casos_b]}

    # A · clientes de prueba, el más cercano al centro de cada segmento
    prep, km, renum, segmento, _, clientes = segmentos_del_cuaderno(sg.perfil(saldos, movs))
    dist = km.transform(prep.transform(clientes[sg.VARIABLES]))
    grupo = km.predict(prep.transform(clientes[sg.VARIABLES]))
    posterior = sg.desenlace_posterior(saldos, movs)
    casos_a = []
    for g in range(sg.K):
        nombre = NOMBRES[int(renum[g])]
        en_g = np.where(grupo == g)[0]
        i = en_g[np.argmin(dist[en_g, g])]
        cli = clientes.iloc[i]
        post = posterior.loc[clientes.index[i]] if clientes.index[i] in posterior.index else None
        casos_a.append({
            "caso": f"A · cliente de prueba · {nombre}",
            "por_que_es_nuevo": "Cliente del 30 % de prueba de la segmentación; el K-means se ajustó "
                                "con el 70 % de entrenamiento.",
            "segmento_esperado": nombre,
            "despues_de_2025_06": None if post is None else {
                "facturas_con_desenlace": int(post.facturas),
                "pct_tardias": round(float(post.tardias / post.facturas * 100), 1)},
            "cuerpo": {"clientes": [{v: round(float(cli[v]), 4) for v in sg.VARIABLES}
                                    | {"referencia": f"cliente {nombre}"}]},
        })
        assert segmento.loc[clientes.index[i]] == nombre

    DESTINO.write_text(json.dumps({"B": casos_b, "B_lista_de_las_tres": lista, "A": casos_a},
                                  ensure_ascii=False, indent=2), encoding="utf-8")
    texto = DESTINO.read_text(encoding="utf-8")
    ids = [x for x in (*saldos.nit_cliente.dropna().astype(str).unique(),
                       *saldos.id_saldo.dropna().astype(str).unique()) if len(x) >= 5]
    assert not [x for x in ids if f'"{x}"' in texto], "el archivo de casos contiene identificadores"

    HOJA.write_text(hoja(casos_b, casos_a), encoding="utf-8")
    texto_hoja = HOJA.read_text(encoding="utf-8")
    assert not [x for x in ids if x in texto_hoja.split()], "la hoja contiene identificadores"

    print(f"Casos guardados en {DESTINO.relative_to(RAIZ)} y {HOJA.relative_to(RAIZ)} (sin id_saldo ni NIT)")
    for c in casos_b:
        print(f"  {c['caso']}: emitida {c['emitida']}, probabilidad {c['probabilidad_esperada']}")
    for c in casos_a:
        print(f"  {c['caso']}: después de 2025-06 → {c['despues_de_2025_06']}")


if __name__ == "__main__":
    main()
