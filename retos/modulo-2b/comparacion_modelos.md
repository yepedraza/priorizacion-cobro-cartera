# R13 · Comparación de modelos

> **Proyecto Final Integrador · Machine Learning I · Universidad EAN**
> Fase CRISP-DM: **Modelado** · Reto acumulativo: **R13**
> Integrantes: **Claudia Naranjo, Yery Pedraza y Nicolás Ruiz** · Última actualización: 2026-10-21

Comparación de candidatos para el score de pago tardío (B). Las cifras salen de
[`modelos_R13.ipynb`](modelos_R13.ipynb) (*[§n]*); el diseño se aprobó en D-26. Todo se mide con el
entrenamiento (2022-01 a 2025-06): **la prueba no se usó**.

## 1. Cómo se compara

- **Misma partición y mismas columnas** que en R12: las 11 predictoras de D-24 y D-27 (el grupo se
  trata como una sola empresa: `empresa` no es predictora) y el entrenamiento completo de D-23
  (8.930 facturas, 30,2 % tardías).
- **Validación cruzada agrupada por trimestre**, la unidad de agrupación de R12: 5 pliegues de
  ventana creciente. Cada uno valida un trimestre completo, de 2024-T2 a 2025-T2, y entrena con los
  anteriores, solo con facturas cuyo desenlace ya se conocía cuando empieza el trimestre validado
  (D-17). El cuaderno verifica que ningún trimestre queda en los dos lados *[§1]*.
- **Métrica: AUC-PR** (área bajo la curva de precisión y exhaustividad). Las gestoras pueden atender
  solo 20 clientes por día, así que el modelo sirve si pone arriba las facturas que de verdad se van
  a atrasar. Un falso negativo cuesta días de caja sobre el saldo; un falso positivo, el tiempo de
  una gestora y la incomodidad de un cliente cumplido (`diseno_experimental.md` §7). La AUC-PR mide justo eso, y
  no se infla con el 70 % de facturas a tiempo, como sí lo haría la exactitud.

## 2. Resultados

| Candidato | AUC-PR media | Desv. | AUC-ROC | Segundos por ajuste |
|---|---|---|---|---|
| Línea base (`DummyClassifier`) | 0,309 | 0,007 | 0,500 | 0,01 |
| Árbol de referencia (R12) | 0,665 | 0,030 | 0,801 | 0,01 |
| **Regresión logística** | **0,720** | **0,021** | 0,841 | 0,01 |
| SVM RBF | 0,700 | 0,037 | 0,840 | 0,38 |
| Bosque aleatorio, por defecto | 0,697 | 0,048 | 0,833 | 0,10 |
| Bosque aleatorio, ajustado | 0,719 | 0,049 | 0,842 | 0,37 |
| Gradient boosting, por defecto | 0,700 | 0,041 | 0,835 | 0,62 |
| Gradient boosting, ajustado | 0,720 | 0,043 | 0,845 | 0,41 |

*[§2 y §3]*. Los valores por pliegue están en el cuaderno.

**Búsqueda de hiperparámetros frente al modelo por defecto.** Se probaron 30 combinaciones por
ensamble, con la misma CV y todas las filas (D-22). La búsqueda subió el bosque de 0,697 a 0,719 y el
boosting de 0,700 a 0,720 *[§3]*. Las dos mejoras son menores que la desviación de la CV (0,049 y
0,043): no se distinguen del ruido. Además, la mejor de 30 combinaciones tiende a sobrestimarse.

## 3. Modelo final preliminar: regresión logística

La regla se fijó antes de ver los resultados (D-26): gana el de mejor AUC-PR media; si su mejora
sobre la regresión logística no supera la desviación de la CV, gana la logística *[§4]*.

- La regresión logística tiene la mejor AUC-PR media (0,720, empatada con el boosting ajustado al
  tercer decimal) y la menor desviación (0,021), la mitad que la de los ensambles.
- Los dos ensambles ajustados quedan a menos de 0,002 de ella: es un empate, y en ningún pliegue
  un candidato le gana a la logística por más que la desviación.
- **Ningún modelo más complejo supera a la logística por más que la desviación de la CV**, así que
  la complejidad no se merece el lugar.
- Además, la logística es la más rápida, la más fácil de explicar a cartera y la más estable entre
  trimestres.

Frente a la línea base, la mejora es grande: de 0,309 a 0,720, unas 20 veces la desviación.

## 4. Importancia de las variables

Medida por **permutación en datos no vistos**: la logística se entrena con el subentrenamiento
(2022-01 a 2024-06) y se mide cuánto cae la AUC-PR en la validación de R12 (2024-07 a 2025-06) al
desordenar cada columna. Se agregó una columna de **ruido** como control. Se compara con la
importancia por **impureza** (Gini) de un bosque aleatorio entrenado igual *[§5]*.

| Variable | Permutación (puesto) | Impureza (puesto) |
|---|---|---|
| Atraso promedio histórico | 0,236 (1.º) | 0,217 (1.º) |
| Facturas vencidas el día *t* | 0,108 (2.º) | 0,074 (7.º) |
| Facturas pagadas antes de *t* | 0,066 (3.º) | 0,109 (3.º) |
| Saldo abierto el día *t* | 0,001 (7.º) | 0,113 (**2.º**) |
| Monto inicial | 0,000 (10.º) | 0,100 (**4.º**) |
| **Ruido (control)** | 0,000 (8.º) | 0,086 (**6.º**) |

**Lo que cambia de lugar.** El saldo abierto pasa del 2.º puesto por impureza al 7.º por permutación,
y el monto inicial, del 4.º al 10.º. La prueba de que es un sesgo de la impureza es la columna de
ruido: no tiene ninguna información y aun así la impureza la pone 6.ª, por encima de variables
reales. La impureza favorece a las variables con muchos valores distintos. Por permutación, el ruido
da casi cero, como debe ser. Lo que el modelo usa de verdad es el historial de pago del cliente,
sobre todo su atraso promedio y si ya está atrasado con otras facturas. Ninguna importancia indica
causa.

## 5. Grupo al que el modelo podría perjudicar

Con un cupo declarado: se marca el 30 % de las facturas de validación con mayor puntaje (≈ la
proporción de tardías). La **tasa de falsos negativos** es la parte de las tardías de cada grupo que
el modelo dejó pasar *[§6]*.

| Grupo | Facturas | Tardías | % marcadas | Exhaustividad | Falsos negativos |
|---|---|---|---|---|---|
| Empresa A | 2.374 | 764 | 31,4 % | 0,683 | 31,7 % |
| **Empresas B, C y D** | 287 | 57 | 18,5 % | 0,386 | **61,4 %** |
| Clientes con 4 o menos facturas pagadas | 281 | 87 | 52,3 % | 0,759 | 24,1 % |
| Clientes con 5 o más | 2.380 | 734 | 27,4 % | 0,651 | 34,9 % |
| Todas | 2.661 | 821 | 30,0 % | 0,663 | 33,7 % |

- **Empresas B, C y D:** el modelo deja pasar el 61,4 % de sus facturas tardías, casi el doble que
  en la Empresa A. Son solo el 11 % de las facturas, tienen menos tardías (19,9 % frente a 32,2 %) y el
  modelo aprende sobre todo de la Empresa A: con un mismo cupo para todas, a sus facturas les toca
  menos. Las perjudicadas son esas empresas del grupo: su cartera tardía recibe menos seguimiento. Quitar
  `empresa` de las predictoras (D-27) no lo corrige: con `empresa`, la tasa también era 61,4 %; solo
  sube un poco la parte de sus facturas que se marca (de 14,6 % a 18,5 %).
- **Clientes con poca historia:** reciben el error contrario. Se marca más de la mitad de sus facturas (52,3 %),
  aunque su proporción de tardías (31 %) es como la del resto, así que reciben más presión de cobro
  de la que merecen. Es el riesgo que R12 vio en el árbol.

R14 vuelve a medir estos grupos con el modelo final y su calibración, y el informe los declara como
límite.
