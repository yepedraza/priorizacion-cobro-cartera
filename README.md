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

## Trazabilidad: de cada reto a su fase CRISP-DM

Cada reto deja un documento y, cuando corresponde, un cuaderno. Todos usan el mismo código de `src/cartera/`.

| Reto | Qué avanza | Fase CRISP-DM | Artefactos |
|---|---|---|---|
| R10 | Problema y decisión, enfoque elegido, métrica de negocio, riesgos y viabilidad con KNN y Naive Bayes | Comprensión del negocio | [`anteproyecto_PFI.md`](retos/modulo-2b/anteproyecto_PFI.md), [`viabilidad_R10.ipynb`](retos/modulo-2b/viabilidad_R10.ipynb) |
| R11 | Ficha de datos y diagnóstico de calidad, con la etiqueta y los cierres sin pago | Comprensión de los datos | [`ficha_datos.md`](retos/modulo-2b/ficha_datos.md), [`diagnostico_R11.ipynb`](retos/modulo-2b/diagnostico_R11.ipynb) |
| R12 | Partición temporal, variables y prueba anti-fuga, árbol de referencia | Preparación | [`diseno_experimental.md`](retos/modulo-2b/diseno_experimental.md), [`preparacion_R12.ipynb`](retos/modulo-2b/preparacion_R12.ipynb) |
| R13 | Comparación de candidatos con validación cruzada agrupada y modelo final preliminar | Modelado y evaluación | [`comparacion_modelos.md`](retos/modulo-2b/comparacion_modelos.md), [`modelos_R13.ipynb`](retos/modulo-2b/modelos_R13.ipynb) |
| R14 | Red neuronal, auditoría por grupo e informe de avance del Módulo 2B | Modelado | [`informe_avance_M2B.md`](retos/modulo-2b/informe_avance_M2B.md), [`red_R14.ipynb`](retos/modulo-2b/red_R14.ipynb) |
| R15 | Segmentación de clientes con K-means | Modelado | [`segmentacion_R15.md`](retos/modulo-3/segmentacion_R15.md), [`kmeans_R15.ipynb`](retos/modulo-3/kmeans_R15.ipynb) |
| R16 | Contraste de la segmentación con DBSCAN y agrupamiento jerárquico | Modelado | [`contraste_R16.md`](retos/modulo-3/contraste_R16.md), [`contraste_R16.ipynb`](retos/modulo-3/contraste_R16.ipynb) |
| R17 | Evaluación de la segmentación: estabilidad y desenlace posterior | Evaluación | [`evaluacion_R17.md`](retos/modulo-3/evaluacion_R17.md), [`evaluacion_R17.ipynb`](retos/modulo-3/evaluacion_R17.ipynb) |
| R18 | Cierre: riesgos, plan de seguimiento, esquema de la sustentación y resumen en inglés | Despliegue y cierre | [`cierre_R18.md`](retos/modulo-3/cierre_R18.md) |

Las piezas de la entrega final recorren la cadena completa:

| Pieza | Fase CRISP-DM | Archivo |
|---|---|---|
| Evaluación del modelo B: prueba consultada una sola vez, calibración y backtest | Evaluación | [`evaluacion_B.ipynb`](entrega/evaluacion_B.ipynb) |
| Plazo real por segmento y diseño del piloto (componente C) | Modelado | [`plazo_C.ipynb`](entrega/plazo_C.ipynb) |
| Cuaderno final: corre de principio a fin y reproduce las cifras del informe | Todas | [`cuaderno_PFI.ipynb`](entrega/cuaderno_PFI.ipynb) |
| Informe y resumen ejecutivo en inglés | Todas | [`informe_PFI.md`](entrega/informe_PFI.md), [`resumen_ejecutivo_EN.pdf`](entrega/resumen_ejecutivo_EN.pdf) |
| Anexos: enfoque y datos reales | Comprensión del negocio y de los datos | [`anexo_A_enfoque.md`](entrega/anexo_A_enfoque.md), [`anexo_B_datos_reales.md`](entrega/anexo_B_datos_reales.md) |

## Contexto académico

Proyecto Final Integrador del curso Machine Learning I, Maestría en Gerencia en IA.
