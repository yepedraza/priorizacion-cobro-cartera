"""Arma entrega/resumen_ejecutivo_EN.pdf desde el §1 de retos/modulo-3/cierre_R18.md.

El texto vive solo en cierre_R18.md; este script no lo copia a otro archivo, solo lo lee, lo
maqueta y verifica los requisitos de Canvas: 1 página y entre 250 y 350 palabras.

Uso (desde cualquier carpeta):  python3 scripts/resumen_pdf.py
Requiere Google Chrome; en otra ubicación, definir la variable de entorno CHROME.
"""
import html
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FUENTE = RAIZ / "retos" / "modulo-3" / "cierre_R18.md"
SALIDA = RAIZ / "entrega" / "resumen_ejecutivo_EN.pdf"
TITULO = "Executive summary"
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
MIN_PALABRAS, MAX_PALABRAS = 250, 350

CSS = """@page{size:A4;margin:2.5cm}
body{font:11.5pt/1.45 Calibri,Arial,sans-serif;color:#111}
h1{font-size:17pt;margin:0 0 .8em}
p{margin:0 0 .75em;text-align:justify}"""


def parrafos_del_resumen() -> list[str]:
    texto = FUENTE.read_text(encoding="utf-8")
    m = re.search(r"^## 1\. Resumen ejecutivo \(English\)\n(.*?)(?=^## )", texto, re.S | re.M)
    if not m:
        sys.exit(f"No se encontró el §1 «Resumen ejecutivo (English)» en {FUENTE}")
    return [p.strip() for p in m.group(1).strip().split("\n\n") if p.strip()]


def a_html(parrafo: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(parrafo, quote=False))


def main() -> None:
    parrafos = parrafos_del_resumen()
    palabras = len(re.sub(r"\*\*", "", TITULO + " " + " ".join(parrafos)).split())
    if not MIN_PALABRAS <= palabras <= MAX_PALABRAS:
        sys.exit(f"El resumen tiene {palabras} palabras (título incluido); Canvas pide {MIN_PALABRAS} a {MAX_PALABRAS}.")

    cuerpo = "".join(f"<p>{a_html(p)}</p>" for p in parrafos)
    pagina = f"<!doctype html><meta charset=utf-8><title>{TITULO}</title><style>{CSS}</style><h1>{TITULO}</h1>{cuerpo}"

    with tempfile.TemporaryDirectory() as tmp:
        fuente_html = Path(tmp) / "resumen.html"
        fuente_html.write_text(pagina, encoding="utf-8")
        SALIDA.parent.mkdir(exist_ok=True)
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
             f"--print-to-pdf={SALIDA}", fuente_html.as_uri()],
            check=True, capture_output=True,
        )

    paginas = len(re.findall(rb"/Type\s*/Page[^s]", SALIDA.read_bytes()))
    if paginas != 1:
        sys.exit(f"El PDF tiene {paginas} páginas; Canvas pide 1.")
    print(f"{SALIDA.relative_to(RAIZ)}: {palabras} palabras (título incluido), {paginas} página")


if __name__ == "__main__":
    main()
