"""Prueba el servicio contra el modelo del cuaderno, con facturas de la prueba.

Se corre en el computador del equipo (necesita `datos_crudos/`). Por defecto prueba el servicio en
el mismo proceso; con `--url` prueba uno ya levantado (local o en Azure). El token se lee de la
variable de entorno `TOKEN_API`.

    TOKEN_API=... .venv/bin/python app/probar_servicio.py
    TOKEN_API=... .venv/bin/python app/probar_servicio.py --url https://<servicio>

Comprueba:
1. sin token, o con uno incorrecto, responde 401;
2. para 200 facturas de la prueba, la probabilidad del servicio es la misma (a 4 decimales) que la
   del Pipeline ajustado en el cuaderno, que aquí se vuelve a ajustar con el mismo código;
3. una categoría desconocida se rechaza con 422;
4. para los 68 clientes de prueba de la segmentación, `/segmentar` da el mismo segmento que
   `plazo_C.ipynb`;
5. si se pasa `TOKEN_QR`, el token del QR también da acceso.

Las facturas viajan sin `id_saldo` ni NIT: solo sus 11 predictoras.
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "app"))

from cartera import datos  # noqa: E402
from cartera import diseno as dis  # noqa: E402
from cartera import segmentacion as sg  # noqa: E402
from cartera.diseno import CAT, NUM  # noqa: E402
from guardar_modelo import modelo_final  # noqa: E402
from guardar_segmentacion import segmentos_del_cuaderno  # noqa: E402


def cliente(url):
    if url:
        import httpx
        return httpx.Client(base_url=url, timeout=60)
    from fastapi.testclient import TestClient
    import servicio
    return TestClient(servicio.app)


def a_json(fila):
    d = {c: fila[c] for c in NUM + CAT}
    for c in ["plazo_dias_observado", "fecha_mes", "n_pagadas_hist", "n_abiertas_t", "n_vencidas_t"]:
        d[c] = int(d[c])
    d["atraso_prom_hist"] = None if np.isnan(d["atraso_prom_hist"]) else float(d["atraso_prom_hist"])
    for c in ["log_monto_inicial", "saldo_abierto_t", "antiguedad_dias"]:
        d[c] = float(d[c])
    return d


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url")
    args = parser.parse_args()
    token = os.environ["TOKEN_API"]

    saldos, movs = datos.leer_todo()
    conj = dis.conjuntos(saldos, movs)
    ent, prueba = conj["entrenamiento completo"], conj["prueba"]
    *_, segmento, _, clientes_prueba = segmentos_del_cuaderno(sg.perfil(saldos, movs))
    del saldos, movs
    cuaderno = modelo_final().fit(ent[NUM + CAT], ent.tardia)  # calibrada(ent) del cuaderno

    muestra = prueba.sample(200, random_state=0)
    esperadas = cuaderno.predict_proba(muestra[NUM + CAT])[:, 1]
    cuerpo = {"facturas": [a_json(f) | {"referencia": f"prueba {i}"}
                           for i, (_, f) in enumerate(muestra.iterrows())]}

    c = cliente(args.url)
    assert c.get("/salud").status_code == 200
    assert c.post("/predecir", json=cuerpo).status_code == 401, "sin token debería dar 401"
    assert c.post("/predecir", json=cuerpo, headers={"Authorization": "Bearer otro"}).status_code == 401
    cab = {"Authorization": f"Bearer {token}"}

    r = c.post("/predecir", json=cuerpo, headers=cab)
    assert r.status_code == 200, r.text
    obtenidas = {x["referencia"]: x["probabilidad_pago_tardio"] for x in r.json()}
    dif = max(abs(obtenidas[f"prueba {i}"] - round(p, 4)) for i, p in enumerate(esperadas))
    assert dif == 0, f"diferencia máxima {dif}"

    malo = {"facturas": [cuerpo["facturas"][0] | {"unidad_negocio": "Unidad 99"}]}
    assert c.post("/predecir", json=malo, headers=cab).status_code == 422

    cuerpo_a = {"clientes": [{v: float(f[v]) for v in sg.VARIABLES} | {"referencia": f"cliente {i}"}
                             for i, (_, f) in enumerate(clientes_prueba.iterrows())]}
    assert c.post("/segmentar", json=cuerpo_a).status_code == 401
    r = c.post("/segmentar", json=cuerpo_a, headers=cab)
    assert r.status_code == 200, r.text
    obtenidos = [x["segmento"] for x in r.json()]
    assert obtenidos == list(segmento.loc[clientes_prueba.index]), "segmentos distintos al cuaderno"

    token_qr = os.environ.get("TOKEN_QR")
    if token_qr:
        assert c.get("/modelo", headers={"Authorization": f"Bearer {token_qr}"}).status_code == 200

    print(f"Servicio: {args.url or 'en el mismo proceso'}")
    print("401 sin token y con token incorrecto: sí")
    print(f"200 facturas de la prueba: probabilidad idéntica a la del cuaderno (diferencia máxima {dif})")
    print("Categoría desconocida rechazada con 422: sí")
    print(f"{len(obtenidos)} clientes de prueba de A: mismo segmento que plazo_C.ipynb")
    if token_qr:
        print("Token del QR: da acceso")


if __name__ == "__main__":
    main()
