# R17 · Evaluación de la segmentación

> **Proyecto Final Integrador · Machine Learning I · Universidad EAN**
> Fase CRISP-DM: **Evaluación (A)** · Reto acumulativo: **R17**
> Integrantes: **Claudia Naranjo, Yery Pedraza y Nicolás Ruiz** · Última actualización: 2026-10-21

¿Se adopta la segmentación de R15 (K-means con k = 2: «paga a tiempo o casi» y «paga tarde», D-32),
contrastada en R16? Las cifras salen de [`evaluacion_R17.ipynb`](evaluacion_R17.ipynb) (*[§n]*). k,
la preparación y los centros se fijaron en R15, antes de mirar el desenlace. Los datos de la
compañía no están en el repositorio.

## 1. ¿Se reproduce con otra muestra?

Se partieron los 158 clientes de entrenamiento en dos mitades al azar, **20 veces**. Con cada mitad
se ajustó de nuevo la preparación y el agrupamiento, y se comparó cómo asignan los dos modelos a
todos los clientes. La comparación se mide con el índice de Rand ajustado (ARI) *[§1]*:

| Segmentación | ARI mediana | Rango |
|---|---|---|
| **K-means, k = 2 (elegida)** | **0,652** | 0,317 a 0,890 |
| K-means, k = 3 | 0,385 | 0,172 a 0,678 |
| Ward, 2 grupos | 0,456 | 0,097 a 0,870 |

La segmentación elegida es la que mejor se reproduce, y por bastante. Pero no es perfecta: con la
mitad de los clientes, en el peor caso, solo coincide en parte (0,317). Es lo esperable en un
continuo cortado en dos (R16): los clientes cercanos al corte cambian de lado según la muestra.

## 2. ¿Separa algo que importa?

**Desenlace externo:** las facturas de cada cliente emitidas **después** del 1/07/2025, con
desenlace conocido al 18/10/2026, y cuántas fueron tardías (más de 30 días de atraso). Los grupos se
formaron solo con facturas hasta el 30/06/2025, así que este desenlace no se usó para formarlos
*[§2]*.

| Conjunto | Segmento | Clientes | Facturas | Tardías (eventos) | Tasa | IC 95 % (Wilson) |
|---|---|---|---|---|---|---|
| Entrenamiento | Paga a tiempo o casi | 85 | 1.869 | 455 | 24,3 % | 22,5 a 26,3 % |
| Entrenamiento | **Paga tarde** | 23 | 389 | 292 | **75,1 %** | 70,5 a 79,1 % |
| **Prueba** | Paga a tiempo o casi | 36 | 755 | 259 | 34,3 % | 31,0 a 37,8 % |
| **Prueba** | **Paga tarde** | 10 | 227 | 182 | **80,2 %** | 74,5 a 84,8 % |

**Prueba contra el azar.** Las facturas de un mismo cliente no son independientes, así que la prueba
principal es de **permutación por cliente**: se repartió al azar la etiqueta de segmento entre los
clientes 5.000 veces.

| Conjunto | Diferencia de tasas | p por permutación de clientes | Chi cuadrado por factura (complemento) |
|---|---|---|---|
| Entrenamiento | 50,7 puntos | < 0,001 | 371,9 (p < 0,001) |
| Prueba | 45,9 puntos | 0,0006 | 146,6 (p < 0,001) |

## 3. Qué diferencias superan al azar y el límite de los eventos

- **Supera al azar:** la diferencia entre los dos segmentos en la tasa de facturas tardías
  posteriores, en entrenamiento y en prueba. Los intervalos ni se tocan: «paga tarde» se atrasa en
  tres de cada cuatro facturas; «paga a tiempo o casi», en una de cada tres o cuatro.
- **No se puede afirmar con estos datos:** que la diferencia sea exactamente de 46 a 51 puntos, ni
  que valga igual en todas las empresas o unidades.
- **La tasa de los dos segmentos sube en el periodo posterior** (24 → 34 % y 75 → 80 %, de
  entrenamiento a prueba), igual que en B: después de mediados de 2025 hay más tardías en toda la
  cartera. La segmentación ordena bien, pero los niveles cambian con el tiempo.
- **Límite de los eventos.** En la prueba, «paga tarde» tiene 182 eventos, pero solo **10
  clientes**. La prueba por permutación de clientes, la honesta, se apoya en esos 10 y en 36 clientes
  del otro grupo: con tan pocos, un par de clientes atípicos podría mover mucho la diferencia. El chi
  cuadrado por factura da un p mucho menor, pero es optimista, porque cuenta 982 facturas como si
  fueran independientes. Además, 72 clientes (50 de entrenamiento y 22 de prueba) no tienen facturas
  posteriores y no entran en esta validación.

## 4. Mapa con PCA

PCA ajustado solo con el entrenamiento, en el espacio preparado *[§3]*.

| Componente | CP1 | CP2 | CP3 | CP4 | CP5 |
|---|---|---|---|---|---|
| Varianza explicada | 38,7 % | 18,5 % | 13,1 % | 11,9 % | 10,2 % |
| Acumulada | 38,7 % | 57,2 % | 70,3 % | 82,2 % | 92,4 % |

**Cargas:**
- **CP1, «qué tan mal paga».** Pesan casi por igual el atraso mediano (0,56), el % de tardías
  (0,53) y la variabilidad del atraso (0,51). Es el eje que separa los dos segmentos.
- **CP2, «cómo se le factura».** Más facturas por año (0,59) frente a más monto (−0,53) y más cierres
  con notas (−0,52).
- **CP3, abonos y monto:** varios abonos (0,70) y monto (0,63).

**La segmentación vive en el primer eje.** K-means con 2 componentes reproduce la segmentación
original con un ARI de **0,945**, conservando solo el 57 % de la varianza. Las demás variables
(frecuencia, monto, abonos) describen diferencias entre clientes, pero no son las que separan los
segmentos. El mapa describe; la evaluación de §1 y §2 se hizo en el espacio completo de las 7
variables.

## 5. Decisión: adoptar con condiciones

**Se adopta la segmentación**, por tres razones:
- se reproduce mejor que las alternativas;
- anticipa con claridad el comportamiento posterior, también en clientes que no se usaron para
  formarla;
- se explica con un solo eje: qué tan mal paga el cliente.

**Condiciones:**
1. **Se usa para el tono del contacto y para describir la cartera, no como predictor de B** (D-10).
   Acompaña la lista diaria: le dice a la gestora qué tipo de cliente tiene enfrente.
2. **Se recalcula con la historia reciente.** Los niveles de atraso cambian con el tiempo; un cliente
   cerca del corte puede cambiar de segmento.
3. **Los clientes con menos de 5 facturas pagadas quedan como «sin historia suficiente»** (D-09) y no
   se les asigna segmento.

**Lo que cambiaría la decisión:** que, al recalcularla con datos nuevos, la diferencia de tardías
posteriores entre los dos segmentos deje de superar al azar en la prueba por permutación de clientes.
También, que un piloto muestre que tratar distinto a los dos segmentos no cambia nada. En los dos
casos, la segmentación describiría el pasado, pero no serviría para decidir.

**Lo que esta evaluación no prueba:** que pertenecer a «paga tarde» cause el atraso, ni que cambiar
el trato a esos clientes lo reduzca.
