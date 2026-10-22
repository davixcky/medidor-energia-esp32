"""Convierte las pantallas PPM dibujadas por ./pantallas en las figuras del documento.

  python3 componer_pantallas.py salida ../../img

ui-lcd-pantallas.png: las cuatro páginas del ciclo de SW1, la alerta y la tara, cada una dentro del
marco del módulo Waveshare de 1,9" (área activa 42,72 × 22,70 mm sobre un módulo de 51,2 × 27,3 mm).
ui-lcd-<nombre>.png: cada pantalla sola, al doble de tamaño.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ESCALA = 2
ORDEN = [("resumen", "1. Resumen"), ("ch1", "2. CH1"), ("ch2", "3. CH2"),
         ("energia", "4. Energía hoy"), ("alerta", "Alerta (CH1 sobre el umbral)"),
         ("tara", "Tara de un canal (SW2 sostenido 2 s)")]


def fuente(tam):
    candidatas = ["DejaVuSans.ttf", "/usr/share/fonts/TTF/DejaVuSans.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/noto/NotoSans-Regular.ttf"]
    try:
        import matplotlib
        candidatas.append(f"{matplotlib.get_data_path()}/fonts/ttf/DejaVuSans.ttf")
    except ImportError:
        pass
    for nombre in candidatas:
        try:
            return ImageFont.truetype(nombre, tam)
        except OSError:
            pass
    return ImageFont.load_default()


def modulo(pantalla):
    """Pantalla dentro del marco negro del módulo, con las proporciones reales."""
    w, h = pantalla.size
    px_mm = w / 42.72
    mw, mh = round(51.2 * px_mm), round(27.3 * px_mm)
    marco = Image.new("RGB", (mw, mh), (8, 8, 9))
    d = ImageDraw.Draw(marco)
    d.rounded_rectangle([0, 0, mw - 1, mh - 1], radius=round(1.5 * px_mm), outline=(40, 40, 44), width=2)
    # La ventana va desplazada hacia el lado contrario al conector.
    x = round(2.0 * px_mm)
    marco.paste(pantalla, (x, (mh - h) // 2))
    return marco


def main(origen, destino):
    origen, destino = Path(origen), Path(destino)
    grandes = {}
    for ppm in sorted(origen.glob("*.ppm")):
        img = Image.open(ppm).convert("RGB").resize((320 * ESCALA, 170 * ESCALA), Image.NEAREST)
        img.save(destino / f"ui-lcd-{ppm.stem}.png")
        grandes[ppm.stem] = img

    tarjetas = [(modulo(grandes[n]), t) for n, t in ORDEN]
    tw, th = tarjetas[0][0].size
    sep, alto_texto, cols = 40, 44, 2
    filas = (len(tarjetas) + cols - 1) // cols
    lienzo = Image.new("RGB", (cols * tw + (cols + 1) * sep, filas * (th + alto_texto) + (filas + 1) * sep - 10),
                       (246, 241, 238))
    d = ImageDraw.Draw(lienzo)
    f = fuente(26)
    for k, (img, titulo) in enumerate(tarjetas):
        c, fl = k % cols, k // cols
        x = sep + c * (tw + sep)
        y = sep + fl * (th + alto_texto + sep)
        d.text((x, y), titulo, fill=(29, 21, 23), font=f)
        lienzo.paste(img, (x, y + alto_texto))
    lienzo.save(destino / "ui-lcd-pantallas.png")
    print(f"{len(grandes)} pantallas y ui-lcd-pantallas.png en {destino}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
