# R18 · Cierre

> **Proyecto Final Integrador · Machine Learning I · Universidad EAN**
> Fase CRISP-DM: **Despliegue y cierre** · Reto acumulativo: **R18**
> Integrantes: **Claudia Naranjo, Yery Pedraza y Nicolás Ruiz** · Última actualización: 2026-10-22

Las cifras salen de los artefactos del equipo: `informe_avance_M2B.md`, `evaluacion_R17.md`,
`plazo_C.ipynb` y `evaluacion_B.ipynb`. Los datos de la compañía no están en el repositorio. Este
cierre no promete que el modelo funcione en producción: declara qué se midió y qué no.

## 1. Resumen ejecutivo (English)

**Problem and decision.** A Colombian services group collects its invoices about 22 days later than agreed, which ties up working capital. Two collections analysts can give personal follow-up to only 20 customers per day, out of about 135 with overdue invoices, and today they choose by balance and due date. The decision we support is which 20 customers to contact each day.

**Data.** We use the company's own anonymized ERP records, used under written authorization: 19,262 balances and 40,519 movements. The target, an invoice paid more than 30 days after its due date, is not in the data, so we built it, measuring delay up to the last cash receipt. This leaves 15,822 labeled invoices, 32.84% of them late.

**Method.** We trained models on invoices issued from January 2022 to June 2025, using 11 predictors known at issue, and evaluated them forward in time. Logistic regression matched a random forest, gradient boosting and a neural network within validation noise, so we kept it as the simplest to explain. The test period, July 2025 to September 2026, was queried only once. A daily list ranks customers by late-payment probability times balance.

**Main result.** On unseen data the model reaches a precision-recall AUC of 0.744, against 0.386 for the base rate. With a quota of 20 customers, its list captures 47.4% of the money still at risk that ended up late, versus 37.9% for the current rule, and it wins on 254 of 296 business days.

**Main limit.** The backtest does not show that contacting customers shortens delays. Probabilities run low: where the model predicts 32%, 52% were late. It also misses more late invoices in the group's smaller companies (61% versus 32%, in validation, on only 57 late invoices).

**Recommendation.** Adopt with conditions. Use the list to order work, not to promise savings. Retrain on recent history now, because late invoices reached 38.6% against a 31–34% reference. Monitor four metrics quarterly. Validate the benefit with a randomized pilot by customer before reporting any effect.

## 2. Matriz de riesgos

Probabilidad e impacto son un juicio del equipo (Baja, Media, Alta); las cifras de «Evidencia» son medidas.

| # | Riesgo (tipo) | Evidencia (fuente) | Prob. | Impacto | Mitigación |
|---|---|---|---|---|---|
| 1 | **Deriva del nivel de atraso** (modelo): ordena bien, pero su probabilidad queda corta | Tardías 38,6 % en la prueba frente a ≈ 30 % en entrenamiento; donde predice 32 %, se atrasa el 52 % (`evaluacion_B.ipynb` §3) | Alta | Media | Usar solo el orden de la lista; reentrenar (§3) |
| 2 | **`fecha_vencimiento` puede ser la actual, no la original** (datos): una prórroga alarga el plazo y acorta el atraso. Afecta a C (documentado) y posiblemente a etiqueta, plazo, historial, segmentación y backtest (no medido) | Diccionario §6, punto 9; la base no guarda la fecha original | Media | Alta | Preguntar a cartera si prorroga y si guarda la original; si no, declararlo como límite |
| 3 | **Fuga de datos confidenciales** (datos) | Autorización escrita; datos fuera del repositorio (anteproyecto §11) | Baja | Alta | Datos solo en `datos_crudos/`, ignorada por Git; aplicación privada, solo durante la sustentación |
| 4 | **Peor cobertura en las empresas B, C y D** (sesgo / equidad): el modelo deja pasar más tardías | Falsos negativos de 61 % frente a 32 % en la Empresa A, con 57 tardías; la A tiene el 89 % de los datos (validación, `informe_avance_M2B.md` §7) | Alta | Media | Reportar por empresa; no generalizar a B, C y D; revisar un cupo por empresa si crece su volumen |
| 5 | **Cobro insistente a clientes con poca historia** (sesgo / equidad) | Marca el 52,3 % de sus facturas, aunque solo el 31 % es tardía (validación, `informe_avance_M2B.md` §7) | Alta | Media | La gestora decide; esos clientes quedan «sin historia suficiente» y sin segmento |
| 6 | **Profecía autocumplida** (operación): contactar cambia el historial, que es la señal principal del modelo | Anteproyecto §11; §4 de este cierre | Media | Media | Correo semanal para todos; vigilar a los clientes no priorizados |
| 7 | **Beneficio no demostrado** (valor): el backtest no mide si llamar acorta el atraso | 47,4 % frente a 37,9 % de la regla actual; el piloto solo detectaría diferencias de 13–14 días y de 25–27 (`plazo_C.ipynb` §5) | Alta | Alta | No prometer ahorros; piloto con asignación al azar por cliente antes de reportar efecto |

## 3. Plan de seguimiento

Las referencias son medidas; **los umbrales y las frecuencias son un criterio del equipo**, no una
cifra que salga de los datos (el 5 de la métrica 2 es la mitad de la ventaja medida).

| # | Métrica | Referencia medida | Umbral | Frecuencia |
|---|---|---|---|---|
| 1 | **Proporción de facturas tardías** (más de 30 días de atraso) | Rango de 31–34 % anual (anteproyecto §11); 38,6 % en la prueba | Fuera de 31–34 % durante un trimestre: revisar el modelo | Mensual |
| 2 | **Monto en riesgo capturado con K = 20**, frente a la regla actual | 47,4 % frente a 37,9 % (`evaluacion_B.ipynb` §3) | Ventaja menor de 5 puntos: reentrenar. Menor o igual a 0 dos trimestres seguidos: retirar | Trimestral |
| 3 | **AUC-PR** en facturas nuevas con desenlace conocido | 0,744 (IC 95 %: 0,721 a 0,768) frente a 0,386 de la línea base | Por debajo de 0,721: reentrenar | Trimestral |
| 4 | **Falsos negativos por empresa** (B, C y D frente a A) | 61 % frente a 32 % en validación | Brecha mayor que 29 puntos: revisar el cupo por empresa | Trimestral |

**Reentrenar:** cualquiera de las métricas 1 a 4 fuera de su umbral. **Retirar:** la métrica 2 sin
ventaja sobre la regla actual dos trimestres seguidos, o un piloto de C que muestre que gestionar no
cambia el pago.

**Dos avisos.** La métrica 1 **ya está fuera del rango** (38,6 % frente a 31–34 %), así que según
este plan el modelo ya debería reentrenarse con la historia reciente. Y como una factura solo tiene
desenlace conocido 30 días después de vencer, las métricas 2 y 3 detectan un deterioro con al menos
un mes de atraso.

## 4. ¿Hay una decisión secuencial?

**No.** Un modelo supervisado basta.

- El modelo puntúa cada día con un modelo ya entrenado con desenlaces históricos; no elige acciones
  para aprender de su recompensa.
- Los datos no registran qué gestión se hizo a cada cliente, así que no hay una recompensa por
  acción con la que entrenar una política.
- Si gestionar de otro modo acorta el pago es una pregunta causal, y C la deja a un piloto con
  asignación al azar por cliente: un experimento de una sola vez, no un agente que explora.

**Límite.** Sí hay retroalimentación: contactar a un cliente puede cambiar su pago futuro y, con él,
su historial (riesgo 6). No se modela como decisión secuencial; se vigila con el plan de seguimiento.

**Qué lo cambiaría.** Que el piloto muestre que gestionar acorta el pago y que cartera quiera elegir
en línea qué gestión dar, aprendiendo de los resultados. Entonces habría agente (la gestora),
acciones (tipo de gestión) y recompensa (días hasta el pago), y el costo de explorar lo pagarían los
clientes que reciban la gestión que se cree inferior. No se entrega `cierre_R18.ipynb`.

## 5. Esquema de la sustentación

Un mensaje por sección del informe. Quién presenta cada una y cuánto dura:
`[POR COMPLETAR]`.

| # | Sección | Mensaje | Cifra y artefacto |
|---|---|---|---|
| 1 | **Problema y decisión** | Se cobra unos 22 días tarde y las gestoras atienden 20 clientes por día; el modelo decide a cuáles | 20 de unos 135 clientes (`informe_avance_M2B.md` §1) |
| 2 | **Datos** | Datos reales y confidenciales; el objetivo se construye: el atraso llega hasta el último recibo de caja | 15.822 facturas, 32,84 % tardías (§2) |
| 3 | **Preparación y diseño experimental** | Se evalúa hacia adelante en el tiempo y solo se usa lo conocido al emitir la factura | Corte 1/07/2025; 11 predictoras; prueba consultada una vez (§3) |
| 4 | **Modelado** | Ningún modelo más complejo superó a la logística por más que la variación; se elige el más simple | AUC-PR 0,720 frente a 0,730 de la red; variación entre pliegues 0,035 (§5, §6) |
| 5 | **Evaluación** | En datos no vistos captura más dinero en riesgo que la regla actual, pero su probabilidad queda corta | 47,4 % frente a 37,9 %; AUC-PR 0,744 (`evaluacion_B.ipynb` §3) |
| 6 | **Decisión con límites y gobernanza** | Se adopta con condiciones: ordena la lista, no se probó que gestionar reduzca el atraso, y el plan ya pide reentrenar | 38,6 % frente a 31–34 %; siete riesgos (§2, §3) |
| 7 | **Roles del equipo** | Los tres trabajamos cada fase juntos; cada uno defiende un rol (Crack, Líder, Jefe/a) con sus decisiones | Registro de decisiones |
