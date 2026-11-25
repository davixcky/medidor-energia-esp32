GOAL: Mostrar que E.7 es un producto modular montable y que sus luces comunican los tres estados del firmware.
OUTPUT: Blender/FFmpeg, 1920 x 1080, 24 fps, 38 s (912 fotogramas), H.264 + AAC + subtítulos en español.
LOOK: fondo #111820; gabinete grafito; guarda de red naranja translúcida; FCOB verde/ámbar/rojo como único acento variable; tipografía sans 44/25 px.
OBJECTS: gabinete E.7 con tapa suelta de cierre magnético, difusor hexagonal de la FCOB, LCD, encoder, dos pulsadores, LED D8 verde, piezo 44 mm empotrado, FCOB 200 mm, T1–T5, borneras, JST-XH, potenciómetros, ESP32S V1.1 USB-C, arneses y zona de red con guarda.
MOTION: planos unidos por corte; cámara con movimiento lento dentro de cada plano; tapa en 48 fotogramas; estados LED por corte.
SHOTS: hero cerrado verde; fila de controles; verde fijo; ámbar a 1 Hz; rojo a 5 Hz; apertura; planta con rótulos T1–T5; conexiones y ESP32S; zona de red; cierre y verde.
BANNED: LED tipo ecualizador; colores distintos entre segmentos FCOB; LED D8 en otro color; piezas flotando; arneses desconectados; afirmar que el render es prueba física.
QA: `verificar.py` sin fallos; hoja de contacto revisada; cinco tarjetas visibles; estado final verde y cerrado.
