# R12 · Diseño experimental sin fuga

> **Proyecto Final Integrador · Machine Learning I · Universidad EAN**
> Fase CRISP-DM: **Preparación de los datos** · Reto acumulativo: **R12**
> Integrantes: **Claudia Naranjo, Yery Pedraza y Nicolás Ruiz** · Última actualización: 2026-10-22

Cómo se evalúa el score de pago tardío (B). Las cifras salen de
[`preparacion_R12.ipynb`](preparacion_R12.ipynb) (*[§n]*). Todo se mide en **validación**: la prueba
se consulta una sola vez, al final del proyecto.

Desde el 22/10/2026 este documento reúne también las definiciones, las reglas contra la fuga y las
métricas del proyecto (§5 a §7), que antes estaban en el anteproyecto (§6 a §8). Allí quedaron
resumidas para cumplir el largo de R10.

## 1. Unidades y partición

- **Unidad de observación:** la factura (`id_saldo`).
- **Unidad de agrupación:** el **trimestre de emisión**. El cliente no es el grupo: el modelo se usa
  con los mismos clientes, que se repiten mes a mes, y su información principal es su propio
  historial. Agrupar por cliente mediría clientes nuevos, que no es el uso real; por eso se agrupa por bloque de tiempo. Por eso
  ningún identificador del cliente entra como predictor.
- **Partición temporal** (corte el 1/07/2025, bloques trimestrales), con la regla de desenlace conocido aplicada en cada corte: solo
  entran facturas que ya tuvieron 30 días después de vencer en la fecha en que termina su conjunto.

| Conjunto | Emisión | Facturas | Trimestres |
|---|---|---|---|
| Subentrenamiento | 2022-01 a 2024-06 | 5.972 | 10 |
| Validación | 2024-07 a 2025-06 | 2.661 | 4 |
| Prueba (sin usar) | 2025-07 a 2026-09 | 3.970 | 5 |

El cuaderno verifica que ningún trimestre ni ninguna factura queda en dos conjuntos y que la regla
de desenlace conocido se cumple en cada corte *[§1]*. **Límite:** la etiqueta de 112 facturas de
entrenamiento (1,25 %) usa un cierre posterior al corte; su desenlace ya estaba decidido, pero su
exclusión por cierres sin pago o con RC parcial depende de ese cierre.

## 2. Variables

**Predictoras**, 11, todas conocidas el día de emisión *t*. El grupo se trata como una
sola empresa: `empresa` no es predictora.

| Variable | Fuente |
|---|---|
| Plazo, mes de emisión, unidad de negocio, tipo de cliente | Tabla de saldos |
| Monto inicial (log del primer débito) | Tabla de movimientos, `src/cartera/muestra.py` |
| Atraso promedio histórico, facturas pagadas, saldo abierto, facturas abiertas y vencidas el día *t*, antigüedad del cliente | Historial antes de *t*, `src/cartera/historial.py` |

El historial se calcula solo con hechos estrictamente anteriores a *t*. Una prueba automática lo
recalcula fila por fila para 300 facturas y da exactamente lo mismo en los 1.800 valores
*[§2]*.

**Excluidas:**

| Motivo | Columnas |
|---|---|
| Derivadas del objetivo | «% de facturas con más de 30 días», segmento de A (filtrarían la etiqueta); `dias_hasta_cancelacion` |
| No disponibles antes de la decisión | Todas las (P): cancelación, créditos, saldo y estado al corte, recaudos, días de mora, tipo de cierre |
| Calculadas con el periodo que se predice | Cualquier historial con facturas posteriores a *t* |
| Pueden cambiar después de la emisión | `total_debitos` (se usa el débito inicial), `codigo_cuenta` |
| Identificadores | `nit_cliente`, `cliente`, `id_*`: el modelo memorizaría al cliente |
| Uso que el proyecto descartó | `nombre_vendedor`: daría reglas por vendedor; `empresa`: el grupo se trata como una sola empresa. Las dos se usan solo para auditar errores |
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

## 5. Definiciones

| Concepto | Definición | Aclaración / por qué importa |
|---|---|---|
| Factura | Saldo cuyo documento de origen es una factura electrónica (`FEV`/`FVE`; columna `es_deuda_facturada = True`) | Excluye saldos nacidos de notas, ajustes o saldos iniciales, que no son ventas |
| Vencimiento | Fecha límite de pago de la factura (`fecha_vencimiento`) | El plazo es la diferencia entre el vencimiento y la emisión |
| Atraso de una factura | Días entre el vencimiento y la fecha del **último recibo de caja (RC)** que la pagó (`fecha_cancelacion_registrada − fecha_vencimiento` cuando el saldo cerró con un RC). Negativo = pago anticipado | Se mide hasta cuándo entra el dinero, no hasta que contabilidad deja el saldo en cero: una nota o un ajuste no es dinero que entra. Si el pago llegó en varios abonos, cuenta el último |
| **Pago tardío (variable objetivo de B)** | Vale 1 si el atraso es **mayor que 30 días** y 0 si no | Criterio de la compañía: reporta su cartera por edades de mora, y a partir de 30 días la considera en mora que exige gestión; así lo confirma el controller |
| Desenlace conocido | Se sabe si la factura fue o no un pago tardío. Solo entran las facturas con `fecha_vencimiento + 30 ≤ fecha_corte`, es decir, que ya tuvieron 30 días para resolverse: si están pagadas, con su atraso; si siguen abiertas, son tardías | Solo estas facturas sirven para entrenar y evaluar. Una factura vencida hace 10 días todavía puede pagarse a tiempo o no: su desenlace es desconocido y se excluye. Exigir los 30 días evita que las semanas más recientes, que son la prueba, queden solo con facturas pagadas a tiempo |
| Facturas excluidas de B | (1) Las de plazo negativo, que son un error de registro (vencimiento anterior a la emisión; 245 saldos *[`viabilidad_R10.ipynb` §7]*). (2) Las de desenlace desconocido. (3) Las cerradas **sin ningún RC**: se cerraron con nota o ajuste y no describen un pago. (4) Las **mixtas** (pagadas con RC y cerradas después con nota o ajuste) cuyo RC cubre **menos del 90 % del valor**, porque la mayor parte se cerró sin dinero | Evita aprender de datos erróneos o incompletos. Las excluidas por cierre sin pago siguen en el perfil de A como frecuencia de cierres con notas o ajustes |
| Facturas mixtas | Facturas pagadas con RC y cerradas después con una nota o un ajuste | Se miden hasta el último RC, siempre que el RC cubra al menos el 90 % del valor. El 90 % es un criterio del equipo: con 80 % y con 95 % el porcentaje de pago tardío no cambia (32,86 % y 32,84 %) |
| Unidad de análisis de A | El **cliente** (`nit_cliente`), con al menos 5 facturas pagadas (cerradas con etiqueta) entre las emitidas de 2022-01 a 2025-06: **226 clientes** (`retos/modulo-3/segmentacion_R15.md`). La cifra inicial de 329 *[`viabilidad_R10.ipynb` §3]* contaba toda la historia y la definición anterior de «pagada» | Con menos de 5 no hay suficiente historia para describir cómo paga; esos clientes quedan en un grupo "sin historia suficiente". La ventana es la misma del entrenamiento de B, y lo posterior se reserva para evaluar la segmentación (R17) |
| Unidad de análisis de B | La **factura** (`id_saldo`) | El riesgo se estima por factura y luego se suma por cliente para armar la lista |
| **K = 20 clientes por día** | Número de clientes a los que las dos gestoras pueden dar seguimiento personalizado en un día de trabajo (llamada, registro y seguimiento) | Es la capacidad real del equipo. Define el tamaño de la lista diaria y es el **umbral de decisión** del modelo: no se elige una probabilidad de corte arbitraria, sino a los 20 más prioritarios. También se reporta qué pasaría con 10 y con 40 |
| Regla actual (línea base principal) | Ordenar a los clientes con facturas vencidas por saldo vencido, de mayor a menor | Es la **línea base**: lo que la solución tiene que superar. No lleva desempate por vencimiento, porque los saldos casi nunca empatan y no cambiaría la lista |
| Segunda línea base | Ordenar a los clientes por su saldo vencido en facturas con **entre 1 y 30 días de mora**, de mayor a menor | Junta las dos mitades del criterio del área («saldo más alto» y «próxima a 30 días») sin inventar pesos, y compite por el mismo dinero en duda que el modelo (§7). Trata igual una factura de 5 días que una de 28 |

## 6. Reglas para no engañarnos

Un modelo puede parecer excelente en las pruebas y fallar en la vida real si durante su construcción
"ve" información que no tendría al momento de usarse. Eso se llama **fuga de información**. Estas
reglas la evitan:

1. **Solo información disponible al momento de predecir.** El diccionario de datos
   (`datos_crudos/diccionario-datos.md`, confidencial y fuera de Git) marca con **(P)** las columnas
   que solo se conocen *después* de emitir la factura o que describen su estado a la fecha de corte.
   Esas columnas **no se usan** para predecir, y el historial de cada cliente se calcula solo con
   facturas pagadas antes del día de la factura que se evalúa. El detalle está en §2.
2. **Partición temporal.** El modelo se entrena con las facturas más antiguas y se prueba con las más
   recientes cuyo desenlace ya se conoce; en la validación cruzada los bloques respetan el orden del
   tiempo. Una partición al azar mezclaría facturas futuras en el entrenamiento. El corte, los bloques
   y la unidad de agrupación están en §1. Además, la regla de desenlace conocido (§5) se aplica **en
   cada corte**, en cada pliegue y en el final. *Límite declarado:* los resultados valen para
   clientes con historial, no para clientes nuevos.
3. **Periodo de estudio: desde 2022.** En 2020 y 2021, el **43 %** de las facturas pagadas se pagó
   con más de 30 días de atraso, frente a entre el **31 % y el 34 %** de cada año desde 2022 (2026 va
   en 31 %, aunque el año aún no termina) *[`viabilidad_R10.ipynb` §3]*. Ese cambio, probablemente
   asociado a la pandemia, muestra que en esos años los clientes se comportaron distinto. Entrenar
   con ellos enseñaría al modelo un patrón que ya no se observa.
4. **Las transformaciones se ajustan solo con el conjunto de entrenamiento.** Algunos pasos de
   preparación "aprenden" de los datos: por ejemplo, la estandarización calcula la media y la
   desviación de cada variable, y la imputación calcula la mediana para llenar vacíos. Si esos valores
   se calculan con todos los datos, información del conjunto de prueba se filtra al modelo y su
   desempeño parece mejor de lo que es. Por eso todos esos pasos van dentro de un **Pipeline** de
   scikit-learn y se ajustan solo con entrenamiento.
5. **El desbalance se trata solo en entrenamiento.** Solo una de cada tres facturas es tardía, así
   que el modelo podría inclinarse a predecir siempre "no tardía". En la comparación de modelos se
   probó darle más peso a las tardías en el entrenamiento, pero **el modelo final no usa pesos**: inflaban las probabilidades, y la lista diaria multiplica probabilidad × saldo, así que
   necesita probabilidades que se parezcan a la realidad. Sin pesos, la regresión logística ordena
   igual y queda mejor calibrada. El desbalance se atiende de otra forma: con métricas que no se
   engañan con él (AUC-PR, §7) y con un cupo fijo de 20 clientes por día en lugar de un umbral de
   0,5. El conjunto de prueba **no se toca**, porque debe reflejar la proporción real con la que el
   modelo se encontrará en la práctica.
6. **El conjunto de prueba se usa una sola vez, al final.** Si se consultara varias veces para elegir
   entre modelos o ajustar parámetros, se terminaría escogiendo el modelo que mejor le funciona *a ese
   conjunto en particular*, y la cifra final sería optimista. Todas las comparaciones se hacen con
   validación sobre entrenamiento; la prueba solo confirma el modelo ya elegido.
7. **Reproducibilidad.** Los cuadernos fijan una **semilla aleatoria**, única para todo el proyecto
   (`SEMILLA = 2026`, en `src/cartera/config.py`), imprimen las **versiones** de Python y de las
   librerías, y usan **rutas relativas** a la carpeta del proyecto, de modo que corren igual en el
   computador de cualquier integrante o del profesor.

## 7. Métricas, líneas base y backtest

**Líneas base.** Cada día, se arman dos listas de 20 clientes sin modelo:
- **Principal, la regla actual:** los 20 con mayor saldo vencido (§5).
- **Segunda, de sensibilidad:** los 20 con mayor saldo vencido en facturas de 1 a 30 días de mora
  (§5). Es la comparación más exigente: compite por el mismo dinero en duda que el modelo, así que
  superarla es superar a las gestoras en su propio terreno.

Superar dos reglas razonables es una prueba más fuerte que superar una sola.

| Nivel | Métrica | Qué significa | Para qué |
|---|---|---|---|
| **Negocio (principal)** | Monto en riesgo capturado con el mismo K, **solo sobre el dinero con desenlace todavía incierto** | De todo el dinero de ese día que terminó pagándose con más de 30 días de atraso y que aún no estaba decidido (facturas no vencidas o vencidas hace 30 días o menos), qué porcentaje estaba en la lista de 20 clientes. Se compara la lista del modelo con las dos líneas base | Demostrar que la lista del modelo dirige mejor el esfuerzo de las gestoras |
| Negocio | Días de recaudo (DSO) y su equivalente en caja | Cuántos días tarda la empresa en cobrar; cada día menos libera ≈ $65 M (anteproyecto §2) | Traducir la mejora a dinero |
| Técnica · B | AUC-PR (área bajo la curva de precisión y recall) | Qué tan bien el modelo pone las facturas tardías por encima de las demás. Es más exigente que la exactitud cuando la clase de interés es minoritaria, como aquí | Comparar y elegir modelos |
| Técnica · B | Precisión y recall en el top-K | De las facturas de la lista, cuántas eran tardías (precisión); de todas las tardías, cuántas entraron a la lista (recall) | Medir el desempeño en el punto donde se toma la decisión |
| Técnica · B | Calibración | Si el modelo dice "70 %", ¿se atrasa realmente cerca del 70 % de esas facturas? | Que la probabilidad se pueda leer y multiplicar por el saldo |
| Técnica · A | Silueta, Davies-Bouldin y estabilidad | Qué tan separados y compactos son los segmentos, y si se mantienen al repetir el análisis con submuestras de clientes | Elegir el número y el tipo de segmentos |
| Técnica · A | Interpretabilidad | Que cada segmento se pueda describir en lenguaje de cartera y tenga un tratamiento claro | Que el resultado sea útil, no solo matemáticamente correcto |

**Cómo se mide la métrica principal (backtest).** Se simula qué habría pasado en el pasado. Para cada
día hábil del periodo de prueba se reconstruye la cartera vencida de ese día y se arman las listas de
20 clientes: una con cada línea base y otra con el modelo. Como hoy ya se sabe cómo terminó cada
factura, se mide qué parte del dinero que terminó pagándose con más de 30 días de atraso estaba en
cada lista. Gana la que capture más con los mismos 20 cupos. *Simplificación declarada:* el riesgo se
estima al emitir la factura y no se recalcula con los días que ya lleva vencida.

*Por qué solo el dinero en duda.* El día *t*, una factura vencida hace más de 30 días ya es
tardía: su desenlace está decidido y no hay nada que anticipar. Contarla premiaría a la regla que
mira el tablero, no a quien anticipa. Por eso el denominador incluye solo facturas no vencidas o
vencidas hace 30 días o menos, y el dinero en duda solo se cuenta si su factura cumple la regla de
desenlace conocido (§5), de modo que el periodo termina antes de la fecha de corte. Se descartó medir
«saldo × días de atraso», porque supone que la llamada acorta el atraso, algo que no se puede
verificar sin registros de gestión.

*Tabla complementaria.* Con las mismas listas, el resultado se reporta también contando **todo** el
dinero, con una columna de «dinero ya tardío que tenía la lista». Es secundaria: reconoce la
alternativa descartada y muestra que la métrica se fijó antes de ver resultados. *Consecuencia
esperable:* con esta tabla la regla principal puede captar más, porque parte de su lista ya era
dinero tardío; no se lee como el resultado principal.

**Costo de cada tipo de error (B).**
- **Falso negativo:** una factura que sí se iba a atrasar y el modelo no la priorizó. Cuesta días de
  caja sobre su saldo.
- **Falso positivo:** una factura que se iba a pagar bien y el modelo la priorizó. Cuesta el tiempo de
  una gestora y la incomodidad de un cliente cumplido.

Como la capacidad es fija (20 clientes), el umbral no es una probabilidad elegida arbitrariamente,
sino el **top-K**: se gestionan los 20 de mayor prioridad.

**Familias de modelos** (la rúbrica exige al menos tres, bajo el mismo diseño experimental):
- **B:** línea base (regla actual), regresión logística, árboles y ensambles, y al menos otra familia
  vista en el curso; los hiperparámetros se eligen con validación (`comparacion_modelos.md`).
- **A:** K-means, contrastado con DBSCAN y agrupamiento jerárquico; PCA para visualizar los
  segmentos (`retos/modulo-3/`).
