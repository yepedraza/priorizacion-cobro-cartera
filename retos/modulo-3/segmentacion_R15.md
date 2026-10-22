# R15 · Segmentación de clientes con K-means

> **Proyecto Final Integrador · Machine Learning I · Universidad EAN**
> Fase CRISP-DM: **Modelado (A)** · Reto acumulativo: **R15**
> Integrantes: **Claudia Naranjo, Yery Pedraza y Nicolás Ruiz** · Última actualización: 2026-10-21

Tipos de cliente según cómo pagan (componente A del anteproyecto §5), con el diseño de D-31. Las
cifras salen de [`kmeans_R15.ipynb`](kmeans_R15.ipynb) (*[§n]*). Los datos de la compañía no están
en el repositorio.

## 1. Datos, variables y columnas excluidas

- **Unidad:** el cliente con al menos 5 facturas pagadas (D-09). Las pagadas son las cerradas con
  etiqueta según D-16 y D-20.
- **Ventana:** facturas emitidas de 2022-01 a 2025-06 con desenlace conocido al 1/07/2025, la misma
  del entrenamiento de B. Lo posterior se reserva para evaluar la segmentación en R17.
- **Clientes:** 226 *[§1]*. La cifra de 329 de D-09 venía de la definición anterior de «pagada» y de
  toda la historia.

**Siete variables**, todas de cómo paga el cliente (anteproyecto §5, A):

| Variable | Qué mide |
|---|---|
| Atraso mediano | Qué tan tarde suele pagar |
| Rango intercuartílico del atraso | Qué tan variable es ese atraso |
| % de facturas con más de 30 días | Proporción de pagos tardíos |
| Facturas por año | Con qué frecuencia se le factura |
| Monto mediano (log) | Cuánto se le factura |
| % pagadas con varios abonos | Si suele pagar con abonos parciales |
| % cerradas con notas o ajustes | Cierres sin pago (D-16) |

**Excluidas:**

| Columnas | Motivo |
|---|---|
| Identificadores (`nit_cliente`, `cliente`, `id_*`) | El algoritmo no debe distinguir clientes por su código |
| `empresa`, `nombre_vendedor` | El grupo se trata como una sola empresa (D-27); no se juzga a los vendedores (D-02) |
| Todo lo posterior al 1/07/2025 | Es el desenlace externo de R17 |
| Puntaje del modelo B | La segmentación debe describir a los clientes por sí misma |

## 2. Partición y preparación

- **Partición:** los clientes se separaron al azar **antes** de transformar nada, con la semilla
  2026: 158 para entrenamiento y 68 para prueba.
- **Preparación:** el recorte de extremos (percentiles 1 y 99) y la escala estándar se aprendieron
  solo con el entrenamiento, dentro de un `Pipeline` *[§2]*.

**Sin preparar frente a preparado** *[§3]*. Con k = 2:
- Sin preparar, los grupos tienen 123 y 35 clientes; preparado, 120 y 38.
- Cambió poco porque, en unidades originales, las variables de atraso tienen las desviaciones más
  grandes (≈ 32 a 34) y dominan la distancia en los dos casos. El monto (0,8) y los abonos (7) casi
  no pesaban sin escalar.
- La preparación las pone en igualdad: es una decisión explícita, no un efecto de las unidades.

## 3. Inercia y silueta

*[§4]*, con 50 reinicios de K-means:

| k | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|
| Inercia | 812,6 | 710,8 | 621,1 | 539,9 | 474,8 | 421,0 | 391,7 | 366,7 | 345,5 |
| Silueta | **0,353** | 0,259 | 0,218 | 0,231 | 0,251 | 0,231 | 0,235 | 0,223 | 0,232 |
| Grupo más chico (%) | 24,1 | 7,0 | 6,3 | 6,3 | 5,7 | 5,7 | 2,5 | 2,5 | 1,9 |

**No hay un codo claro.** La inercia baja de forma pareja (102, 90, 81, 65… por cada k más) hasta
k = 7 y se aplana después, cuando ya aparecen grupos de menos del 5 %.

## 4. Elección de k

**k = 2** (D-32). Se eligió con la estabilidad y la interpretación, no solo con un índice:

| | k = 2 | k = 3 | k = 4 |
|---|---|---|---|
| ARI mínimo entre 5 semillas (10 reinicios) | 1,00 | **0,23** | 0,72 |
| ARI mínimo entre 5 semillas (50 reinicios) | 1,00 | 0,97 | 0,77 |
| ARI frente al mínimo de 3 facturas pagadas | **0,80** | 0,28 | 0,34 |
| ARI frente al mínimo de 10 facturas pagadas | **0,85** | 0,35 | 0,53 |

*[§5 y §7]*

- **Estabilidad entre semillas.** Con 10 reinicios, k = 3 cambiaba según la semilla. Con 50 se
  estabiliza, y por eso se usan 50.
- **La prueba decisiva es la sensibilidad al mínimo de facturas** que D-09 prometía. Solo con k = 2
  los grupos se mantienen al pasar de 5 a 3 o a 10 facturas.
- **Por qué no k = 3.** Encajaba con los tres tratamientos del anteproyecto, pero su tercer grupo
  (11 clientes muy tardíos e irregulares) desaparece al cambiar un criterio arbitrario del equipo.
  R16 revisa si otro algoritmo los encuentra.
- **Lo demás que apoya a k = 2:** tiene la mejor silueta (0,353), ningún grupo pequeño y dos grupos
  que se nombran con un tratamiento.

## 5. Perfil de los grupos

Medianas en el entrenamiento *[§6]*:

| Grupo | Clientes | Atraso mediano (días) | Rango del atraso | % tardías | Facturas por año | % varios abonos | % cierres con nota |
|---|---|---|---|---|---|---|---|
| **Paga a tiempo o casi** | 120 (75,9 %) | 9,0 | 14,0 | 10,4 | 13,1 | 0,0 | 7,1 |
| **Paga tarde** | 38 (24,1 %) | 51,5 | 50,0 | 81,3 | 12,7 | 2,4 | 11,8 |

Los dos grupos se parecen en cuánto y con qué frecuencia se les factura: se separan por **cómo
pagan**. «Paga tarde» se atrasa más, de forma más variable, y cierra más facturas con notas.

- **Paga a tiempo o casi:** le basta el correo semanal.
- **Paga tarde:** requiere llamada.

En prueba, los 68 clientes asignados al centro más cercano se reparten casi igual: 75,0 % y 25,0 %
*[§6]*.

## 6. Lo que el agrupamiento no prueba

Los grupos describen cómo pagó cada cliente entre 2022 y mediados de 2025. No dicen **por qué** paga
así ni que vaya a seguir igual. Que un cliente esté en «paga tarde» tampoco prueba que llamarlo vaya
a cambiar su comportamiento: eso solo lo mide un piloto (anteproyecto §5, C). R17 mide si los grupos
anticipan lo que pasó después.
