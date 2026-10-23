# Anexo B · Datos reales

> **Proyecto Final Integrador · Machine Learning I · Universidad EAN** · Equipo **ArbolesDeIndecision**
> Integrantes: **Claudia Naranjo, Yery Pedraza y Nicolás Ruiz** · Última actualización: 2026-10-22

Evidencias para el bono de datos reales, condición por condición. La ficha completa está en
`ficha_datos.md`; el diagnóstico, en `retos/modulo-2b/diagnostico_R11.ipynb`.

## 1. Hechos observados de una organización real

Los datos son la **cartera (cuentas por cobrar) registrada en el sistema contable (ERP)** de un grupo
empresarial colombiano de servicios: cada factura emitida, cada recibo de caja, nota y ajuste que la
compañía registró en su operación entre diciembre de 2019 y octubre de 2026. No son simulados ni
generados con código o con IA: el proyecto no genera datos sintéticos en ningún paso.

## 2. Procedencia verificable

| Condición | Evidencia |
|---|---|
| Organización de origen | Grupo empresarial colombiano de servicios: cuatro empresas, once unidades de negocio. Su nombre no se publica, por confidencialidad |
| Autorización por escrito | Firmada el 22/10/2026 en Bogotá por el gerente de un área de la compañía, con facultad para autorizar el uso de su información, a nombre de los tres integrantes y exclusivamente para este proyecto. No hay licencia pública. Condiciones: no intentar reidentificar clientes, vendedores ni empresas; no publicar ni redistribuir los datos (en el repositorio solo va código y la compañía no se nombra); limitar el uso al proyecto y su sustentación; y la compañía puede revisar el informe antes de la entrega. El documento firmado se conserva fuera del repositorio, porque identifica a la compañía, y se muestra al jurado si lo pide |
| Fecha de corte y de acceso | 18/10/2026, el día en que el equipo recibió los datos |
| Cita (APA 7) | Compañía anonimizada. (2026). *Cartera de cuentas por cobrar: saldos y movimientos, 2019–2026* [Datos no publicados, anonimizados; uso autorizado para este proyecto]. |

## 3. Cómo obtener los datos

El archivo crudo **no va en el zip ni en el repositorio**, porque la autorización no permite
redistribuirlo. Los dos archivos (`saldos_anonimizados.csv` y `movimientos_anonimizados.csv`) y el
diccionario de datos viven en la carpeta `datos_crudos/`, que Git ignora; su `LEEME.md` explica qué
archivos van ahí y cómo se usan. Para reproducir los cuadernos, el jurado puede pedir los archivos al
equipo, que los entrega con el permiso de la compañía; con ellos en `datos_crudos/`, los cuadernos y
los scripts corren con rutas relativas.

## 4. Anonimización y tratamiento ético

- **Anonimización, hecha por la compañía antes de entregar los datos, de forma irreversible:** nombres
  y códigos reemplazados por etiquetas, montos multiplicados por un factor secreto por saldo (entre 0,85
  y 0,98 o entre 1,02 y 1,15) y una columna de actividad económica inventada, que el proyecto no usa
  [ficha §1].
- **Personas:** el 98,3 % de los saldos es de personas jurídicas. Los clientes que son personas
  naturales aparecen solo con una etiqueta anónima; ninguna columna identifica a una persona [ficha §5].
- **Normativa:** el tratamiento de datos personales en Colombia se rige por la Ley 1581 de 2012. Los
  datos llegan anonimizados de forma irreversible y se usan solo para este proyecto académico.
- **Uso ético decidido por el equipo:** no se evalúa el desempeño de vendedores ni de gestoras;
  `nombre_vendedor` no entra al modelo y solo se usa para auditar [informe §3].
- **Resguardo:** los datos solo están en `datos_crudos/`, fuera de Git. La aplicación, si se muestra,
  es privada y se habilita solo durante la sustentación.

## 5. Tamaño

| Tabla | Filas | Columnas |
|---|---|---|
| `saldos_anonimizados.csv` | 19.262 | 54 |
| `movimientos_anonimizados.csv` | 40.519 | 44 |

El modelo B usa 15.822 facturas con etiqueta, muy por encima del mínimo de 1.000 filas [diagnóstico §1].

## 6. Suciedad real encontrada

| Hallazgo | Cuánto | Qué se hizo |
|---|---|---|
| Facturas que llegan a cero sin dinero: cerradas con notas o ajustes contables | 1.284 sin ningún recibo de caja y 511 mixtas | El atraso se mide hasta el último recibo de caja; las que no tienen ninguno salen de la etiqueta [diagnóstico §1.2 a §1.4] |
| Mixtas cuyo recibo cubre poco del valor | 103 con menos del 90 % | Salen de la etiqueta; con 80 % o 95 % el resultado casi no cambia [diagnóstico §1.6] |
| Plazos negativos: vencimiento anterior a la emisión | 245 saldos | Error de registro; se excluyen [ficha §4] |
| Facturas cerradas sin fecha de cancelación | 25 | Sin atraso medible; sin etiqueta [diagnóstico §1.1] |
| Faltantes estructurales | `dias_mora_actual`, 96,27 %: falta justo cuando el saldo está en cero | No entra al modelo, porque es posterior a la emisión [ficha §4] |
| Columnas sin información | `cuota` vale 0 siempre; `fecha_radicacion` es igual a la emisión en el 99,7 % | No se usan [ficha §4] |
| Categorías del diccionario que no aparecen | La cuenta 131510 y el tipo de cliente `INDETERMINADO` | Se documenta [ficha §4] |
| Vencimiento que puede no ser el original | No se puede contar: la base no guarda la fecha original | Se declara como límite (informe §2 y §6) |
| Concentración | La Empresa A tiene el 89 % de los saldos | El desempeño se reporta por empresa (informe §6) |
