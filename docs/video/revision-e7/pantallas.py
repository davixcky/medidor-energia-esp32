"""Pantallas LCD de los estados sin conexión y alerta, a 2x (640 x 340).

Siguen la geometría de firmware/lib/interfaz/interfaz.cpp (encabezado, barras
Wi-Fi tachadas, pantalla ALERTA).  La tipografía es aproximada: son imágenes
ilustrativas para el video, no capturas del equipo.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

p = Path(__file__).resolve().parent / 'assets'
ROJO, AMBAR, GRIS, TEXTO, TENUE = (0xE0, 0x3A, 0x2E), (0xE8, 0xA3, 0x3D), (0x4A, 0x40, 0x43), (0xF2, 0xEE, 0xE9), (0x9A, 0x90, 0x93)


def fuente(tam, negrita=True):
    for f in ('/usr/share/fonts/TTF/DejaVuSans-Bold.ttf' if negrita else '/usr/share/fonts/TTF/DejaVuSans.ttf',
              str(Path.home() / '.fonts/Roboto/Roboto-Bold.ttf')):
        if Path(f).is_file():
            return ImageFont.truetype(f, tam)
    return ImageFont.load_default(tam)


def wifi_sin_red(d, fondo):
    x, base = 292, 20
    d.rectangle([2 * (x - 2), 2 * (base - 14), 2 * (x + 20), 2 * (base + 2)], fill=fondo)
    for k in range(4):
        h = 4 + 3 * k
        d.rectangle([2 * (x + 5 * k), 2 * (base - h), 2 * (x + 5 * k + 3) - 1, 2 * base - 1], fill=GRIS)
    d.line([2 * (x - 1), 2 * (base - 13), 2 * (x + 18), 2 * base], fill=ROJO, width=4)


img = Image.open(p / 'lcd-resumen.png').convert('RGB')
wifi_sin_red(ImageDraw.Draw(img), img.getpixel((560, 8)))
img.save(p / 'lcd-sin-red.png')

img = Image.new('RGB', (640, 340), (0, 0, 0))
d = ImageDraw.Draw(img)
d.rectangle([0, 0, 640, 51], fill=ROJO)
d.rectangle([0, 0, 7, 51], fill=TEXTO)
d.text((24, 38), '! ALERTA  CH1', font=fuente(30), fill=TEXTO, anchor='ls')
d.text((24, 72), 'POTENCIA SOSTENIDA', font=fuente(17, False), fill=TENUE)
d.text((20, 164), '2360', font=fuente(84), fill=ROJO, anchor='ls')
d.text((250, 164), 'W', font=fuente(44), fill=TENUE, anchor='ls')
d.text((24, 224), 'Sobre el umbral de 2000 W', font=fuente(26, False), fill=TEXTO, anchor='ls')
d.text((24, 268), 'Durante 5 min', font=fuente(26, False), fill=TEXTO, anchor='ls')
d.rectangle([0, 292, 640, 340], fill=AMBAR)
d.text((320, 326), 'SW2: RECONOCER', font=fuente(28), fill=(0, 0, 0), anchor='ms')
img.save(p / 'lcd-alerta.png')
