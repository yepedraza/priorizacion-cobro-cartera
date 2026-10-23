"""Arma entrega/informe_PFI.pdf desde entrega/informe_PFI.md, con los gráficos de entrega/figuras/.

Verifica el límite de Canvas: hasta 15 páginas sin contar anexos (todo lo que va desde
«## Anexos y referencias»).

Uso (desde cualquier carpeta):  python3 scripts/informe_pdf.py
Antes: ../.venv/bin/python scripts/figuras_informe.py   (genera los gráficos)
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
FUENTE = RAIZ / "entrega" / "informe_PFI.md"
SALIDA = RAIZ / "entrega" / "informe_PFI.pdf"
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
MAX_PAGINAS = 15
INICIO_ANEXOS = "## Anexos y referencias"

CSS = """@page{size:A4;margin:2.2cm 2.3cm}
body{font:10.5pt/1.42 Calibri,Arial,sans-serif;color:#111}
h1{font-size:17pt;margin:0 0 .4em;line-height:1.2}
h2{font-size:13pt;margin:1.1em 0 .4em;break-after:avoid}
p{margin:0 0 .6em;text-align:justify}
blockquote{margin:0 0 1em;padding:.4em .8em;border-left:3px solid #2a78d6;background:#f4f8fd;font-size:9.5pt}
blockquote p{margin:0;text-align:left}
table{border-collapse:collapse;width:100%;font-size:8.8pt;margin:.3em 0 .9em;break-inside:avoid}
th,td{border:1px solid #c9c8c2;padding:3px 5px;vertical-align:top;text-align:left}
th{background:#f1f0ec}
code{font-family:Menlo,Consolas,monospace;font-size:8.6pt}
figure{margin:.4em 0 .9em;break-inside:avoid;text-align:center}
figure img{max-width:100%;max-height:7.2cm}
figcaption{font-size:8.6pt;color:#52514e;margin-top:.2em;text-align:left}
.anexos{break-before:page}"""


def inline(texto: str) -> str:
    t = html.escape(texto, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<i>\1</i>", t)


def a_html(md: str, base: Path) -> str:
    lineas, salida, i = md.split("\n"), [], 0
    while i < len(lineas):
        linea = lineas[i]
        if not linea.strip():
            i += 1
        elif linea.startswith("|"):
            filas = []
            while i < len(lineas) and lineas[i].startswith("|"):
                filas.append([c.strip() for c in lineas[i].strip().strip("|").split("|")])
                i += 1
            cuerpo = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in f) + "</tr>" for f in filas[2:])
            salida.append("<table><tr>" + "".join(f"<th>{inline(c)}</th>" for c in filas[0]) + f"</tr>{cuerpo}</table>")
        elif m := re.match(r"!\[(.*)\]\((.+)\)", linea):
            ruta = (base / m.group(2)).resolve()
            if not ruta.exists():
                sys.exit(f"Falta el gráfico {ruta}: ejecute antes scripts/figuras_informe.py")
            salida.append(f'<figure><img src="{ruta.as_uri()}"><figcaption>{inline(m.group(1))}</figcaption></figure>')
            i += 1
        elif m := re.match(r"(#{1,3}) (.*)", linea):
            clase = ' class="anexos"' if linea.startswith(INICIO_ANEXOS) else ""
            salida.append(f"<h{len(m.group(1))}{clase}>{inline(m.group(2))}</h{len(m.group(1))}>")
            i += 1
        elif linea.startswith(">"):
            bloque = []
            while i < len(lineas) and lineas[i].startswith(">"):
                bloque.append(inline(lineas[i][1:].strip()))
                i += 1
            salida.append("<blockquote><p>" + "<br>".join(bloque) + "</p></blockquote>")
        else:
            parrafo = []
            while i < len(lineas) and lineas[i].strip() and not re.match(r"[|#>]|!\[", lineas[i]):
                parrafo.append(lineas[i].strip())
                i += 1
            salida.append(f"<p>{inline(' '.join(parrafo))}</p>")
    return "\n".join(salida)


def imprimir(md: str, destino: Path, tmp: Path) -> int:
    pagina = tmp / (destino.stem + ".html")
    pagina.write_text(f"<!doctype html><meta charset=utf-8><title>Informe PFI</title><style>{CSS}</style>"
                      + a_html(md, FUENTE.parent), encoding="utf-8")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer", "--allow-file-access-from-files",
                    f"--print-to-pdf={destino}", pagina.as_uri()], check=True, capture_output=True)
    return len(re.findall(rb"/Type\s*/Page[^s]", destino.read_bytes()))


def main() -> None:
    md = FUENTE.read_text(encoding="utf-8")
    if INICIO_ANEXOS not in md:
        sys.exit(f"No se encontró «{INICIO_ANEXOS}» en {FUENTE}")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        cuerpo = imprimir(md.split(INICIO_ANEXOS)[0], tmp / "cuerpo.pdf", tmp)
        total = imprimir(md, SALIDA, tmp)
    print(f"{SALIDA.relative_to(RAIZ)}: {cuerpo} páginas sin anexos ({total} en total)")
    pendientes = md.count("[POR COMPLETAR")
    if pendientes:
        print(f"Aviso: quedan {pendientes} marcas [POR COMPLETAR]")
    if cuerpo > MAX_PAGINAS:
        sys.exit(f"El cuerpo tiene {cuerpo} páginas; Canvas pide hasta {MAX_PAGINAS} sin anexos.")


if __name__ == "__main__":
    main()
