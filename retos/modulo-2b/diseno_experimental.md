# R12 · Diseño experimental sin fuga

> **Proyecto Final Integrador · Machine Learning I · Universidad EAN**
> Fase CRISP-DM: **Preparación de los datos** · Reto acumulativo: **R12**
> Integrantes: **Claudia Naranjo, Yery Pedraza y Nicolás Ruiz** · Última actualización: 2026-10-21

Cómo se evalúa el score de pago tardío (B). Las cifras salen de
[`preparacion_R12.ipynb`](preparacion_R12.ipynb) (*[§n]*). Todo se mide en **validación**: la prueba
se consulta una sola vez, al final del proyecto.

## 1. Unidades y partición

- **Unidad de observación:** la factura (`id_saldo`).
- **Unidad de agrupación:** el **trimestre de emisión**. El cliente no es el grupo: el modelo se usa
  con los mismos clientes, que se repiten mes a mes, y su información principal es su propio
  historial. Agrupar por cliente mediría clientes nuevos, que no es el uso real (D-18). Por eso
  ningún identificador del cliente entra como predictor.
- **Partición temporal** (D-23), con la regla de desenlace conocido aplicada en cada corte: solo
  entran facturas que ya tuvieron 30 días después de vencer en la fecha en que termina su conjunto
  (D-17).

| Conjunto | Emisión | Facturas | Trimestres |
|---|---|---|---|
| Subentrenamiento | 2022-01 a 2024-06 | 5.972 | 10 |
| Validación | 2024-07 a 2025-06 | 2.661 | 4 |
| Prueba (sin usar) | 2025-07 a 2026-09 | 3.970 | 5 |

El cuaderno verifica que ningún trimestre ni ninguna factura queda en dos conjuntos y que la regla
de desenlace conocido se cumple en cada corte *[§1]*. **Límite:** la etiqueta de 112 facturas de
entrenamiento (1,25 %) usa un cierre posterior al corte; su desenlace ya estaba decidido, pero su
exclusión por cierres sin pago (D-16 y D-20) depende de ese cierre.

## 2. Variables

**Predictoras** (D-24 y D-27), 11, todas conocidas el día de emisión *t*. El grupo se trata como una
sola empresa: `empresa` no es predictora (D-27).

| Variable | Fuente |
|---|---|
| Plazo, mes de emisión, unidad de negocio, tipo de cliente | Tabla de saldos |
| Monto inicial (log del primer débito) | Tabla de movimientos, `src/cartera/muestra.py` |
| Atraso promedio histórico, facturas pagadas, saldo abierto, facturas abiertas y vencidas el día *t*, antigüedad del cliente | Historial antes de *t*, `src/cartera/historial.py` |

El historial se calcula solo con hechos estrictamente anteriores a *t*. Una prueba automática lo
recalcula fila por fila para 300 facturas y da exactamente lo mismo en los 1.800 valores (D-11)
*[§2]*.

**Excluidas:**

| Motivo | Columnas |
|---|---|
| Derivadas del objetivo | «% de facturas con más de 30 días», segmento de A (D-10); `dias_hasta_cancelacion` |
| No disponibles antes de la decisión | Todas las (P): cancelación, créditos, saldo y estado al corte, recaudos, días de mora, tipo de cierre |
| Calculadas con el periodo que se predice | Cualquier historial con facturas posteriores a *t* |
| Pueden cambiar después de la emisión | `total_debitos` (se usa el débito inicial), `codigo_cuenta` |
| Identificadores | `nit_cliente`, `cliente`, `id_*`: el modelo memorizaría al cliente |
| Uso que el proyecto descartó | `nombre_vendedor`: daría reglas por vendedor (D-02); `empresa`: el grupo se trata como una sola empresa (D-27). Las dos se usan solo para auditar errores |
| Sin información o redundantes | `condicion_pago_inferida`, `cuota`, `fecha_radicacion`, actividad sintética, vencimiento y sus derivadas |

**Sensibles:** ninguna; la compañía anonimizó todo el conjunto.

## 3. Línea base y modelo de referencia

Entrenados con el subentrenamiento y medidos en validación (30,9 % de tardías) *[§3]*:

| Modelo | AUC-PR | AUC-ROC |
|---|---|---|
| Línea base (predice siempre la proporción) | 0,309 | 0,500 |
| Regla simple: ordenar por atraso promedio histórico | 0,673 | 0,799 |
| **Regresión logística** (modelo de referencia) | **0,724** | **0,844** |
| Árbol de referencia (§4) | 0,668 | 0,810 |

La AUC-PR mide qué tan bien se ponen las facturas tardías por encima de las demás y, a diferencia
de la exactitud, no se infla con la clase minoritaria. El historial del cliente es lo que mueve el
resultado: sin él, en R10, el mejor modelo llegaba a 0,351.

## 4. Árbol de referencia

- **Poda elegida en validación:** se probaron profundidades de 2 a 10 y sin límite, y mínimos de 20,
  50 y 100 facturas por hoja. Regla: el árbol con menos hojas cuya AUC-PR en validación está a menos
  de 0,01 de la mejor (0,673) *[§4]*.
- **Árbol elegido:** profundidad 6, mínimo 50 facturas por hoja, **36 hojas**.
- **Brecha:** AUC-PR 0,679 en subentrenamiento y 0,668 en validación (brecha 0,011): casi no
  memoriza. Un árbol sin límite llega a 0,811 en subentrenamiento y cae a 0,609 en validación. La
  brecha frente a la prueba se reporta una sola vez, al final (consulta al docente pendiente).
- **Qué usa:** el atraso promedio histórico concentra el 56 % de la importancia, seguido de las
  facturas vencidas el día *t* (19 %) y las facturas ya pagadas (15 %).

**Una regla, interpretada.** *Si el cliente pagó en promedio con más de 32,8 días de atraso, tiene
106 facturas pagadas o menos, ya tenía 2 o más facturas vencidas el día de emisión y el plazo es de
más de 31,5 días, el árbol predice pago tardío.* En lenguaje de cartera: a un cliente que suele
pagar tarde, que ya está atrasado con otras facturas y al que se le da un plazo largo, el modelo lo
marca como riesgo. Describe lo que usa el modelo, no la causa del atraso.

**A quién podría perjudicar.**
- **Clientes que mejoraron.** El atraso promedio pesa igual toda la historia: un cliente que pagaba
  tarde en 2022 y hoy paga a tiempo sigue arrastrando su promedio y recibe más presión de cobro de
  la que merece.
- **Clientes con poca historia.** Otra rama marca como tardía la factura de un cliente sin facturas
  vencidas, con 4 o menos facturas pagadas y fuera de la Unidad 01, si su atraso promedio pasa de
  1,8 días: con tan pocos datos, un par de pagos algo tardíos basta para señalarlo.

Se mitiga porque la gestora decide (el modelo prioriza, no sanciona) y porque R14 mide la
exhaustividad por grupo, incluidos estos dos.
