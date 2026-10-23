"""Arma ML1_PFI_ArbolesDeIndecision.zip con los archivos de la entrega final (biblia §2).

El zip es plano, sin subcarpetas salvo `datos_crudos/`. Como los datos de la compañía no se
redistribuyen, de `datos_crudos/` solo va `LEEME.md`, que explica cómo obtenerlos.
Antes de armarlo verifica que estén todos los archivos, que no queden marcas [POR COMPLETAR] y que
los PDF estén al día con su fuente.

Uso (desde cualquier carpeta):  python3 scripts/armar_zip.py
Antes: python3 scripts/resumen_pdf.py y python3 scripts/informe_pdf.py
"""
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NOMBRE_ZIP = "ML1_PFI_ArbolesDeIndecision.zip"

# Nombre dentro del zip → archivo del repositorio (cada documento existe una sola vez)
ARCHIVOS = {
    "informe_PFI.pdf": "entrega/informe_PFI.pdf",
    "resumen_ejecutivo_EN.pdf": "entrega/resumen_ejecutivo_EN.pdf",
    "cuaderno_PFI.ipynb": "entrega/cuaderno_PFI.ipynb",
    "ficha_datos.md": "retos/modulo-2b/ficha_datos.md",
    "declaracion_IA.md": "declaracion_IA.md",
    "anexo_A_enfoque.md": "entrega/anexo_A_enfoque.md",
    "anexo_B_datos_reales.md": "entrega/anexo_B_datos_reales.md",
    "datos_crudos/LEEME.md": "datos_crudos/LEEME.md",
}
# PDF → fuente de la que se genera: el PDF no puede ser más viejo que su fuente
PDF_FUENTE = {
    "entrega/informe_PFI.pdf": ["entrega/informe_PFI.md"],
    "entrega/resumen_ejecutivo_EN.pdf": ["retos/modulo-3/cierre_R18.md"],
}


def main() -> None:
    faltan = [r for r in ARCHIVOS.values() if not (RAIZ / r).is_file()]
    if faltan:
        sys.exit(f"Faltan archivos: {', '.join(faltan)}")

    pendientes = [r for r in ARCHIVOS.values() if r.endswith((".md", ".ipynb"))
                  and "[POR COMPLETAR" in (RAIZ / r).read_text(encoding="utf-8")]
    viejos = [pdf for pdf, fuentes in PDF_FUENTE.items()
              if any((RAIZ / f).stat().st_mtime > (RAIZ / pdf).stat().st_mtime for f in fuentes)]
    if viejos:
        sys.exit(f"PDF desactualizados frente a su fuente: {', '.join(viejos)}. Regenérelos con scripts/.")

    destino = RAIZ / NOMBRE_ZIP
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for nombre, ruta in ARCHIVOS.items():
            z.write(RAIZ / ruta, nombre)

    with zipfile.ZipFile(destino) as z:
        contenido = z.namelist()
    print(f"{NOMBRE_ZIP}: {len(contenido)} archivos, {destino.stat().st_size / 1e6:.1f} MB")
    for nombre in contenido:
        print("  ", nombre)
    if pendientes:
        print(f"Aviso: quedan marcas [POR COMPLETAR] en {', '.join(pendientes)}")


if __name__ == "__main__":
    main()
