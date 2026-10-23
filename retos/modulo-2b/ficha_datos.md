# R11 · Ficha de datos

> **Proyecto Final Integrador · Machine Learning I · Universidad EAN**
> Fase CRISP-DM: **Comprensión de los datos** · Reto acumulativo: **R11**
> Integrantes: **Claudia Naranjo, Yery Pedraza y Nicolás Ruiz** · Última actualización: 2026-10-21

Las cifras salen de [`diagnostico_R11.ipynb`](diagnostico_R11.ipynb) (*[Diag. §n]*) y de
[`viabilidad_R10.ipynb`](viabilidad_R10.ipynb) (*[Viab. §n]*).

## 1. Procedencia

| Aspecto | Detalle |
|---|---|
| Fuente | Sistema contable (ERP) de un grupo empresarial colombiano de servicios: su cartera (cuentas por cobrar) |
| Autorización | La compañía autorizó por escrito el uso de los datos para este proyecto académico. No hay licencia pública: los datos no se pueden redistribuir |
| Anonimización | Hecha por la compañía, irreversible, antes de entregar los datos: nombres y códigos reemplazados por etiquetas, montos multiplicados por un factor secreto por saldo (entre 0,85 y 0,98 o entre 1,02 y 1,15) y una columna de actividad económica inventada |
| Fecha de corte de la extracción | 2026-10-18 |
| Fecha de acceso | 2026-10-18, el día en que el equipo recibió los datos |
| Cobertura | Diciembre de 2019 a octubre de 2026; 648 clientes, 4 empresas, 11 unidades de negocio *[Viab. §1]* |
| Cómo obtenerlos | Los datos no están en el repositorio: la carpeta `datos_crudos/` está excluida de Git (ver `datos_crudos/LEEME.md`) |
| Cita (APA 7) | Compañía anonimizada. (2026). *Cartera de cuentas por cobrar: saldos y movimientos, 2019–2026* [Datos no publicados, anonimizados; uso autorizado para este proyecto]. |

## 2. Tablas

| Tabla | Filas | Columnas | Una fila es |
|---|---|---|---|
| `saldos_anonimizados.csv` | 19.262 | 54 | Un **saldo**: el registro contable de una cuenta por cobrar, con su estado a la fecha de corte |
| `movimientos_anonimizados.csv` | 40.519 | 44 | Un **movimiento**: cada cargo, recaudo (recibo de caja, RC), nota o ajuste aplicado a un saldo |

Se unen por `id_saldo`; la relación está completa: no hay saldos sin movimientos ni movimientos sin
saldo *[Viab. §1]*. Tipos: en saldos, 18 de texto, 24 numéricas, 9 fechas y 3 booleanas
*[Diag. §2]*.

## 3. Unidad de observación y objetivo

- **Unidad de observación del modelo B:** la **factura** (`id_saldo` con `es_deuda_facturada`). Son
  17.920 de los 19.262 saldos; los demás nacen de notas, ajustes o saldos iniciales *[Viab. §1]*.
- **Unidad de la segmentación A:** el **cliente** (`nit_cliente`) con al menos 5 facturas pagadas.
- **Objetivo:** `tardia`, pago tardío. Vale 1 si la factura se pagó más de 30 días después de su
  vencimiento y 0 si no. No es una columna de la base: se construye en `src/cartera/etiqueta.py`.
  - El atraso se mide hasta que entra el dinero, no hasta que el saldo queda en cero: hasta el
    cierre, si lo cerró un RC, o hasta el último RC, si lo cerró una nota (el atraso se mide hasta el último pago con recibo de caja).
  - Quedan sin etiqueta las facturas cerradas sin ningún RC y las que se pagaron con RC menos del
    90 % de su valor (la etiqueta debe describir un pago, no un cierre casi sin dinero).
  - Solo se usan facturas que ya tuvieron 30 días para resolverse después de vencer (se exige un desenlace ya conocido a la fecha de corte).
- **Desbalance:** 32,84 % de pago tardío en las 15.822 cerradas con etiqueta; ≈ 30 % por año en
  2022–2024 *[Diag. §1.6 y §4]*.

## 4. Calidad

| Hallazgo | Detalle | Qué se hace |
|---|---|---|
| Faltantes | Solo en 7 columnas de saldos y 1 de movimientos, todas posteriores a la emisión. La peor es `dias_mora_actual` (96,27 %): falta justo cuando el saldo está en cero o a favor (mecanismo estructural, MAR) *[Diag. §2 y §5]* | No se imputa: no entra al modelo. Las predictoras no tienen faltantes en 2022–2024 |
| Duplicados | Ninguno, con o sin las columnas de identificadores *[Diag. §3]* | — |
| Categorías | Sin variantes de escritura. `condicion_pago_inferida` repite el plazo por tramos y su tramo C15 incluye los 245 plazos negativos *[Diag. §4]* | Se usa el plazo, no la condición |
| Plazos negativos | 245 saldos con vencimiento anterior a la emisión: error de registro *[Viab. §7]* | Se excluyen |
| Cierres sin pago | 1.284 facturas cerradas sin ningún RC y 511 mixtas *[Diag. §1.2]* | Etiqueta: atraso hasta el último RC; las sin RC y las mixtas con RC de menos del 90 % quedan fuera |
| Cerradas sin fecha | 25 facturas en cero sin fecha de cancelación *[Diag. §1.1]* | Sin atraso medible: sin etiqueta |
| Columnas sin información | `cuota` vale 0 siempre; `fecha_radicacion` es igual a la emisión en el 99,7 % *[Viab. §7]* | No se usan |
| Categorías del diccionario ausentes | La cuenta 131510 y el tipo de cliente `INDETERMINADO` no aparecen *[Diag. §4]* | Se documenta |
| Montos escalados | Un monto individual difiere del real entre 2 % y 15 % | Se reportan totales como aproximados; los porcentajes dentro de un saldo son exactos |

## 5. Fuga y datos sensibles

- **Fuga:** las columnas que se conocen después de la emisión quedan fuera de las predictoras. Un
  ejemplo extremo es `dias_hasta_cancelacion`: menos el plazo, da exactamente el atraso en el
  100 % de las facturas cerradas, es decir, la etiqueta *[Diag. §6]*. También quedan fuera
  `total_debitos` (es un acumulado; se usa el débito inicial) y `codigo_cuenta` (la cuenta de difícil
  cobro es una reclasificación posterior).
- **Datos sensibles:** ninguno. La compañía anonimizó todo el conjunto, así que ninguna columna
  identifica a una persona. Si `nombre_vendedor` y `tipo_cliente` entran como predictoras se decide en
  R12.
- **Identificadores:** fuera, para que el modelo no memorice al cliente (la validación se agrupa por bloque de tiempo y no por cliente).
- **Representatividad:** el 98,3 % de los saldos es de personas jurídicas nacionales y la Empresa A
  concentra el 89 %. Los resultados no representan bien a personas naturales, clientes del exterior
  ni a las empresas B, C y D.

## 6. Costo de ajuste

Una SVM RBF tarda ≈ 0,25 s con 4.942 facturas de entrenamiento, y el tiempo crece con un exponente
cercano a 1,8: más rápido que lineal *[Diag. §7]*. Con las 13.212 facturas con desenlace conocido
desde 2022, un ajuste tomaría ≈ 1,5 s y una búsqueda de 150 ajustes, unos 4 minutos. Los tiempos
varían un poco entre ejecuciones; el cuaderno da los de la última. La AUC-PR en validación casi no
cambia entre 500 y 4.942 filas (0,35 a 0,36), igual que la de una regresión logística (0,353).

**Filas para la búsqueda de hiperparámetros: todas las de entrenamiento, sin submuestrear.** La
curva muestra que el costo es de minutos y que submuestrear no ahorra nada que importe; además,
conviene no perder datos cuando R12 agregue el historial del cliente. Si las variables de R12 hacen
la SVM mucho más lenta, la curva se repite.
