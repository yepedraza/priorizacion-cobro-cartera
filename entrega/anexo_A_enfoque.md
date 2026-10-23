# Anexo A · Enfoque: intraemprendimiento

> **Proyecto Final Integrador · Machine Learning I · Universidad EAN** · Equipo **ArbolesDeIndecision**
> Integrantes: **Claudia Naranjo, Yery Pedraza y Nicolás Ruiz** · Última actualización: 2026-10-22

Evidencias de la ruta de intraemprendimiento. Las cifras salen de los artefactos del repositorio,
citados entre corchetes; el resumen está en el informe, §1 («Ruta de intraemprendimiento»).

## 1. Enfoque declarado desde R10 y sostenido hasta la entrega

- **R10 (anteproyecto):** el bloque «Enfoque: intraemprendimiento» abre `retos/modulo-2b/anteproyecto_PFI.md`,
  antes del §1, con la propuesta de valor y la ruta de validación. Entró al repositorio el 21/10/2026
  (commit `bb63cbb`).
- **R14 (informe de avance):** el encabezado de `retos/modulo-2b/informe_avance_M2B.md` declara el mismo
  enfoque, y su §1 lo define como «una mejora para el área de cartera de la propia compañía».
- **Entrega final:** `informe_PFI.pdf` lo declara en el encabezado y en §1.

## 2. Organización y usuarios concretos

| Quién | Qué hace hoy | Qué cambia |
|---|---|---|
| **Dos gestoras de cartera** | Eligen cada día a unos 20 clientes, de unos 135 con facturas vencidas, por saldo más alto y vencimiento más próximo [R10, viabilidad §6] | Reciben cada mañana la lista ordenada por probabilidad de pago tardío × saldo. Siguen decidiendo ellas |
| **Controller** | Supervisa la cartera | Vigila el plan de seguimiento (informe §6) |
| **Tesorería** | Recibe el dinero unos 22 días después de lo pactado: 43 días reales frente a 21 pactados, ponderados por monto [R10, viabilidad §2] | Es quien recibe el efecto si el recaudo se acorta |

Hoy hay además un correo automático semanal a cada cliente con saldo pendiente, que no incluye las
facturas que todavía no vencen, según una gestora del área [R10 §1].

## 3. Propuesta de valor

Una **lista diaria** que dice a las gestoras a qué 20 clientes contactar primero, ordenada por el
dinero con mayor riesgo de pagarse con más de 30 días de atraso, para **cobrar antes con la misma
capacidad**, sin contratar personal ni cambiar el tablero que ya usan.

## 4. Hipótesis de mejora

Con el mismo cupo de 20 clientes, priorizar por *probabilidad de pago tardío × saldo* concentra más
dinero en riesgo que la regla actual y, si ese dinero se gestiona antes, se acorta el recaudo.

- **Primera parte, medida en el backtest:** con K = 20, la lista del modelo contiene el 47,4 % del
  dinero en duda que terminó tardío, frente al 37,9 % de la regla actual, y le gana en 254 de 296 días
  hábiles de la prueba [evaluación B §3].
- **Segunda parte, no medida:** que gestionar ese dinero antes acorte el recaudo. Es una hipótesis
  causal y se valida con el piloto (§6).

## 5. Estimación de impacto, con supuestos declarados

**Cada día menos de recaudo libera en caja lo que la compañía factura en un día, ≈ $65 M**
[R10, viabilidad §2].

| Supuesto | Qué implica |
|---|---|
| Los montos están escalados por la compañía (cada saldo, por un factor entre 0,85 y 1,15) | La cifra es aproximada; los porcentajes son exactos [R11, ficha §1 y §4] |
| El efecto se sostiene en toda la cartera | No se ha comprobado; el modelo rinde peor en las empresas B, C y D (informe §6) |
| **No se sabe cuántos días acorta la lista** | El impacto se expresa por día de recaudo ganado, no como un ahorro prometido |

El impacto no se suma ni se proyecta a un año: hacerlo exigiría suponer un número de días ganados
que ningún artefacto del proyecto mide.

## 6. Ruta de validación

1. **Backtest, hecho.** Cada día hábil del 1/07/2025 al 18/08/2026 se reconstruyó la cartera con los
   movimientos anteriores a ese día y se compararon tres listas de 20: regla actual, segunda línea base
   y modelo. La prueba se consultó una sola vez [evaluación B §3].
2. **Piloto con asignación al azar, diseñado.** Dentro de cada segmento de clientes, los activos se
   reparten al azar en dos grupos del mismo tamaño: uno recibe la gestión nueva y el otro sigue con la
   actual. La unidad que se asigna es el cliente, porque la gestión se hace con el cliente [C §4].

| Segmento | Gestión nueva | Clientes por grupo | Diferencia mínima detectable en días hasta el pago (3 / 6 meses) |
|---|---|---|---|
| Paga a tiempo o casi | Aviso automático antes del vencimiento de cada factura | 61 | 13,7 / 13,1 días |
| Paga tarde | Contacto personal de las gestoras apenas vence cada factura | 16 | 27,2 / 25,1 días |

El piloto suma cerca de **1 contacto personal por día hábil** a las gestoras; los avisos del otro
segmento son automáticos [C §5]. Solo detectaría efectos grandes, de cerca de un tercio de los días
medios hasta el pago (39,6 y 70,8 días). Si no encuentra diferencia, eso no prueba que no haya efecto:
solo que no es tan grande. Queda por definir con el área de cartera cuántos días antes del
vencimiento se envía el aviso.

## 7. Qué no demuestra este proyecto

- Que llamar a los clientes de la lista acorte su atraso: el backtest compara qué dinero estaba en cada
  lista, no el efecto de la gestión.
- Que mover el plazo pactado mueva el pago: dentro del mismo cliente, cada día de plazo de más retrasa
  el pago solo 0,29 días (IC 95 %: 0,07 a 0,61), y una prórroga registrada como plazo podría sesgar esa
  cifra [C §3].
