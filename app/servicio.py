"""Servicio del score de pago tardío (B): el modelo final del informe, fuera del cuaderno.

Recibe las 11 predictoras de cada factura ya calculadas (el servicio no tiene ni consulta los datos
de la compañía) y devuelve la probabilidad de que se pague con más de 30 días de atraso.

`/segmentar` agrega la segmentación A: recibe el perfil de pago de un cliente y devuelve su
segmento y lo que C propone para él (acción del piloto y plazo real del segmento).

Acceso: todas las rutas salvo `/salud` exigen el token de la variable de entorno `TOKEN_API`, como
cabecera `Authorization: Bearer <token>` (en `/docs`, botón «Authorize»).
"""

import hashlib
import json
import os
import secrets
import sys
from pathlib import Path

# La segmentación usa la clase Recorte de src/cartera/segmentacion.py (solo código, sin datos)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import joblib
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator

CARPETA_MODELOS = Path(os.environ.get("CARPETA_MODELOS", Path(__file__).resolve().parents[1] / "modelos"))
ARCHIVO = CARPETA_MODELOS / "modelo_B.joblib"
FICHA = json.loads((CARPETA_MODELOS / "modelo_B.json").read_text(encoding="utf-8"))

MODELO = joblib.load(ARCHIVO)
SHA256 = hashlib.sha256(ARCHIVO.read_bytes()).hexdigest()
if SHA256 != FICHA["sha256"]:
    raise RuntimeError("modelo_B.joblib no corresponde a su ficha: no es el modelo verificado")

NUM = FICHA["predictoras_numericas"]
CAT = FICHA["predictoras_categoricas"]
CATEGORIAS = FICHA["categorias"]

ARCHIVO_A = CARPETA_MODELOS / "segmentacion_A.joblib"
FICHA_A = json.loads((CARPETA_MODELOS / "segmentacion_A.json").read_text(encoding="utf-8"))
SEGMENTACION = joblib.load(ARCHIVO_A)  # usa cartera.segmentacion.Recorte (src/ en la ruta)
if hashlib.sha256(ARCHIVO_A.read_bytes()).hexdigest() != FICHA_A["sha256"]:
    raise RuntimeError("segmentacion_A.joblib no corresponde a su ficha")
VARIABLES_A = FICHA_A["variables"]

TOKEN = os.environ.get("TOKEN_API")
if not TOKEN:
    raise RuntimeError("Falta la variable de entorno TOKEN_API")

app = FastAPI(
    title="Score de pago tardío (componente B)",
    version="1.0",
    description=(
        "Regresión logística sin `class_weight`, el modelo final del informe, ajustada con las "
        "facturas de 2022-01 a 2025-06. Devuelve la probabilidad de que cada factura se pague con "
        "más de 30 días de atraso. **La probabilidad ordena bien, pero en la prueba quedó corta** "
        "(subestima cuando sube la proporción de tardías): sirve para priorizar, no para leerla al "
        "pie de la letra."
    ),
)
_bearer = HTTPBearer(auto_error=False)


def exigir_token(cred: HTTPAuthorizationCredentials | None = Depends(_bearer)):
    if cred is None or not secrets.compare_digest(cred.credentials.encode(), TOKEN.encode()):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token ausente o incorrecto",
                            headers={"WWW-Authenticate": "Bearer"})


class Factura(BaseModel):
    """Las 11 predictoras de una factura, tal como las calcula `src/cartera/` el día de emisión."""

    referencia: str | None = Field(None, max_length=40,
                                   description="Etiqueta libre para reconocer el caso (nunca un NIT ni un id de la compañía)")
    plazo_dias_observado: int = Field(ge=0, le=3650, description="Vencimiento menos emisión, en días")
    log_monto_inicial: float = Field(description="Logaritmo natural del valor inicial de la factura")
    fecha_mes: int = Field(ge=1, le=12, description="Mes de emisión")
    atraso_prom_hist: float | None = Field(None, description="Atraso promedio de las facturas pagadas antes de la emisión; nulo si no hay")
    n_pagadas_hist: int = Field(ge=0, description="Facturas del cliente pagadas antes de la emisión")
    saldo_abierto_t: float = Field(description="Saldo del cliente en facturas el día de emisión")
    n_abiertas_t: int = Field(ge=0, description="Facturas del cliente abiertas el día de emisión")
    n_vencidas_t: int = Field(ge=0, description="De esas, cuántas ya habían vencido")
    antiguedad_dias: float = Field(ge=0, description="Días desde la primera factura del cliente")
    unidad_negocio: str = Field(description="Una de: " + ", ".join(CATEGORIAS["unidad_negocio"]))
    tipo_cliente: str = Field(description="Una de: " + ", ".join(CATEGORIAS["tipo_cliente"]))
    saldo: float | None = Field(None, ge=0, description="Opcional: saldo de la factura, para ordenar por probabilidad × saldo")

    @field_validator("unidad_negocio", "tipo_cliente")
    @classmethod
    def categoria_conocida(cls, v, info):
        if v not in CATEGORIAS[info.field_name]:
            raise ValueError(f"categoría desconocida; use una de {CATEGORIAS[info.field_name]}")
        return v


class Solicitud(BaseModel):
    facturas: list[Factura] = Field(min_length=1, max_length=500)


class Resultado(BaseModel):
    referencia: str | None
    probabilidad_pago_tardio: float
    monto_en_riesgo: float | None = Field(description="Probabilidad × saldo, si se envió el saldo")


class Cliente(BaseModel):
    """Perfil de pago del cliente (7 variables de `src/cartera/segmentacion.py`), con su ventana."""

    referencia: str | None = Field(None, max_length=40,
                                   description="Etiqueta libre para reconocer el caso (nunca un NIT)")
    atraso_mediano: float = Field(description="Atraso mediano de sus facturas pagadas, en días")
    atraso_iqr: float = Field(ge=0, description="Rango intercuartílico del atraso, en días")
    pct_tardias: float = Field(ge=0, le=100, description="% de facturas con más de 30 días de atraso")
    facturas_por_anio: float = Field(ge=0, description="Facturas emitidas por año")
    log_monto_mediano: float = Field(description="Logaritmo del monto mediano de sus facturas")
    pct_varios_abonos: float = Field(ge=0, le=100, description="% de facturas pagadas con más de un RC")
    pct_cierre_nota: float = Field(ge=0, le=100, description="% de facturas cerradas con notas o ajustes")


class SolicitudA(BaseModel):
    clientes: list[Cliente] = Field(min_length=1, max_length=500)


class ResultadoA(BaseModel):
    referencia: str | None
    segmento: str
    accion_C: str
    dias_hasta_el_pago_del_segmento: dict
    aviso_C: str


PAGINA_DEMO = (Path(__file__).with_name("demo.html").read_text(encoding="utf-8")
               .replace("__CATEGORIAS__", json.dumps(CATEGORIAS, ensure_ascii=False)))


@app.get("/", include_in_schema=False)
def inicio():
    return RedirectResponse("/demo")


@app.get("/demo", response_class=HTMLResponse, include_in_schema=False)
def demo():
    """Página visual con formulario. No trae datos: las llamadas que hace exigen el token."""
    return PAGINA_DEMO


@app.get("/salud")
def salud():
    """Sin token: confirma que el servicio está arriba y qué archivos de modelo sirve."""
    return {"estado": "ok", "modelo": FICHA["modelo"], "sha256": SHA256,
            "segmentacion": FICHA_A["modelo"], "sha256_segmentacion": FICHA_A["sha256"]}


@app.post("/segmentar", response_model=list[ResultadoA], dependencies=[Depends(exigir_token)])
def segmentar(solicitud: SolicitudA):
    """Segmento de A de cada cliente y lo que C propone para ese segmento.

    Válido para clientes con al menos 5 facturas pagadas, con el perfil calculado en la misma
    ventana que formó los segmentos (2022-01 a 2025-06).
    """
    filas = [c.model_dump() for c in solicitud.clientes]
    grupo = SEGMENTACION.predict(pd.DataFrame(filas)[VARIABLES_A])
    salida = []
    for f, g in zip(filas, grupo):
        nombre = FICHA_A["cluster_a_segmento"][str(int(g))]
        politica = FICHA_A["politica_C"][nombre]
        salida.append(ResultadoA(referencia=f["referencia"], segmento=nombre, accion_C=politica["accion"],
                                 dias_hasta_el_pago_del_segmento=politica["dias_hasta_el_pago"],
                                 aviso_C=FICHA_A["aviso_C"]))
    return salida


def _leer_casos():
    """Casos de la demostración (`datos_crudos/casos_demo.json`), si se configuraron.

    No están en la imagen ni en el repo. En Azure llegan como secreto (variable `CASOS_DEMO`, con el
    JSON); en local, como archivo montado de solo lectura (variable `CASOS_DEMO_ARCHIVO`).
    """
    texto = os.environ.get("CASOS_DEMO")
    archivo = os.environ.get("CASOS_DEMO_ARCHIVO")
    if not texto and archivo and Path(archivo).is_file():
        texto = Path(archivo).read_text(encoding="utf-8")
    return json.loads(texto) if texto else None


CASOS = _leer_casos()


@app.get("/casos", dependencies=[Depends(exigir_token)], include_in_schema=False)
def casos():
    """Casos preparados para llenar el formulario de /demo. Exigen el token, como toda ruta con datos."""
    if CASOS is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No hay casos configurados")
    return {"B": [{"caso": c["caso"], "desenlace_real": c["desenlace_real"],
                   "factura": c["cuerpo"]["facturas"][0]} for c in CASOS["B"]],
            "A": [{"caso": c["caso"], "despues_de_2025_06": c["despues_de_2025_06"],
                   "cliente": c["cuerpo"]["clientes"][0]} for c in CASOS["A"]]}


@app.get("/modelo", dependencies=[Depends(exigir_token)])
def modelo():
    """Ficha del modelo: predictoras, categorías, versiones y la verificación contra el cuaderno."""
    return {k: v for k, v in FICHA.items() if k != "contenido"}


@app.post("/predecir", response_model=list[Resultado], dependencies=[Depends(exigir_token)])
def predecir(solicitud: Solicitud):
    """Probabilidad de pago tardío de cada factura.

    Si todas traen `saldo`, el resultado se ordena por probabilidad × saldo (como la lista diaria
    del informe); si no, por probabilidad.
    """
    filas = [f.model_dump() for f in solicitud.facturas]
    X = pd.DataFrame(filas)[NUM + CAT].astype({c: float for c in NUM})
    prob = MODELO.predict_proba(X)[:, 1]
    resultados = [
        Resultado(referencia=f["referencia"], probabilidad_pago_tardio=round(float(p), 4),
                  monto_en_riesgo=None if f["saldo"] is None else round(float(p) * f["saldo"], 2))
        for f, p in zip(filas, prob)
    ]
    con_saldo = all(r.monto_en_riesgo is not None for r in resultados)
    return sorted(resultados, reverse=True,
                  key=lambda r: r.monto_en_riesgo if con_saldo else r.probabilidad_pago_tardio)
