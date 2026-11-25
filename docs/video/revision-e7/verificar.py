"""Verifica el MP4 final y escribe verificacion.json y contacto-final.png.

Comprueba contenedor y códecs, decodificación completa, sonoridad, número de
fotogramas y, sobre los píxeles decodificados del propio MP4: color común de
los cuatro segmentos FCOB, frecuencia de parpadeo del LED de panel y estado
verde final.  Son mediciones del archivo; nadie escuchó el audio.
"""
from pathlib import Path
import colorsys
import json
import re
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import linea_tiempo as lt

p = Path(__file__).resolve().parent
mp4 = p / 'medidor-E7-producto.mp4'
seg = json.loads((p / 'seguimiento.json').read_text(encoding='utf-8'))
W, H, N = 1920, 1080, lt.FRAMES
res, fallos = {}, []


def exigir(cond, texto):
    if not cond:
        fallos.append(texto)
    return bool(cond)


# ---------------------------------------------------------------- contenedor
info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', str(mp4)]))
v = next(s for s in info['streams'] if s['codec_type'] == 'video')
a = next(s for s in info['streams'] if s['codec_type'] == 'audio')
sub = [s for s in info['streams'] if s['codec_type'] == 'subtitle']
res['contenedor'] = {
    'video': f"{v['codec_name']} {v['profile']} {v['width']}x{v['height']} {v['r_frame_rate']} fps {v['pix_fmt']}",
    'fotogramas_decodificados': int(v['nb_read_frames']), 'audio': f"{a['codec_name']} {a['profile']} {a['sample_rate']} Hz {a['channels']} canales",
    'subtitulos': [f"{s['codec_name']} ({s['tags'].get('language')})" for s in sub],
    'duracion_s': float(info['format']['duration']), 'tamano_bytes': int(info['format']['size']),
}
exigir((v['width'], v['height']) == (W, H), 'no es Full HD')
exigir(v['codec_name'] == 'h264' and v['r_frame_rate'] == f'{lt.FPS}/1', 'no es H.264 a 24 fps')
exigir(int(v['nb_read_frames']) == N, f"fotogramas {v['nb_read_frames']} != {N}")
exigir(a['codec_name'] == 'aac', 'audio no es AAC')
exigir(abs(float(info['format']['duration']) - lt.DUR) < .05, 'duración distinta de 38 s')
exigir(sub and sub[0]['tags'].get('language') == 'spa', 'sin subtítulos en español')

# ---------------------------------------------------------------- decodificación completa y sonoridad
dec = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(mp4), '-f', 'null', '-'], capture_output=True, text=True)
res['decodificacion_completa'] = {'errores': dec.stderr.strip().splitlines(), 'ok': dec.returncode == 0 and not dec.stderr.strip()}
exigir(res['decodificacion_completa']['ok'], 'errores de decodificación')
eb = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(mp4), '-map', '0:a', '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
fin = eb[eb.rindex('Summary:'):]
res['audio_medido'] = {'lufs_integrado': float(re.search(r'I:\s+(-?[\d.]+) LUFS', fin).group(1)), 'lra_lu': float(re.search(r'LRA:\s+(-?[\d.]+) LU', fin).group(1)),
                       'pico_real_dbtp': float(re.search(r'Peak:\s+(-?[\d.]+) dBFS', fin).group(1)), 'escucha_humana': False}
exigir(-17.5 <= res['audio_medido']['lufs_integrado'] <= -14.5, 'sonoridad fuera de -16 ± 1,5 LUFS')
exigir(res['audio_medido']['pico_real_dbtp'] <= -1.0, 'pico real por encima de -1 dBTP')

# ---------------------------------------------------------------- píxeles del MP4
proc = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', str(mp4), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
TONO = {'verde': 153, 'ambar': 22, 'rojo': 0}   # tono HSV de (0,18,10), (24,9,0) y (32,0,0)
contacto_idx = [lt.frame_de(t) for t in np.linspace(.6, lt.DUR - .9, 20)]
miniaturas, led_muestras, fcob = {}, {}, {'fotogramas': 0, 'max_dif_tono': 0.0, 'max_dif_rgb': 0.0, 'errores': []}
f_final = lt.frame_de(lt.DUR - 1.1)
final = None


def parche(img, pt, r=3):
    x, y = int(round(pt['x'])), int(round(pt['y']))
    return img[max(y - r, 0):y + r + 1, max(x - r, 0):x + r + 1].reshape(-1, 3).mean(0)


def tono(rgb):
    return colorsys.rgb_to_hsv(*(rgb / 255))[0] * 360


def dif_tono(a_, b_):
    d = abs(a_ - b_) % 360
    return min(d, 360 - d)


for frame in range(1, N + 1):
    raw = proc.stdout.read(W * H * 3)
    if len(raw) < W * H * 3:
        fallos.append(f'flujo de video truncado en el fotograma {frame}')
        break
    img = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
    t, s = lt.tiempo(frame), seg['frames'][str(frame)]
    est = lt.estado(t)
    if frame in contacto_idx:
        miniaturas[frame] = Image.fromarray(img).resize((480, 270), Image.LANCZOS)
    # Lejos de fundidos y de la franja de títulos; a 2 fotogramas de un cambio de estado por el códec.
    estable = all(lt.estado(lt.tiempo(frame + k)) == est for k in (-2, 2)) and .5 < t < lt.DUR - .6
    zonas = s['fcob']
    if estable and all(z['visible'] and z['y'] > 175 and 12 < z['x'] < W - 12 for z in zonas):
        cols = [parche(img, z) for z in zonas]
        tonos = [tono(c) for c in cols]
        dt = max(dif_tono(tonos[0], x) for x in tonos)
        fcob['fotogramas'] += 1
        fcob['max_dif_tono'] = max(fcob['max_dif_tono'], dt)
        fcob['max_dif_rgb'] = max(fcob['max_dif_rgb'], float(max(np.abs(c - cols[0]).max() for c in cols)))
        if dt > 12 or any(dif_tono(x, TONO[est]) > 25 for x in tonos):
            fcob['errores'].append({'fotograma': frame, 'estado': est, 'tonos': [round(x) for x in tonos]})
        if frame == f_final:
            final = {'fotograma': frame, 't_s': round(t, 2), 'tonos_fcob': [round(x) for x in tonos], 'apertura_tapa': seg['apertura'][str(frame)]}
    if s['led']['visible'] and s['led']['y'] > 175:
        led_muestras[frame] = float(parche(img, s['led'], 2)[1])
proc.stdout.close()
proc.wait()

fcob['max_dif_tono'], fcob['max_dif_rgb'] = round(fcob['max_dif_tono'], 1), round(fcob['max_dif_rgb'], 1)
res['fcob_cuatro_segmentos'] = fcob
exigir(fcob['fotogramas'] > 200 and not fcob['errores'], 'los segmentos FCOB no comparten color en algún fotograma')
res['estado_final'] = final
exigir(final and all(dif_tono(x, TONO['verde']) < 25 for x in final['tonos_fcob']) and final['apertura_tapa'] == 0, 'el final no es verde y cerrado')

# LED: brillo del canal verde frente al modelo del firmware, fotograma a fotograma.
res['led_panel'] = {}
for est, hz in (('ambar', 1.0), ('rojo', 5.0)):
    t0, t1 = lt.T[est], lt.T['rojo' if est == 'ambar' else 'normal']
    fr_ = [f for f in range(lt.frame_de(t0), lt.frame_de(t1)) if f in led_muestras]
    val = np.array([led_muestras[f] for f in fr_])
    umbral = (val.min() + val.max()) / 2
    medido = val > umbral
    esperado = np.array([lt.led_encendido(lt.tiempo(f)) for f in fr_])
    flancos = int(np.sum(~medido[:-1] & medido[1:]))
    periodos = np.diff([fr_[i + 1] for i in range(len(fr_) - 1) if not medido[i] and medido[i + 1]]) / lt.FPS
    res['led_panel'][est] = {'fotogramas': len(fr_), 'flancos_de_subida': flancos, 'frecuencia_medida_hz': round(float(1 / periodos.mean()), 2) if len(periodos) else None,
                             'frecuencia_firmware_hz': hz, 'coincidencia_con_firmware': round(float((medido == esperado).mean()), 3),
                             'contraste_verde_8bit': [round(float(val.min())), round(float(val.max()))]}
    r = res['led_panel'][est]
    exigir(r['frecuencia_medida_hz'] and abs(r['frecuencia_medida_hz'] - hz) < .08 * hz and r['coincidencia_con_firmware'] > .95, f'LED en {est}: no se miden {hz} Hz')
fijo = [led_muestras[f] for f in range(lt.frame_de(lt.T['verde'] + .2), lt.frame_de(lt.T['ambar'])) if f in led_muestras]
res['led_panel']['verde'] = {'fotogramas': len(fijo), 'verde_min_8bit': round(min(fijo)), 'fijo': min(fijo) > 150}
exigir(res['led_panel']['verde']['fijo'], 'LED no queda fijo en estado normal')

# Gabinete abierto: las cinco tarjetas dentro de cuadro y sin tapar (trazado de rayos de Blender).
res['cinco_tarjetas_visibles'] = {'fotograma': seg['frame_planta'], 'tarjetas': {k: bool(r['visible'] and r['esquina']['visible']) for k, r in seg['rotulos'].items()}}
exigir(len(res['cinco_tarjetas_visibles']['tarjetas']) == 5 and all(res['cinco_tarjetas_visibles']['tarjetas'].values()), 'no se ven las cinco tarjetas')

# ---------------------------------------------------------------- hoja de contacto
fuente = ImageFont.truetype(subprocess.check_output(['fc-match', '-f', '%{file}', 'DejaVu Sans:bold'], text=True), 18)
hoja = Image.new('RGB', (5 * 484 + 4, 4 * 274 + 4), (12, 16, 22))
for i, frame in enumerate(contacto_idx):
    im = miniaturas[frame]
    d = ImageDraw.Draw(im)
    d.rectangle([0, 244, 150, 270], fill=(0, 0, 0))
    d.text((6, 247), f'{lt.tiempo(frame):05.2f} s · {lt.estado(lt.tiempo(frame))}', font=fuente, fill=(255, 255, 255))
    hoja.paste(im, (4 + (i % 5) * 484, 4 + (i // 5) * 274))
hoja.save(p / 'contacto-final.png')

res['valido'], res['fallos'] = not fallos, fallos
res['limites'] = 'Mediciones sobre el MP4. No hubo escucha humana del audio. El render no valida aislamiento, calibración ni seguridad del prototipo.'
(p / 'verificacion.json').write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(res, indent=1, ensure_ascii=False))
raise SystemExit(1 if fallos else 0)
