# Proyecto Final Integrador — Machine Learning I

Proyecto de machine learning que recorre el ciclo CRISP-DM completo sobre datos reales: de la pregunta de negocio al modelo desplegado, con cada decisión documentada y defendible.

## Enfoque

El trabajo sigue las seis fases de CRISP-DM:

1. **Comprensión del negocio:** qué decisión apoya el modelo, quién la toma y cómo se mide el éxito.
2. **Comprensión de los datos:** procedencia, licencia, calidad y representatividad.
3. **Preparación:** limpieza y transformación dentro de un diseño experimental sin fuga.
4. **Modelado:** comparación contra una línea base con validación cruzada.
5. **Evaluación:** métricas elegidas según el costo de cada error, variabilidad y umbral justificado.
6. **Despliegue:** el mismo modelo final, con sus límites y un plan de seguimiento.

## Principios

- **Datos reales:** sin datos sintéticos en lugar de los datos reales.
- **Sin fuga de datos:** la partición se hace antes de transformar, todo el preprocesamiento vive en un `Pipeline` y el conjunto de prueba se consulta una sola vez.
- **Reproducibilidad:** semilla y versiones declaradas, rutas relativas y un cuaderno que corre desde un núcleo reiniciado.
- **Transparencia:** todo uso de IA queda registrado (herramienta, prompt, qué se aceptó y qué se descartó).

## Estructura del repositorio

```
├── retos/
│   ├── modulo-2b/          R10–R14: un documento y un cuaderno por reto
│   └── modulo-3/           R15–R18: segmentación, contraste, evaluación y cierre
├── src/cartera/            código compartido: carga de datos, etiqueta, historial del cliente y backtest
├── entrega/                piezas exclusivas de la entrega final: cuaderno, informe, resumen en inglés y anexos
├── modelos/                modelo final guardado (Pipeline completo) y su hash
├── app/                    servicio de despliegue (FastAPI + Docker)
├── scripts/                utilidades, como el empaquetado del zip de la entrega
├── datos_crudos/           datos de la compañía; fuera de Git salvo LEEME.md, que explica cómo obtenerlos
├── declaracion_IA.md       registro de uso de IA de cada integrante
└── requirements.txt        versiones exactas del entorno (Python 3.14.5)
```

- **Los nombres de los retos son los de Canvas**, para que cada artefacto se ubique sin buscarlo. Por ejemplo, R10 son `retos/modulo-2b/anteproyecto_PFI.md` y `viabilidad_R10.ipynb`.
- **Los datos no están en el repositorio.** Son confidenciales y su uso está autorizado solo para este proyecto. Los cuadernos los buscan en `datos_crudos/` con rutas relativas.
- **La preparación vive en `src/cartera/`** y no se copia entre cuadernos, de modo que los retos, el cuaderno final y la aplicación usan exactamente la misma etiqueta y las mismas variables.
- **Cada documento existe una sola vez.** Por ejemplo, la ficha de datos vive en R11 y el script de `scripts/` la copia al zip.

## Contexto académico

Proyecto Final Integrador del curso Machine Learning I, Maestría en Gerencia en IA.
