"""Genera MEDIDAS.md desde medidas-componentes.json y validacion-3d.json."""
from pathlib import Path
import json

p = Path(__file__).resolve().parent
d = json.loads((p / 'medidas-componentes.json').read_text(encoding='utf-8'))
val = json.loads((p / 'validacion-3d.json').read_text(encoding='utf-8'))
GRUPO = {'publicada': 'Publicadas', 'publicada_fabricante': 'Publicadas', 'publicada_nominal': 'Publicadas', 'publicada_fabricante_equivalente': 'Publicadas',
         'nominal': 'Nominales', 'diseño': 'Nominales'}


def cota(c):
    for k in ('envolvente', 'envolvente_usada', 'envolvente_reservada'):
        if k in c:
            v = c[k]
            return ' × '.join(f'{x:g}' for x in v) if isinstance(v, list) else '; '.join(f"{a.replace('_', ' ')} {b}" for a, b in v.items())
    return f"agujero {c.get('agujero_panel', '—')}"


out = ['# Medidas del modelo E.7', '', f"Revisión `{d['revision']}`, en milímetros. Generado por `informe_medidas.py`; no editar a mano.", '',
       '**Ninguna cota está confirmada con calibre sobre la pieza recibida.** «Publicada» significa que la da la tienda o el fabricante; '
       '«nominal», que sale de la norma o serie del componente; «conservadora», que el CAD reserva espacio de más hasta medir. '
       'La columna de compra sigue `hardware/COMPONENTES-COMPRADOS-VERIFICADOS.md`.', '']
grupos = {'Publicadas': [], 'Nominales': [], 'Conservadoras o mixtas': []}
pend = []
for nombre, c in d['componentes'].items():
    g = GRUPO.get(c['estado'], 'Conservadoras o mixtas')
    grupos[g].append(f"| `{nombre}` | {cota(c)} | {c.get('compra', '—')} | {c.get('detalle', '')} |")
    pend += [f"- `{nombre}`: {x}" for x in c.get('por_medir', [])]
for g, filas in grupos.items():
    out += [f'## {g}', '', '| Componente | Cota usada en el CAD | Compra | Nota |', '|---|---|---|---|', *filas, '']
out += ['## Pendientes de medir', '', *pend, '',
        '## Holguras comprobadas en el CAD', '',
        f"- Tapa suelta con imanes: recorre la trayectoria de servicio hasta quedar de pie en sus bolsillos sin interferencias ({len(val['interferencias_al_abrir'])} detectadas).",
        f"- Imanes: el más cercano al transformador del ZMPT101B queda a {min(m['distancia_a_transformador_ZMPT_mm'] for m in val['tapa']['imanes']):g} mm "
        f"(mínimo de diseño {val['tapa']['separacion_minima_exigida_mm']:g} mm; el efecto magnético no está medido).",
        f"- Difusor hexagonal: {val['difusor_hex']['celdas']} celdas, espesores {' / '.join(f'{t:g}' for t in val['difusor_hex']['espesores_mm'])} mm, "
        f"{val['difusor_hex']['distancia_fcob_a_piel_mm']:g} mm entre la FCOB y la piel.",
        f"- Piezas sin apoyo: {len(val['piezas_sin_apoyo'])} de {val['objetos']} objetos.", '',
        '| Puente de arnés | Vías | Largo | Radio de coca cerrada | Cuerda con tapa de pie | Cuerda máxima del recorrido | Holgura mínima | Separación a la pared frontal |', '|---|---:|---:|---:|---:|---:|---:|---:|']
out += [f"| {b['nombre']} | {b['vias']} | {b['longitud_mm']:g} | {b['radio_coca_cerrada_mm']:g} | {b['cuerda_estacionada_mm']:g} | {b['cuerda_maxima_mm']:g} | {b['holgura_minima_mm']:g} | {b['separacion_pared_frontal_mm']:g} |"
        for b in val['puentes_de_arnes']]
peor = min(val['arneses'], key=lambda h: h['relacion_radio_diametro'])
out += ['', f"Radio de curvatura mínimo entre los {len(val['arneses'])} arneses: {peor['radio_minimo_mm']:g} mm en `{peor['nombre']}` "
        f"({peor['relacion_radio_diametro']:g} diámetros). El criterio de 2,5 diámetros es de este diseño, no de una norma.", '',
        'Esto es una comprobación geométrica del modelo. No valida aislamiento, distancias normativas ni el prototipo físico.', '']
(p / 'MEDIDAS.md').write_text('\n'.join(out), encoding='utf-8')
