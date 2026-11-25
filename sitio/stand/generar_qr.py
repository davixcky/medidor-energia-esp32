"""Genera sitio/stand/img/qr.svg con la URL que abre el visitante.

Uso:  python3 sitio/stand/generar_qr.py [URL]
Requiere: pip install qrcode
"""
import sys
from pathlib import Path

import qrcode
import qrcode.image.svg

URL = sys.argv[1] if len(sys.argv) > 1 else "https://davixcky.github.io/medidor-energia-esp32/"

qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=2,
                   image_factory=qrcode.image.svg.SvgPathFillImage)
qr.add_data(URL)
qr.make(fit=True)
destino = Path(__file__).parent / "img" / "qr.svg"
qr.make_image().save(destino)
print(f"{destino}  ->  {URL}")
