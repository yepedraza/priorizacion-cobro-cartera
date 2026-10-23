"""Genera los ocho gráficos del cuerpo del informe (D-39) en entrega/figuras/.

Ninguno vuelve a consultar la prueba ni a entrenar un modelo. Las cifras se copian de salidas ya
impresas en los artefactos del equipo; cada bloque cita de dónde sale.

Uso:  ../.venv/bin/python scripts/figuras_informe.py   (entorno del kernel «Python (ML1)»)
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.ticker import FuncFormatter

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "entrega" / "figuras"

# Paleta de referencia (skill dataviz): tres primeros tonos categóricos, válidos en todos los pares.
AZUL, NARANJA, AGUA = "#2a78d6", "#eb6834", "#1baf7a"
GRIS, TINTA, TINTA_2, REJILLA = "#9a9993", "#0b0b0b", "#52514e", "#e6e5e0"

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 9, "axes.edgecolor": GRIS, "axes.labelcolor": TINTA_2,
    "xtick.color": TINTA_2, "ytick.color": TINTA_2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": REJILLA, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "legend.frameon": False, "savefig.dpi": 200, "savefig.bbox": "tight",
})


def coma(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


EJE_COMA = FuncFormatter(lambda x, _: f"{x:g}".replace(".", ","))


def guardar(fig, nombre):
    fig.savefig(SALIDA / nombre)
    plt.close(fig)
    print("  ", nombre)


def solucion():
    """Fig. 1 · Cómo se usa B en la operación (anteproyecto §5)."""
    fig, ax = plt.subplots(figsize=(7.2, 2.5))
    ax.set_axis_off(); ax.set_xlim(-0.15, 10.45); ax.set_ylim(0, 3.4)
    cajas = [
        (0.0, "Factura emitida\n+ historial del cliente", "datos del ERP"),
        (2.65, "B · Score: riesgo de\npagar > 30 días tarde", "regresión logística"),
        (5.3, "Lista diaria:\nprobabilidad × saldo", "20 clientes por día"),
        (7.95, "La gestora decide\na quién contactar", "el controller supervisa"),
    ]
    for x, texto, nota in cajas:
        ax.add_patch(FancyBboxPatch((x, 1.55), 2.35, 1.35, boxstyle="round,pad=0.04,rounding_size=0.12",
                                    fc="#eef4fc", ec=AZUL, lw=1))
        ax.text(x + 1.175, 2.4, texto, ha="center", va="center", fontsize=7.5, color=TINTA)
        ax.text(x + 1.175, 1.8, nota, ha="center", va="center", fontsize=7, color=TINTA_2)
    for x in (2.4, 5.05, 7.7):
        ax.add_patch(FancyArrowPatch((x, 2.22), (x + 0.24, 2.22), arrowstyle="-|>", mutation_scale=9,
                                     color=TINTA_2, shrinkA=0, shrinkB=0))
    notas = [(0.95, "A · Segmento del cliente: define el tono del contacto; no entra al modelo"),
             (0.35, "C · Piloto con asignación al azar: prueba si gestionar distinto acorta el pago")]
    for y, texto in notas:
        ax.add_patch(FancyBboxPatch((0.0, y - 0.22), 10.3, 0.44, boxstyle="round,pad=0.03,rounding_size=0.1",
                                    fc="white", ec=GRIS, lw=0.8, ls="--"))
        ax.text(0.15, y, texto, va="center", fontsize=7.2, color=TINTA_2)
    guardar(fig, "fig1_solucion.png")


def embudo():
    """Fig. 2 · De los saldos a las facturas con etiqueta (diagnostico_R11.ipynb §1; informe de avance §2).
    Las 685 abiertas al corte salen por diferencia (17.920 − 17.235)."""
    pasos = [("Saldos del ERP", 19262, None), ("Facturas", 17920, "1.342 saldos que no son facturas"),
             ("Facturas cerradas", 17235, "685 abiertas al corte"),
             ("Con atraso medible", 17209, "25 sin fecha de cancelación y 1 con plazo negativo"),
             ("Con recibo de caja", 15925, "1.284 cerradas sin ningún recibo de caja (D-16)"),
             ("Con etiqueta de B", 15822, "103 mixtas con recibo de menos del 90 % (D-20)")]
    fig, ax = plt.subplots(figsize=(7.2, 2.9))
    y = list(range(len(pasos)))[::-1]
    ax.barh(y, [p[1] for p in pasos], color=AZUL, height=0.62)
    for yi, (nombre, n, nota) in zip(y, pasos):
        ax.text(-300, yi, nombre, ha="right", va="center", fontsize=8.5, color=TINTA)
        ax.text(n + 250, yi, f"{n:,}".replace(",", "."), va="center", fontsize=8.5, color=TINTA)
        if nota:
            ax.text(22300, yi, f"− {nota}", va="center", fontsize=7.5, color=TINTA_2)
    ax.set_xlim(0, 38500); ax.set_axis_off()
    ax.text(0, -0.85, "De las 15.822 con etiqueta, 5.196 (32,84 %) se pagaron más de 30 días tarde.",
            fontsize=7.5, color=TINTA_2)
    guardar(fig, "fig2_embudo.png")


def particion():
    """Fig. 3 · Partición temporal (D-23; informe de avance §3)."""
    fig, ax = plt.subplots(figsize=(7.2, 1.9))
    franjas = [(2022.0, 2024.5, "Subentrenamiento", "2022-01 a 2024-06", AZUL),
               (2024.5, 2025.5, "Validación", "2024-07 a\n2025-06", AGUA),
               (2025.5, 2026.75, "Prueba", "2025-07 a 2026-09\n3.970 facturas · una consulta", NARANJA)]
    for a, b, nombre, fechas, color in franjas:
        ax.barh(0, b - a, left=a, height=0.45, color=color, edgecolor="white", linewidth=2)
        ax.text((a + b) / 2, 0, nombre, ha="center", va="center", fontsize=8, color="white", fontweight="bold")
        ax.text((a + b) / 2, -0.3, fechas, ha="center", va="top", fontsize=7, color=TINTA_2, linespacing=1.3)
    ax.annotate("", xy=(2022.0, 0.4), xytext=(2025.5, 0.4), arrowprops=dict(arrowstyle="<->", color=TINTA_2, lw=0.8))
    ax.text(2023.75, 0.48, "Entrenamiento · 8.930 facturas", ha="center", va="bottom", fontsize=7.5, color=TINTA_2)
    ax.plot([2025.5, 2025.5], [-0.25, 0.62], color=TINTA, lw=1, ls="--")
    ax.text(2025.53, 0.48, "corte 1/07/2025", fontsize=7.5, color=TINTA, va="bottom")
    ax.set_ylim(-1.05, 0.8); ax.set_xlim(2021.9, 2026.85); ax.set_axis_off()
    for anio in range(2022, 2027):
        ax.text(anio, -0.98, str(anio), ha="center", fontsize=7.5, color=GRIS)
    guardar(fig, "fig3_particion.png")


def candidatos():
    """Fig. 4 · AUC-PR media ± desviación entre pliegues (informe de avance §4 y §5)."""
    datos = [("Línea base (Dummy)", 0.309, 0.007), ("Árbol de referencia", 0.665, 0.030), ("SVM RBF", 0.700, 0.037),
             ("Bosque aleatorio", 0.719, 0.049), ("Gradient boosting", 0.720, 0.043),
             ("Regresión logística (elegida)", 0.720, 0.021), ("Red neuronal (MLP)", 0.730, 0.035)]
    fig, ax = plt.subplots(figsize=(7.2, 2.7))
    for i, (nombre, m, d) in enumerate(datos):
        color = AZUL if "elegida" in nombre else (GRIS if "Dummy" in nombre else TINTA_2)
        ax.errorbar(m, i, xerr=d, fmt="o", color=color, ms=6, capsize=3, lw=1.2)
        ax.text(m + d + 0.008, i, f"{coma(m, 3)} ± {coma(d, 3)}", va="center", fontsize=7.5, color=TINTA_2)
    ax.set_yticks(range(len(datos)), [d[0] for d in datos]); ax.set_xlim(0.25, 0.85)
    ax.xaxis.set_major_formatter(EJE_COMA)
    ax.set_xlabel("AUC-PR en validación cruzada por trimestre (5 pliegues)"); ax.grid(axis="y", visible=False)
    guardar(fig, "fig4_candidatos.png")


def backtest():
    """Fig. 5 · Monto en riesgo capturado en la prueba (evaluacion_B.ipynb §3, tabla impresa)."""
    k = ["K = 10", "K = 20", "K = 40"]
    series = [("Modelo", [32.0, 47.4, 67.1], AZUL), ("Saldo de 1 a 30 días (D-19)", [26.9, 41.4, 60.1], AGUA),
              ("Regla actual (D-07)", [24.0, 37.9, 57.3], NARANJA)]
    fig, ax = plt.subplots(figsize=(7.2, 2.6))
    ancho = 0.26
    for j, (nombre, v, color) in enumerate(series):
        xs = [i + (j - 1) * (ancho + 0.02) for i in range(3)]
        ax.bar(xs, v, width=ancho, color=color, label=nombre)
        for x, vi in zip(xs, v):
            ax.text(x, vi + 1.2, coma(vi), ha="center", fontsize=7.5, color=TINTA)
    ax.set_xticks(range(3), k); ax.set_ylim(0, 80); ax.grid(axis="x", visible=False)
    ax.set_ylabel("% del dinero en duda\nque terminó tardío")
    ax.legend(loc="upper left", fontsize=7.5)
    guardar(fig, "fig5_backtest.png")


def calibracion():
    """Fig. 6 · Calibración por decil (evaluacion_B.ipynb §1, sin class_weight, y §3)."""
    val_p = [0.034, 0.060, 0.104, 0.140, 0.176, 0.226, 0.286, 0.386, 0.555, 0.848]
    val_r = [0.030, 0.068, 0.098, 0.135, 0.158, 0.211, 0.351, 0.483, 0.722, 0.831]
    pru_p = [0.024, 0.055, 0.095, 0.125, 0.168, 0.226, 0.320, 0.432, 0.568, 0.809]
    pru_r = [0.038, 0.128, 0.161, 0.156, 0.214, 0.385, 0.516, 0.647, 0.781, 0.836]
    fig, ax = plt.subplots(figsize=(3.6, 3.3))
    ax.plot([0, 1], [0, 1], color=GRIS, lw=1, ls="--", label="Calibración perfecta")
    ax.plot(val_p, val_r, "-o", color=AZUL, lw=2, ms=4, label="Validación (2024-07 a 2025-06)")
    ax.plot(pru_p, pru_r, "-o", color=NARANJA, lw=2, ms=4, label="Prueba (2025-07 a 2026-09)")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal")
    ax.xaxis.set_major_formatter(EJE_COMA); ax.yaxis.set_major_formatter(EJE_COMA)
    ax.set_xlabel("Probabilidad media predicha"); ax.set_ylabel("Proporción real de tardías")
    ax.legend(loc="upper left", fontsize=7)
    guardar(fig, "fig6_calibracion.png")


def falsos_negativos():
    """Fig. 7 · Falsos negativos por grupo, logística, validación (informe de avance §7)."""
    grupos = [("Todas (821 tardías)", 34.0), ("Empresa A (764)", 31.9), ("Empresas B, C y D (57)", 61.4),
              ("4 o menos facturas pagadas (87)", 24.1), ("5 o más facturas pagadas (734)", 35.1)][::-1]
    fig, ax = plt.subplots(figsize=(7.2, 2.2))
    for i, (g, v) in enumerate(grupos):
        ax.barh(i, v, color=NARANJA if "B, C" in g else (GRIS if "Todas" in g else AZUL), height=0.6)
        ax.text(v + 0.8, i, f"{coma(v)} %", va="center", fontsize=7.5, color=TINTA)
    ax.set_yticks(range(len(grupos)), [g for g, _ in grupos]); ax.set_xlim(0, 72)
    ax.set_xlabel("% de facturas tardías que el modelo no marca (cupo del 30 %)"); ax.grid(axis="y", visible=False)
    guardar(fig, "fig7_falsos_negativos.png")


def riesgos():
    """Fig. 8 · Mapa de riesgos (cierre_R18.md §2): número de riesgo en su celda."""
    niveles = ["Baja", "Media", "Alta"]
    celdas = {(2, 1): [1, 4, 5], (1, 2): [2], (0, 2): [3], (1, 1): [6], (2, 2): [7]}
    fig, ax = plt.subplots(figsize=(3.6, 3.0))
    tonos = {0: "#f4f8fd", 1: "#d6e6f8", 2: "#a9cbf0", 3: "#6fa7e6", 4: "#2a78d6"}
    for p in range(3):
        for i in range(3):
            ax.add_patch(plt.Rectangle((i, p), 1, 1, fc=tonos[p + i], ec="white", lw=2))
            ids = celdas.get((p, i))
            if ids:
                ax.text(i + 0.5, p + 0.5, " · ".join(str(r) for r in ids), ha="center", va="center",
                        fontsize=10, fontweight="bold", color="white" if p + i >= 3 else TINTA)
    ax.set_xlim(0, 3); ax.set_ylim(0, 3); ax.set_aspect("equal"); ax.grid(False)
    ax.set_xticks([0.5, 1.5, 2.5], niveles); ax.set_yticks([0.5, 1.5, 2.5], niveles)
    ax.set_xlabel("Impacto"); ax.set_ylabel("Probabilidad")
    for s in ax.spines.values():
        s.set_visible(False)
    guardar(fig, "fig8_riesgos.png")


if __name__ == "__main__":
    SALIDA.mkdir(parents=True, exist_ok=True)
    print(f"Gráficos en {SALIDA.relative_to(RAIZ)}:")
    for f in (solucion, embudo, particion, candidatos, backtest, calibracion, falsos_negativos, riesgos):
        f()
