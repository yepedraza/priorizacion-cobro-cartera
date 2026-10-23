# R14 · Informe de avance: cierre del Módulo 2B

> **Proyecto Final Integrador · Machine Learning I · Universidad EAN**
> Fases CRISP-DM: **Comprensión del negocio y de los datos, preparación y modelado** · Reto acumulativo: **R14**
> Integrantes: **Claudia Naranjo, Yery Pedraza y Nicolás Ruiz** · Enfoque: **intraemprendimiento** · Última actualización: 2026-10-21

Este informe consolida el proyecto hasta el modelado del score de pago tardío (componente B). Cada
sección resume un reto y enlaza su artefacto, donde están el detalle y el cálculo.

| Reto | Artefactos |
|---|---|
| R10 · Negocio | [`anteproyecto_PFI.md`](anteproyecto_PFI.md), [`viabilidad_R10.ipynb`](viabilidad_R10.ipynb) |
| R11 · Datos | [`ficha_datos.md`](ficha_datos.md), [`diagnostico_R11.ipynb`](diagnostico_R11.ipynb) |
| R12 · Preparación | [`diseno_experimental.md`](diseno_experimental.md), [`preparacion_R12.ipynb`](preparacion_R12.ipynb) |
| R13 · Modelado | [`comparacion_modelos.md`](comparacion_modelos.md), [`modelos_R13.ipynb`](modelos_R13.ipynb) |
| R14 · Red y cierre | Este informe, [`red_R14.ipynb`](red_R14.ipynb) |

## 1. Problema y decisión (R10)

La compañía, un grupo empresarial colombiano de servicios, cobra sus facturas unos **22 días
después de lo pactado**: el plazo ponderado es de 21 días y el dinero llega, en promedio, a los 43.
Cada día menos de recaudo equivale a ≈ **$65 M** en caja. Las dos gestoras de cartera pueden dar
seguimiento personalizado a **20 clientes por día**, de unos 135 con facturas vencidas en un día
típico, y hoy los eligen por saldo y vencimiento, sin mirar qué tan probable es que cada cliente se
atrase.

- **Decisión que se apoya:** a qué 20 clientes dedicar el seguimiento cada día. Deciden las gestoras;
  el controller supervisa.
- **Solución (componente B):** un modelo estima, al emitir cada factura, la probabilidad de que se
  pague más de 30 días después de vencer. La lista diaria ordena a los clientes por probabilidad ×
  saldo.
- **Métrica de negocio:** monto en riesgo capturado con el mismo cupo de 20 clientes, frente a la
  regla actual, en un backtest. Es distinta de la métrica técnica (§4).
- **Enfoque:** intraemprendimiento: una mejora para el área de cartera de la propia compañía.

## 2. Datos (R11)

| Aspecto | Detalle |
|---|---|
| Fuente | ERP de la compañía, anonimizado por ella; uso autorizado por escrito para este proyecto, sin licencia pública |
| Fecha de corte y de acceso | 2026-10-18 |
| Tablas | Saldos (19.262 filas, 54 columnas) y movimientos (40.519 filas, 44 columnas) |
| Unidad de observación | La **factura** (17.920 de los 19.262 saldos) |
| Objetivo | `tardia` = 1 si la factura se pagó más de 30 días después de vencer |

**El objetivo se construye**, no viene en la base (`src/cartera/etiqueta.py`):
- El atraso se mide hasta que entra el dinero: hasta el último recibo de caja (RC), no hasta que el
  saldo queda en cero.
- Quedan sin etiqueta 1.284 facturas cerradas sin ningún RC y 103 que se pagaron con RC menos del
  90 % de su valor.
- Solo se usan facturas que ya tuvieron 30 días para resolverse después de vencer.

Así quedan 15.822 facturas cerradas con etiqueta, con **32,84 % de pago tardío**.

**Calidad.** No hay duplicados ni variantes de escritura en las categorías. Los faltantes están solo
en columnas posteriores a la emisión, que no entran al modelo. La peor es `dias_mora_actual`
(96 %), que falta justo cuando el saldo está en cero: es un faltante estructural. Una SVM RBF tarda
≈ 1,5 s con todo el entrenamiento posible, así que la búsqueda de hiperparámetros usa todas las
filas de entrenamiento.

## 3. Diseño experimental sin fuga (R12)

- **Unidad de agrupación:** el **trimestre de emisión**, no el cliente. El modelo se usa con los
  mismos clientes, que se repiten mes a mes, y su información principal es su propio historial.
- **Partición temporal** (corte el 1/07/2025): entrenamiento de 2022-01 a 2025-06 (8.930 facturas) y prueba de
  2025-07 a 2026-09 (3.970), **todavía sin usar**. Dentro del entrenamiento, el subentrenamiento va
  hasta 2024-06 y la validación es de 2024-07 a 2025-06. En cada corte solo entran facturas cuyo
  desenlace ya se conocía, y el cuaderno verifica que ningún trimestre queda en dos conjuntos.
- **11 predictoras**, todas conocidas al emitir la factura:
  - De la factura: plazo, monto inicial, mes, unidad de negocio y tipo de cliente.
  - Del historial del cliente antes de la emisión: atraso promedio, facturas pagadas, saldo abierto,
    facturas abiertas y vencidas, y antigüedad.
  - Una prueba automática recalcula el historial fila por fila y da lo mismo en los 1.800 valores
    revisados.

**Columnas excluidas y su motivo:**

| Motivo | Columnas |
|---|---|
| Derivadas del objetivo | «% de facturas con más de 30 días», segmento de A (filtrarían la etiqueta), `dias_hasta_cancelacion` |
| No disponibles antes de la decisión | Cancelación, créditos, saldo y estado al corte, recaudos, días de mora, tipo de cierre |
| Calculadas con el periodo que se predice | Cualquier historial con facturas posteriores a la emisión |
| Pueden cambiar después de la emisión | `total_debitos`, `codigo_cuenta` |
| Identificadores | `nit_cliente`, `cliente`, `id_*` |
| Uso descartado por el proyecto | `nombre_vendedor` y `empresa`: el grupo se trata como una sola empresa; las dos se usan solo para auditar |
| Sin información o redundantes | `condicion_pago_inferida`, `cuota`, `fecha_radicacion`, actividad sintética, vencimiento |

**Árbol de referencia:** 6 niveles y 36 hojas, elegido en validación como el más pequeño a menos de
0,01 de la mejor AUC-PR. Brecha frente al subentrenamiento: 0,011. Lo domina el atraso
promedio histórico del cliente.

## 4. Comparación de candidatos (R13)

Validación cruzada agrupada por trimestre, con 5 pliegues de ventana creciente (2024-T2 a 2025-T2).
La métrica es la **AUC-PR**: con un cupo fijo, lo que importa es poner arriba las facturas que se van
a atrasar, y la exactitud se inflaría con el 70 % de facturas a tiempo.

| Candidato | AUC-PR media ± desv. | Segundos por ajuste |
|---|---|---|
| Línea base (`DummyClassifier`) | 0,309 ± 0,007 | 0,01 |
| Árbol de referencia (R12) | 0,665 ± 0,030 | 0,01 |
| **Regresión logística** | **0,720 ± 0,021** | 0,01 |
| SVM RBF | 0,700 ± 0,037 | 0,38 |
| Bosque aleatorio (ajustado) | 0,719 ± 0,049 | 0,37 |
| Gradient boosting (ajustado) | 0,720 ± 0,043 | 0,41 |

La búsqueda de hiperparámetros mejoró los ensambles respecto a su versión por defecto (0,697 →
0,719 y 0,700 → 0,720), pero dentro de la desviación. **Ningún candidato supera a la regresión
logística por más que la desviación de la CV**, así que por la regla fijada de antemano la logística es el
modelo final preliminar de R13. Por permutación en datos no vistos, lo que usa el modelo es el
historial: el atraso promedio, las facturas vencidas y las facturas pagadas. Una columna de ruido
muestra el sesgo de la importancia por impureza, que la pone 6.ª cuando por permutación da cero.

## 5. Red neuronal (R14)

**Diseño** (*[Red §1]*): un perceptrón multicapa (`MLPClassifier`, optimizador Adam).
- Mismas 11 predictoras, mismos 5 pliegues y misma métrica que R13.
- Imputación, escala y codificación dentro del `Pipeline`, ajustadas solo con el entrenamiento de
  cada pliegue. La escala es necesaria porque la red aprende por gradientes y, sin ella, el saldo
  dominaría.
- Las tardías pesan más (pesos de muestra «balanceados»), como en los demás candidatos.
- **Sin parada temprana automática:** la de scikit-learn separa su validación al azar por fila y
  mezclaría trimestres. El número de épocas se eligió con los pliegues.

**Tabla de sensibilidad** *[Red §2]*. Desde una base (una capa de 32 neuronas, α = 0,001, 100
épocas), se cambió un factor a la vez, con 3 semillas en los 5 pliegues:

| Factor | Valor | AUC-PR media | Desv. entre semillas | Desv. entre pliegues |
|---|---|---|---|---|
| Base | 32 neuronas, α = 0,001, 100 épocas | 0,721 | 0,002 | 0,035 |
| Épocas | 25 / 50 / 200 | 0,725 / 0,726 / 0,715 | ≤ 0,005 | ≈ 0,035 |
| Capacidad | 8 neuronas / dos capas (64 y 32) | 0,723 / **0,696** | 0,002 / 0,009 | 0,035 / 0,049 |
| Regularización α | 0,0001 / 0,01 / **1** | 0,721 / 0,721 / **0,731** | ≤ 0,003 | ≈ 0,035 |

**Lo que más pesó fue la capacidad**: mueve la AUC-PR media en 0,027, frente a 0,011 de las épocas y
0,010 de la regularización. Una red más grande (dos capas) empeora y se vuelve más inestable entre
semillas; con estos datos, más capacidad lleva a memorizar. Lo mismo indican las épocas: 200 dan
menos que 50. La mejor configuración es la base con regularización fuerte (α = 1).

**Red elegida con 5 semillas** (2026 a 2030) *[Red §3]*: **AUC-PR 0,730**, con desviación de 0,002
entre semillas y de 0,035 entre pliegues; ≈ 0,3 s por ajuste.

## 6. Modelo final preliminar del módulo

Regla fijada antes de ver resultados, como en la comparación de modelos: la red reemplaza a la regresión logística
solo si su mejora supera la variación entre semillas **y** la variación entre pliegues *[Red §4]*.

| | Valor |
|---|---|
| Red elegida, AUC-PR media | 0,730 |
| Regresión logística, mismos pliegues | 0,720 |
| Mejora de la red | 0,009 |
| Variación entre semillas | 0,002 |
| Variación entre pliegues | 0,035 |

La red le gana a la logística en 4 de 5 pliegues, y su mejora supera la variación entre semillas.
Pero **no supera la variación entre pliegues**: según el trimestre que se valide, la AUC-PR de un
mismo modelo cambia casi cuatro veces más que la ventaja de la red. Por eso, **el modelo final
preliminar del módulo sigue siendo la regresión logística**. La decisión se tomó sin mirar la
prueba.

La red tampoco compensa su costo: entrena unas 30 veces más lento, depende de la semilla y es más
difícil de explicar a cartera que una logística, cuyos coeficientes se leen como «más atraso
histórico, más riesgo».

## 7. A quién podría perjudicar

Cupo declarado: se marca el 30 % de las facturas de validación (2024-07 a 2025-06) con mayor
puntaje, ≈ la proporción de tardías. El monto es el valor inicial de la factura; es aproximado,
porque los montos están escalados *[Red §5]*.

| Grupo | Tardías | Falsos negativos: logística | Falsos negativos: red | Monto tardío no marcado: logística |
|---|---|---|---|---|
| Empresa A | 764 | 31,9 % | 31,4 % | 28,2 % de $3.734 M |
| **Empresas B, C y D** | 57 | **61,4 %** | **59,6 %** | **58,6 % de $202 M** |
| Clientes con 4 o menos facturas pagadas | 87 | 24,1 % | 35,6 % | 19,8 % de $666 M |
| Clientes con 5 o más | 734 | 35,1 % | 33,1 % | 31,8 % de $3.271 M |
| Todas | 821 | 34,0 % | 33,4 % | 29,8 % de $3.937 M |

- **Empresas B, C y D.** Los dos modelos dejan pasar alrededor del 60 % de sus facturas tardías y
  del dinero tardío, el doble que en la Empresa A. Tratar el grupo como una sola empresa no
  lo corrige: tienen menos tardías (19,9 %) y el modelo aprende de la Empresa A, que tiene el 89 %
  de los datos. En dinero, son ≈ $119 M de los $1.173 M tardíos que la logística no marca (10 %).
  Su cartera tardía recibe menos seguimiento, y se declara como límite.
- **Clientes con poca historia.** La logística los marca de más: marca el 52,3 % de sus facturas,
  aunque solo el 31 % es tardía, igual que en el resto (`comparacion_modelos.md` §5). La red, en cambio, les deja pasar más tardías (35,6 % frente a 24,1 %).
  Cambiar de modelo cambia a quién le toca el error.

*Nota:* en R13 la logística de la auditoría se entrenó con la columna de ruido de control, así que
sus tasas difieren en décimas de las de esta tabla (por ejemplo, 31,7 % frente a 31,9 % en la
Empresa A).

## 8. Lo que sigue

- **Calibración y umbral por capacidad:** la probabilidad del modelo final se va a multiplicar por
  el saldo, así que tiene que estar calibrada.
- **Prueba y backtest, una sola vez:** con el modelo final ya elegido, se mide en la prueba
  (2025-07 a 2026-09) el monto en riesgo capturado por la lista de 20 clientes, frente a las dos
  líneas base de negocio.
- **Segmentación (A) y plazo por segmento (C)**, en el Módulo 3.
