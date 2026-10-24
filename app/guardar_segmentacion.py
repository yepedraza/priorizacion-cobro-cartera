"""Ajusta la segmentación A, la guarda en `modelos/` y verifica que asigna como `plazo_C.ipynb`.

Se corre en el computador del equipo (necesita `datos_crudos/`):

    .venv/bin/python app/guardar_segmentacion.py

El ajuste es el de `entrega/plazo_C.ipynb` §0 (el mismo de R17): perfil de pago de cada cliente
con al menos 5 facturas pagadas, partición 70/30 de clientes con la SEMILLA, recorte y escala
aprendidos con el 70 %, y K-means con k = 2 y 50 reinicios. Los segmentos se numeran por atraso
mediano: 0 = «paga a tiempo o casi», 1 = «paga tarde».

Verificación: el modelo leído desde el disco asigna a los 226 clientes el mismo segmento que el
código del cuaderno (171 y 55).

Junto al modelo se guarda lo que C propone para cada segmento (la acción del piloto y el plazo
real medido en `plazo_C.ipynb` §2). C es una política, no un modelo: el servicio solo la devuelve.
"""

import hashlib
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "app"))

from cartera import datos  # noqa: E402
from cartera import segmentacion as sg  # noqa: E402
from cartera.config import SEMILLA  # noqa: E402
from guardar_modelo import revisar_que_no_lleva_datos  # noqa: E402

DESTINO = RAIZ / "modelos" / "segmentacion_A.joblib"
FICHA = RAIZ / "modelos" / "segmentacion_A.json"
NOMBRES = {0: "paga a tiempo o casi", 1: "paga tarde"}

# Componente C: acción del piloto (decisiones del equipo) y plazo real (plazo_C.ipynb §2)
POLITICA_C = {
    "paga a tiempo o casi": {
        "accion": "Correo automático por factura, 5 días hábiles antes del vencimiento",
        "dias_hasta_el_pago": {"mediana": 28.0, "percentil_75": 43.0},
        "pct_pagadas_dentro_del_plazo": 28.0,
    },
    "paga tarde": {
        "accion": "Contacto de la gestora apenas vence cada factura",
        "dias_hasta_el_pago": {"mediana": 72.5, "percentil_75": 115.8},
        "pct_pagadas_dentro_del_plazo": 4.5,
    },
}
AVISO_C = ("Propuesta para el piloto de C: su efecto no está demostrado. El piloto asigna clientes "
           "al azar dentro de cada segmento, mitad con esta gestión y mitad con la actual.")


def segmentos_del_cuaderno(perfil):
    """Copia literal de plazo_C.ipynb §0: devuelve el modelo y el segmento de los 226 clientes."""
    ent, prueba = sg.particion(perfil, SEMILLA)
    prep = sg.preparacion().fit(ent[sg.VARIABLES])
    km = KMeans(sg.K, n_init=sg.N_INIT, random_state=SEMILLA).fit(prep.transform(ent[sg.VARIABLES]))
    orden = np.argsort([np.median(ent.atraso_mediano.to_numpy()[km.labels_ == g]) for g in range(sg.K)])
    renum = np.argsort(orden)
    segmento = pd.concat([pd.Series(renum[km.labels_], index=ent.index),
                          pd.Series(renum[km.predict(prep.transform(prueba[sg.VARIABLES]))], index=prueba.index)]
                         ).map(NOMBRES).rename("segmento")
    return prep, km, renum, segmento, ent, prueba


def main():
    saldos, movs = datos.leer_todo()
    perfil = sg.perfil(saldos, movs)
    prep, km, renum, segmento, ent, prueba = segmentos_del_cuaderno(perfil)

    # El modelo no necesita las etiquetas de los clientes de entrenamiento para asignar
    del km.labels_
    modelo = Pipeline([("prep", prep), ("kmeans", km)])
    joblib.dump(modelo, DESTINO)
    cargado = joblib.load(DESTINO)

    asignado = pd.Series(renum[cargado.predict(perfil[sg.VARIABLES])], index=perfil.index).map(NOMBRES)
    assert asignado.sort_index().equals(segmento.sort_index()), "el modelo guardado asigna distinto"
    conteo = asignado.value_counts().to_dict()
    assert conteo == {"paga a tiempo o casi": 171, "paga tarde": 55}, conteo

    arreglos = revisar_que_no_lleva_datos(cargado)
    crudo = DESTINO.read_bytes()
    nits = [x for x in saldos.nit_cliente.dropna().astype(str).unique() if len(x) >= 5]
    assert not [x for x in nits if x.encode() in crudo], "el archivo contiene NIT"

    ficha = {
        "modelo": "A · K-means k = 2 sobre el perfil de pago del cliente (plazo_C.ipynb §0, R17)",
        "variables": sg.VARIABLES,
        "ventana_del_perfil": "facturas emitidas de 2022-01 a 2025-06 con desenlace conocido al 1/07/2025",
        "minimo_facturas_pagadas": sg.MIN_PAGADAS,
        "clientes": {"entrenamiento": len(ent), "prueba": len(prueba), "por_segmento": conteo},
        "cluster_a_segmento": {str(g): NOMBRES[int(renum[g])] for g in range(sg.K)},
        "politica_C": POLITICA_C,
        "aviso_C": AVISO_C,
        "semilla": SEMILLA,
        "verificacion": "asigna a los 226 clientes el mismo segmento que plazo_C.ipynb §0",
        "sha256": hashlib.sha256(crudo).hexdigest(),
        "contenido": arreglos,
    }
    FICHA.write_text(json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Modelo guardado en {DESTINO.relative_to(RAIZ)} ({len(crudo) / 1024:.1f} KB)")
    print(f"Clientes: {len(ent)} de entrenamiento y {len(prueba)} de prueba | por segmento: {conteo}")
    print("Asignación idéntica a plazo_C.ipynb en los 226 clientes: sí")
    print("Contenido del archivo:")
    for a in arreglos:
        print("  " + a)


if __name__ == "__main__":
    main()
