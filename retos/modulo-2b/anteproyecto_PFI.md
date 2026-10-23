# R10 · Planteamiento del problema de negocio y de la solución

> **Proyecto Final Integrador · Machine Learning I (IMPN0004) · Universidad EAN**
> Fase CRISP-DM: **Comprensión del negocio** · Reto acumulativo: **R10 (anteproyecto)**
> Integrantes: **Claudia Naranjo, Yery Pedraza y Nicolás Ruiz**
> Última actualización: 2026-10-22

Las cifras salen de [`viabilidad_R10.ipynb`](viabilidad_R10.ipynb) (*[Cuaderno §n]*). Las
definiciones, las reglas contra la fuga y las métricas completas están en
[`diseno_experimental.md`](diseno_experimental.md) §5 a §7.

**Enfoque: intraemprendimiento.** Una mejora para el área de cartera de la propia compañía.
**Propuesta de valor:** una lista diaria que les dice a las dos gestoras a qué 20 clientes contactar
primero, ordenada por el dinero con mayor riesgo de pagarse con más de 30 días de atraso, para cobrar
antes con la misma capacidad. **Ruta de validación:** el backtest (§5) y un piloto con grupo de
comparación (§4, C).

## 1. Contexto y problema

La compañía es un grupo colombiano de servicios (cuatro empresas, once unidades de negocio) que
vende a crédito, sobre todo a empresas. Su cartera la gestionan **2 gestoras**, supervisadas por un
**controller**. Hoy hay un correo automático semanal a cada cliente con saldo pendiente (no incluye
facturas por vencer, según una gestora) y las gestoras eligen en un tablero a quién llamar por
**saldo más alto y vencimiento más próximo**: la factura vencida que está por cumplir 30 días de
mora. Alcanzan unos **20 clientes por día**.

En un día típico de 2025 había **135 clientes con facturas vencidas** *[Cuaderno §6]*: el equipo
llega al 15 %. El dinero entra **≈ 22 días después de lo pactado** (43 días reales frente a 21
pactados, ponderados por monto *[Cuaderno §2]*). El 96 % de los saldos termina en cero
*[Cuaderno §5]*: el problema no es la cartera incobrable, sino la **velocidad** con que se cobra.

## 2. Decisión y métricas de éxito

| Pregunta | Respuesta |
|---|---|
| ¿Qué se decide? | A qué 20 clientes dedicar el seguimiento humano **hoy**, y con qué tratamiento |
| ¿Quién decide? | Las gestoras; el controller supervisa |
| ¿Con qué frecuencia? | Todos los días hábiles |
| ¿A quién afecta? | Clientes (presión de cobro), gestoras (su tiempo) y finanzas (cuándo entra el dinero) |
| **Métrica de negocio** | Del dinero que aún estaba en duda y terminó pagándose con más de 30 días de atraso, qué parte estaba en la lista de 20, frente a la regla actual (mayor saldo vencido); solo cuenta el dinero que el día *t* aún tenía el desenlace incierto. Se traduce a caja con los días de recaudo: cada día menos libera **≈ $65 M**, lo que se factura en un día *[Cuaderno §2]* |
| Métrica técnica | AUC-PR, precisión y recall en el top-20, calibración |

**Hipótesis de mejora.** Con la misma capacidad, priorizar por *riesgo de pago tardío × saldo* y
por tipo de cliente recupera más dinero, o antes, que la regla actual.

## 3. Primer indicio de viabilidad

Facturas de 2022 a 2024 con desenlace conocido; **partición por fecha antes de transformar**:
entrenamiento 2022–2023, validación 2024 (2.820 facturas, 30,2 % tardías). Variables provisionales
conocidas al emitir: plazo, monto inicial, mes, empresa y unidad de negocio *[Cuaderno §9]*.

| Modelo | AUC-PR en validación |
|---|---|
| Línea base (predice siempre la proporción de tardías) | 0,302 |
| Naive Bayes gaussiano | 0,321 |
| KNN (k = 25) | **0,351** |

La AUC-PR no se infla con la clase minoritaria, a diferencia de la exactitud. Los dos superan a la
línea base por poco: sin el historial del cliente, la factura sola dice poco. Con el historial,
calculado sin fuga, la regresión logística llegó a 0,724 en R12.

## 4. Solución

Se evaluaron diez enfoques; se eligieron tres:

| Componente | Qué responde | Técnica | Para quién |
|---|---|---|---|
| **A · Segmentación** (enfoque 1) | ¿Qué tipos de pagadores hay? Por atraso típico y su variación, % > 30 días, frecuencia y monto, abonos y cierres con notas | No supervisado: K-means, contrastado con DBSCAN y jerárquico | Cartera: tono y tratamiento del contacto |
| **B · Score de pago tardío** (enfoques 2 y 3) | Probabilidad de que una factura se pague más de 30 días después del vencimiento. **Uso 1:** lista diaria por Σ probabilidad × saldo. **Uso 2:** alerta al facturar | Supervisado: 11 predictoras conocidas al emitir, de la factura y del historial del cliente; `empresa` no es predictora porque el grupo se trata como una sola empresa | Gestoras, cada mañana |
| **C · Plazo real y gestión por segmento** (enfoque 6) | Cuánto tarda de verdad cada segmento en pagar y si el plazo mueve el pago, **comparando a cada cliente consigo mismo**; diseño de un piloto de gestión por segmento (aviso automático antes del vencimiento a quien paga a tiempo o casi; contacto apenas vence a quien paga tarde), con clientes asignados al azar | Política sugerida, no un modelo: el plazo se presenta como hipótesis a probar con el piloto y el aviso previo es automático | Controller y dirección financiera |

C no es un modelo porque el plazo no se asignó al azar: se negoció con cada cliente, y los mejores
pagadores probablemente recibieron más plazo. Por eso su efecto solo se mide con el piloto.

**Fuera de alcance o descartados:** proyección de recaudo, alerta de deterioro, anomalías en cierres
y trayectorias de pago (no cambian a quién se cobra); desempeño por vendedor (riesgo ético de
perjudicar a trabajadores); aprendizaje por refuerzo (no hay registros de las acciones de cobro).

## 5. Diseño, en resumen

- **Unidad y objetivo de B:** la factura; pago tardío = atraso hasta el último recibo de caja mayor
  que 30 días, con el atraso medido hasta el último pago con recibo de caja, y solo con desenlace conocido
  (facturas vencidas hace al menos 30 días a la fecha de corte).
- **Partición temporal:** entrenamiento 2022-01 a 2025-06, prueba 2025-07 a 2026-09, bloques por
  trimestre, con corte el 1/07/2025. La prueba se consulta **una sola vez**.
- **Sin fuga:** solo columnas conocidas al emitir; el historial, solo con facturas anteriores; toda
  transformación dentro de un `Pipeline`; semilla 2026.
- **Backtest:** cada día hábil de la prueba se arman tres listas de 20 (regla actual, segunda línea
  base y modelo) y se mide cuál capturó más dinero tardío en duda.

## 6. Datos

| Aspecto | Detalle |
|---|---|
| Fuente | ERP de la compañía: tablas de saldos (19.262 filas) y movimientos (40.519), 2019-12 a 2026-10, 648 clientes *[Cuaderno §1]* |
| Autorización | Escrita, de la compañía, para este proyecto académico; datos anonimizados de forma irreversible |
| Fecha de acceso | 2026-10-18 |
| Confidencialidad | `datos_crudos/` fuera de Git, salvo su `LEEME.md` |
| Ficha completa | [`ficha_datos.md`](ficha_datos.md) (R11) |

## 7. Riesgos y alcance

| Riesgo | Mitigación |
|---|---|
| **Fuga:** usar columnas que solo se conocen después de emitir, o historial calculado con el futuro | Lista de columnas (P) excluidas y prueba automática del historial (el atraso promedio se recalcula solo con facturas pagadas antes de la emisión) |
| **Sesgo:** el 89 % de los saldos es de la Empresa A; el modelo puede servir peor a B, C y D | Reportar el desempeño por empresa y no generalizar sin evidencia |
| Un cliente cumplido recibe cobro insistente | El modelo prioriza, la gestora decide; el tono lo define el segmento |
| Leer el plazo de C como causa | Presentarlo como hipótesis y validarlo con el piloto |
| Un cambio de comportamiento, como el de 2020–2021, deja desactualizado el modelo | Revisar y reentrenar si la proporción anual de facturas con más de 30 días de atraso sale del rango reciente (31–34 %) |
| Profecía autocumplida: los clientes no priorizados se deterioran | Mantener el correo semanal para todos y vigilar a los no priorizados |

**No-objetivos:** reemplazar el tablero, medir el efecto de las llamadas (no hay registros),
proyectar flujo de caja, predecir incobrables, evaluar a vendedores o gestoras.

## 8. Entregables y bonos

Entrega el **22/10/2026, 11:59 p. m.**; sustentación el **24/10/2026**. Bonos reclamados: **datos
reales** (+5: ficha, autorización, APA 7, cómo obtener los datos), **intraemprendimiento** (+5:
propuesta de valor, hipótesis, impacto ≈ $65 M por día de recaudo, piloto y sección de
microcredenciales) y **modelo desplegado** (+5: aplicación privada durante la sustentación).
