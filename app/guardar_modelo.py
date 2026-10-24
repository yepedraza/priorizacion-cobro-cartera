"""Ajusta el modelo final de B, lo guarda en `modelos/` y verifica que es el mismo del informe.

Se corre en el computador del equipo, que es el único con `datos_crudos/`. La imagen Docker y la
nube reciben solo el archivo del modelo, nunca los datos.

    .venv/bin/python app/guardar_modelo.py

El ajuste es el de `entrega/evaluacion_B.ipynb` §3, línea por línea: la regresión logística sin
`class_weight` dentro del `Pipeline` de preparación lineal, con las 11 predictoras y el
entrenamiento completo (facturas de 2022-01 a 2025-06 con desenlace conocido al 1/07/2025).

Verificación: el modelo **leído desde el disco** tiene que reproducir las cifras que el cuaderno
publicó para la prueba (AUC-PR, AUC-ROC, Brier y la tabla de calibración). No se decide nada con
la prueba: solo se recalcula lo que ya quedó fijado el 21/10/2026.
"""

import hashlib
import json
import pickle
import sys
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.calibration import calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from cartera import datos  # noqa: E402
from cartera import diseno as dis  # noqa: E402
from cartera.config import SEMILLA  # noqa: E402
from cartera.diseno import CAT, NUM  # noqa: E402

DESTINO = RAIZ / "modelos" / "modelo_B.joblib"
FICHA = RAIZ / "modelos" / "modelo_B.json"

# Cifras publicadas en evaluacion_B.ipynb §3 (consulta única a la prueba, 21/10/2026)
PUBLICADAS = {"facturas": 3970, "AUC-PR": 0.744, "AUC-ROC": 0.829, "Brier": 0.177}
CALIBRACION_PUBLICADA = {
    "probabilidad media predicha": [0.024, 0.055, 0.095, 0.125, 0.168, 0.226, 0.320, 0.432, 0.568, 0.809],
    "proporción real de tardías": [0.038, 0.128, 0.161, 0.156, 0.214, 0.385, 0.516, 0.647, 0.781, 0.836],
}


def modelo_final() -> Pipeline:
    """El mismo objeto que `calibrada(ent)` en evaluacion_B.ipynb, sin ajustar."""
    return Pipeline([("prep", dis.prep_lineal()),
                     ("est", LogisticRegression(class_weight=None, max_iter=2000))])


def revisar_que_no_lleva_datos(modelo: Pipeline) -> list[str]:
    """Lista cada arreglo guardado dentro del modelo con su forma.

    Un modelo que llevara filas tendría arreglos del tamaño del entrenamiento. Aquí solo debe haber
    vectores del tamaño de las columnas (medianas, medias, escalas, coeficientes) y las categorías.
    """
    hallazgos = []

    def recorrer(obj, ruta, vistos):
        if id(obj) in vistos:
            return
        vistos.add(id(obj))
        if isinstance(obj, np.ndarray):
            hallazgos.append(f"{ruta}: {obj.dtype} {obj.shape}")
            if obj.size > 100:
                raise AssertionError(f"{ruta} tiene {obj.size} valores: podría llevar filas de datos")
        elif isinstance(obj, (pd.DataFrame, pd.Series)):
            raise AssertionError(f"{ruta} es un {type(obj).__name__}: el modelo no debe guardar tablas")
        elif isinstance(obj, (list, tuple)):
            for i, x in enumerate(obj):
                recorrer(x, f"{ruta}[{i}]", vistos)
        elif isinstance(obj, dict):
            for k, x in obj.items():
                recorrer(x, f"{ruta}.{k}", vistos)
        elif hasattr(obj, "__dict__"):
            for k, x in vars(obj).items():
                recorrer(x, f"{ruta}.{k}", vistos)

    recorrer(modelo, "modelo", set())
    return hallazgos


def main():
    np.random.seed(SEMILLA)
    saldos, movs = datos.leer_todo()
    conj = dis.conjuntos(saldos, movs)
    ent, prueba = conj["entrenamiento completo"], conj["prueba"]

    modelo = modelo_final().fit(ent[NUM + CAT], ent.tardia)

    DESTINO.parent.mkdir(exist_ok=True)
    joblib.dump(modelo, DESTINO)
    cargado = joblib.load(DESTINO)

    # 1. El modelo leído del disco predice igual que el recién ajustado
    X_pr, y_pr = prueba[NUM + CAT], prueba.tardia.astype(int)
    p_mem = modelo.predict_proba(X_pr)[:, 1]
    p_pr = cargado.predict_proba(X_pr)[:, 1]
    assert np.array_equal(p_mem, p_pr), "el modelo guardado no predice igual que el ajustado"

    # 2. Reproduce las cifras publicadas en el cuaderno
    obtenidas = {"facturas": len(prueba),
                 "AUC-PR": round(average_precision_score(y_pr, p_pr), 3),
                 "AUC-ROC": round(roc_auc_score(y_pr, p_pr), 3),
                 "Brier": round(brier_score_loss(y_pr, p_pr), 3)}
    frac, media = calibration_curve(y_pr, p_pr, n_bins=10, strategy="quantile")
    calibracion = {"probabilidad media predicha": list(np.round(media, 3)),
                   "proporción real de tardías": list(np.round(frac, 3))}
    for k, v in PUBLICADAS.items():
        assert obtenidas[k] == v, f"{k}: el cuaderno publicó {v} y el modelo guardado da {obtenidas[k]}"
    for k, v in CALIBRACION_PUBLICADA.items():
        assert np.allclose(calibracion[k], v, atol=5e-4), f"tabla de calibración distinta en «{k}»"

    # 3. El archivo no lleva datos
    arreglos = revisar_que_no_lleva_datos(cargado)
    crudo = DESTINO.read_bytes()
    nits = saldos.nit_cliente.dropna().astype(str).unique()
    ids = saldos.id_saldo.dropna().astype(str).unique()
    filtrados = [x for x in (*nits, *ids) if len(x) >= 5 and x.encode() in crudo]
    assert not filtrados, f"el archivo del modelo contiene identificadores: {filtrados[:5]}"
    pickle.loads(pickle.dumps(cargado))  # se puede volver a serializar

    ficha = {
        "modelo": "B · regresión logística sin class_weight (evaluacion_B.ipynb §3)",
        "fecha_ajuste": date.today().isoformat(),
        "entrenamiento": {"desde": "2022-01-01", "hasta": "2025-06-30", "facturas": len(ent),
                          "tardias_pct": round(float(ent.tardia.mean()) * 100, 1)},
        "predictoras_numericas": NUM,
        "predictoras_categoricas": CAT,
        "categorias": {c: list(map(str, cats)) for c, cats in
                       zip(CAT, cargado.named_steps["prep"].named_transformers_["cat"].categories_)},
        "semilla": SEMILLA,
        "versiones": {"python": sys.version.split()[0], "scikit-learn": sklearn.__version__,
                      "pandas": pd.__version__, "numpy": np.__version__, "scipy": scipy.__version__,
                      "joblib": joblib.__version__},
        "verificacion_prueba": {"publicadas": PUBLICADAS, "obtenidas": obtenidas, "coinciden": True},
        "sha256": hashlib.sha256(crudo).hexdigest(),
        "contenido": arreglos,
    }
    FICHA.write_text(json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Modelo guardado en {DESTINO.relative_to(RAIZ)} ({len(crudo) / 1024:.1f} KB)")
    print(f"Entrenamiento: {len(ent)} facturas | prueba: {len(prueba)} facturas")
    print("Cifras de la prueba, publicadas → obtenidas con el modelo leído del disco:")
    for k in PUBLICADAS:
        print(f"  {k}: {PUBLICADAS[k]} → {obtenidas[k]}")
    print("Tabla de calibración: coincide en los 10 tramos")
    print(f"Contenido del archivo ({len(arreglos)} arreglos, ninguno con filas de datos):")
    for a in arreglos:
        print("  " + a)
    print(f"sha256: {ficha['sha256']}")


if __name__ == "__main__":
    main()
