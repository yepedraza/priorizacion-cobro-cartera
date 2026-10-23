"""Lectura de los datos crudos de la compañía (carpeta `datos_crudos/`, fuera de Git)."""

from pathlib import Path

import pandas as pd

# Columnas que empiezan por «fecha» pero son números derivados, no fechas
_DERIVADAS = {"fecha_anio", "fecha_mes", "fecha_trimestre", "fecha_dia_mes",
              "fecha_dia_semana", "fecha_es_fin_de_mes"}


def raiz_proyecto() -> Path:
    """La primera carpeta hacia arriba que contiene `datos_crudos/` (ruta relativa)."""
    return next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "datos_crudos").is_dir())


def leer(nombre: str) -> pd.DataFrame:
    """Lee un CSV de `datos_crudos/` y convierte a fecha las columnas de fecha."""
    df = pd.read_csv(raiz_proyecto() / "datos_crudos" / nombre, encoding="utf-8-sig", low_memory=False)
    for c in df.columns:
        if c.startswith("fecha") and c not in _DERIVADAS:
            df[c] = pd.to_datetime(df[c])
    return df


def leer_todo() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Las dos tablas: (saldos, movimientos)."""
    return leer("saldos_anonimizados.csv"), leer("movimientos_anonimizados.csv")
