# R16 · Contraste de la segmentación: DBSCAN y jerárquico

> **Proyecto Final Integrador · Machine Learning I · Universidad EAN**
> Fase CRISP-DM: **Modelado (A)** · Reto acumulativo: **R16**
> Integrantes: **Claudia Naranjo, Yery Pedraza y Nicolás Ruiz** · Última actualización: 2026-10-21

¿La segmentación de R15 (K-means con k = 2: «paga a tiempo o casi» y «paga tarde», D-32) depende del
algoritmo? Las cifras salen de [`contraste_R16.ipynb`](contraste_R16.ipynb) (*[§n]*). Los datos de
la compañía no están en el repositorio.

## 1. Mismo punto de partida y parámetros

Los tres algoritmos usan **la misma partición y la misma preparación de R15**: los 158 clientes de
entrenamiento, con el recorte de extremos y la escala aprendidos solo con ellos *[§1]*.

| Algoritmo | Parámetros |
|---|---|
| K-means (R15) | k = 2, 50 reinicios, semilla 2026 |
| DBSCAN | `min_samples = 8` (número de variables + 1); `eps = 2,99`, el percentil 90 de las k-distancias, en el codo de la curva; distancia euclidiana |
| Jerárquico | Enlaces de Ward y promedio, distancia euclidiana, sobre los 158 clientes sin submuestra (por eso no necesita semilla); corte en 2 grupos |

Ninguna etiqueta ni desenlace se usó para elegir `eps`, el enlace o el corte.

## 2. DBSCAN

El gráfico de k-distancias (distancia de cada cliente a su 8.º vecino, ordenada) crece despacio y se
dispara en el último 10 %: ahí está el codo *[§2]*.

| Percentil de las k-distancias | eps | Grupos | % ruido | Tamaño del grupo |
|---|---|---|---|---|
| 50 | 1,39 | 1 | 36,1 % | 101 |
| 70 | 1,82 | 1 | 18,4 % | 129 |
| 80 | 2,21 | 1 | 10,8 % | 141 |
| **90** | **2,99** | **1** | **3,8 %** | **152** |
| 95 | 3,65 | 1 | 0,6 % | 157 |

**Con ningún eps aparecen dos grupos densos:** DBSCAN ve una sola masa de clientes y, a su alrededor,
clientes aislados que va llamando ruido. Con el eps elegido, el ruido son **6 clientes (3,8 %)**.
Como hay un solo grupo, la silueta sin ruido no está definida.

## 3. Jerárquico

En Ward, la última fusión (de 2 grupos a 1) ocurre a una altura de 22,56, frente a 14,66 de la
anterior: un salto de 7,89, el mayor de todos. Cortar ahí da **2 grupos** (109 y 49 clientes) *[§3]*.

En el enlace promedio no hay un salto así: sus últimas fusiones solo van sumando, uno o pocos a la
vez, clientes aislados al grupo principal. Cortado en 2, separa un grupo de **7 clientes** del resto
(151). Es lo típico de ese enlace cuando los datos no forman grupos compactos: aísla atípicos.

## 4. Comparación

| Comparación | ARI |
|---|---|
| K-means frente a Ward | **0,641** |
| K-means frente a enlace promedio | 0,187 |
| K-means frente a DBSCAN (ruido como grupo) | 0,160 |
| Ward frente a DBSCAN | 0,096 |

**Tablas cruzadas** *[§4]*:
- **K-means y Ward:** de los 120 clientes de «paga a tiempo o casi», Ward pone 107 en un mismo
  grupo; de los 38 de «paga tarde», 36 en el otro. Ward agrega a «paga tarde» 13 clientes de la
  frontera.
- **Enlace promedio:** sus 7 clientes aislados son todos de «paga tarde».
- **DBSCAN:** su ruido (6 clientes) es todo de «paga tarde»; los otros 152 forman un solo grupo.

**Qué reaparece y qué solo existe en uno:**
- **La división en dos de K-means reaparece en Ward**, el otro método que busca grupos compactos, con
  un ARI de 0,64. No es un efecto de K-means.
- **DBSCAN y el enlace promedio no la ven:** para ellos no hay dos zonas densas, sino una masa
  continua con una cola de clientes que pagan muy tarde.
- **Lo que solo aparece fuera de K-means es esa cola:** 6 o 7 clientes que DBSCAN llama ruido y el
  enlace promedio aísla. Es el mismo tipo de cliente que el tercer grupo de k = 3, que en R15 no se
  sostuvo al cambiar el mínimo de facturas.

**Qué índice se parece a lo que se ve en los tamaños.** La silueta de K-means es 0,353 y la de Ward
0,277: valores bajos, que indican grupos que se tocan. Coincide con lo que muestran DBSCAN (una sola
masa con 3,8 % de ruido) y el enlace promedio (151 clientes contra 7). Los clientes no forman islas
separadas, sino un continuo de «paga bien» a «paga mal»; K-means y Ward lo cortan en dos, y el corte
es útil y estable, pero es un corte en un continuo.

## 5. Perfil del ruido

Medianas en unidades originales *[§5]*:

| Grupo | Clientes | Atraso mediano | Rango del atraso | % tardías | % varios abonos | % cierres con nota |
|---|---|---|---|---|---|---|
| K-means: paga a tiempo o casi | 120 | 9,0 | 14,0 | 10,4 | 0,0 | 7,1 |
| K-means: paga tarde | 38 | 51,5 | 50,0 | 81,3 | 2,4 | 11,8 |
| **DBSCAN: ruido** | **6** | **104,0** | **152,0** | 82,1 | 7,9 | **35,1** |
| Enlace promedio: grupo chico | 7 | 103,0 | 151,0 | 80,8 | 7,5 | 33,3 |

El ruido son clientes que **pagan muy tarde y de forma muy irregular**: el doble de atraso mediano
que «paga tarde» y el triple de variabilidad. Además, **un tercio de sus facturas se cierra con
notas o ajustes**. Facturan igual que los demás.

## 6. Lo que el contraste no prueba

Que varios algoritmos coincidan en separar a «paga tarde», y que dos aíslen a los muy tardíos, dice
que esa estructura está en los datos de entrenamiento, no que exista fuera de ellos ni que tenga una
causa común. Tampoco se sabe qué pasa con esos 6 clientes: el contraste no dice que vayan a pagar
peor ni que deban recibir otro tratamiento. R17 mide si los grupos se reproducen y si anticipan el
comportamiento posterior.
