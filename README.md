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

## Contexto académico

Proyecto Final Integrador del curso Machine Learning I, Maestría en Gerencia en IA.
