# Medidor de energía eléctrica no invasivo de dos canales con ESP32

Sistemas Embebidos 1 · Ingeniería Electrónica · Universidad de la Costa (CUC) · Periodo 2026-2
**Integrantes:** David Orozco · Jose Torres · Leo Rojas

Medidor monofásico de 120 V / 60 Hz basado en ESP32. La corriente se mide sin abrir el circuito con
dos pinzas de núcleo partido SCT-013-000 (CH1 tablero, CH2 subcircuito) y la tensión con un módulo
aislado ZMPT101B. El ESP32 calcula valores eficaces, potencia activa, reactiva y aparente, factor de
potencia y THD, y los publica por Wi-Fi a una plataforma web que integra energía, abre alertas y
pronostica 48 h con una red LSTM.

| | |
|---|---|
| 📄 **Informe completo** | [`docs/informe.md`](docs/informe.md) — el documento académico, con cálculos, estado del arte y cronograma |
| 🌐 **Sitio del proyecto** | <https://davixcky.github.io/medidor-energia-esp32/> |
| 🔧 **Revisión vigente** | **E.9** — medidor en cinco tarjetas perforadas modulares |

---

## Mapa del repositorio

### 📐 Hardware

| Qué busco | Dónde está |
|---|---|
| **Esquemático** (revisión vigente E.9, tarjetas T1–T5) | [`hardware/perforadas-modulares/kicad/`](hardware/perforadas-modulares/kicad/) · [PDF T1–T5](hardware/perforadas-modulares/medidor-E9-esquematicos-T1-T5.pdf) · [vistas PNG](hardware/perforadas-modulares/schematic-previews/) |
| **Esquemático** (PCB original de una cara) | [`hardware/medidor-energia.kicad_sch`](hardware/medidor-energia.kicad_sch) · [PDF](hardware/medidor-energia.pdf) |
| **PCB** (una cara, fabricada por el grupo) | [`hardware/medidor-energia.kicad_pcb`](hardware/medidor-energia.kicad_pcb) |
| **BOM** por tarjeta (E.9) | [`BOM-E9-by-board.md`](hardware/perforadas-modulares/BOM-E9-by-board.md) · [CSV](hardware/perforadas-modulares/BOM-E9-by-board.csv) · [por tarjeta](hardware/perforadas-modulares/bom-por-tarjeta/) |
| **BOM** de precisión y componentes ya comprados | [`BOM-precision.md`](hardware/perforadas-modulares/BOM-precision.md) · [verificados](hardware/COMPONENTES-COMPRADOS-VERIFICADOS.md) |
| **Arquitectura** de las cinco tarjetas | [`ARQUITECTURA-E8.md`](hardware/perforadas-modulares/ARQUITECTURA-E8.md) |
| **Seguridad y protocolo de pruebas** | [`SEGURIDAD-Y-PRUEBAS.md`](hardware/perforadas-modulares/SEGURIDAD-Y-PRUEBAS.md) |
| **Fabricación**: Gerber, taladros, tóner, puentes | [`hardware/fabricacion/`](hardware/fabricacion/) · [`PUENTES.md`](hardware/fabricacion/PUENTES.md) |
| **Paquetes de construcción** (armar cada tarjeta) | [`construction-packets/`](hardware/perforadas-modulares/construction-packets/) · [pack E.9](hardware/perforadas-modulares/medidor-E9-construction-pack.pdf) |
| Banco de pruebas | [`hardware/banco-pruebas.kicad_sch`](hardware/banco-pruebas.kicad_sch) · [PDF](hardware/banco-pruebas.pdf) |
| Verificaciones ERC / DRC | [`erc.rpt`](hardware/erc.rpt) · [`drc.rpt`](hardware/drc.rpt) · [`erc-banco.rpt`](hardware/erc-banco.rpt) |
| Simulación en ngspice | [`simulacion/`](simulacion/) · [resultados](simulacion/resultados.md) |

### 💻 Firmware

| Carpeta | Objetivo | Qué hace |
|---|---|---|
| [`firmware/`](firmware/README.md) | ESP32-DevKitC V4 (WROOM) | Medidor: muestrea 8.000 muestras/s por canal, calcula, guarda sin red y envía tramas ADR-001 |
| [`firmware-lilygo/`](firmware-lilygo/README.md) | LilyGO T4-S3 AMOLED | Solo terminal gráfico por ESP-NOW. No mide ni decide alarmas |
| [`firmware-demo-sender/`](firmware-demo-sender/) | Cualquier ESP32 | Emite tramas de prueba contra la plataforma |
| [`shared/telemetry_packet.h`](shared/telemetry_packet.h) | — | Definición de la trama ADR-001 compartida |

### 🧊 Modelos 3D

| Carpeta | Contenido |
|---|---|
| [`freecad/revision-e7/`](freecad/revision-e7/README.md) | **Gabinete vigente (E.9)**: STL, 3MF listos para Bambu Studio, probetas de ajuste, [medidas](freecad/revision-e7/MEDIDAS.md) y [buenas prácticas](freecad/revision-e7/BEST-PRACTICES.md) |
| [`freecad/`](freecad/README.md) | Scripts base del gabinete y del banco, ensambles y [STL](freecad/stl/) |
| [`archivo/`](archivo/README.md) | Revisiones superadas (B y E.5) |

### 🌐 Web

| Carpeta | Contenido |
|---|---|
| [`plataforma/`](plataforma/README.md) | Plataforma: TanStack Start (React 19 + TypeScript), ingesta ADR-001, Postgres en Supabase, energía, alertas, LSTM y tablero en tiempo real. Incluye la **API** y el contrato de la trama |
| [`pronostico/`](pronostico/README.md) | Red LSTM en PyTorch: datos, entrenamiento y pesos |
| [`sitio/`](sitio/README.md) | Sitio del proyecto en Astro, publicado en GitHub Pages |
| [`stand/`](stand/README.md) | Kiosco del stand: página del QR, presentación para iPad y segunda pantalla HDMI |

### 🛠 Herramientas

Todo lo generado (esquemáticos, PCB, figuras, documentación) sale de scripts en
[`herramientas/`](herramientas/). Ver [el anexo del informe](docs/informe.md#10-anexo-archivos-fuente-y-cómo-regenerar-las-ilustraciones)
para regenerar el proyecto completo.

| Script | Para qué |
|---|---|
| [`generar_esquematico.py`](herramientas/generar_esquematico.py) | Genera el esquemático de KiCad del medidor |
| [`generar_kicad_perforadas.py`](herramientas/generar_kicad_perforadas.py) | Esquemáticos T1–T5 de la revisión E.9 |
| [`generar_pcb.py`](herramientas/generar_pcb.py) | PCB de una cara a partir de la netlist (Freerouting) |
| [`exportar_fabricacion.sh`](herramientas/exportar_fabricacion.sh) | Gerber, taladros, vistas 3D, STEP y DRC |
| [`generar_paquetes_construccion.py`](herramientas/generar_paquetes_construccion.py) | PDF para armar cada tarjeta |
| [`simulacion.py`](herramientas/simulacion.py) | Corre ngspice y escribe la tabla de resultados |
| [`figuras.py`](herramientas/figuras.py) | Diagrama de bloques, gabinetes y cronograma |
| [`verificar_enlaces.py`](herramientas/verificar_enlaces.py) | Comprueba que los enlaces de los `.md` resuelvan |

---

## Puesta en marcha

Cada parte es independiente: se puede levantar la plataforma sin tocar el hardware, y compilar el
firmware sin la plataforma.

### 1. Plataforma web (lo más rápido de ver)

Con Docker, sin instalar nada más y sin base de datos: levanta el modo de demostración, que genera
21 días de consumo simulado y luego un registro por segundo.

```bash
docker compose up web            # http://localhost:3000
```

Con Node directamente:

```bash
cd plataforma
pnpm install
pnpm build && DEMO=1 pnpm start  # http://localhost:3000
```

Con Postgres local en lugar de la demostración (incluido en el compose): levanta la base, le aplica
las migraciones y arranca la plataforma real en el puerto 3001.

```bash
docker compose --profile db up postgres migrar web-db   # http://localhost:3001
docker compose down -v                                  # para todo y borra los datos
```

Detalle completo —API, contrato ADR-001, variables de entorno, Supabase y pruebas— en
[`plataforma/README.md`](plataforma/README.md).

### 2. Firmware del medidor

Requiere [PlatformIO](https://platformio.org/install/cli).

```bash
cd firmware
cp include/secretos.h.ejemplo include/secretos.h   # red Wi-Fi y URL del servidor
pio run                                            # compila
make -C test                                       # prueba el cálculo en el PC, sin hardware
```

### 3. Herramientas de diseño

Para regenerar esquemáticos, PCB, modelos 3D y figuras: KiCad 10, FreeCAD 1.1, Blender, ngspice,
Graphviz, Python 3 con Matplotlib y Pillow, y Java + Freerouting 2.5 solo si hay que rutear de nuevo.
La secuencia completa está en [el anexo del informe](docs/informe.md#10-anexo-archivos-fuente-y-cómo-regenerar-las-ilustraciones).

### 4. Sitio del proyecto

```bash
cd sitio
pnpm install
pnpm dev                         # http://localhost:4321
```

---

## Cargar y subir

### Cargar el firmware en las placas

| Placa | Carpeta | Comandos |
|---|---|---|
| ESP32-DevKitC V4 (medidor) | `firmware/` | `pio run -t upload` y luego `pio device monitor` (115200 baudios) |
| LilyGO T4-S3 AMOLED (pantalla) | `firmware-lilygo/` | `pio run -t upload` |
| Emisor de prueba | `firmware-demo-sender/` | `pio run -t upload` |

```bash
cd firmware
cp include/secretos.h.ejemplo include/secretos.h   # obligatorio antes de cargar
pio run -t upload
pio device monitor
```

- `secretos.h` no está en Git. Sin él la compilación falla a propósito.
- Si hay varias placas conectadas, fijar el puerto: `pio run -t upload --upload-port /dev/cu.usbserial-XXXX`
  (en macOS, `ls /dev/cu.*` los lista).
- **La LilyGO no se programa con el arnés conectado.** Desconectar VBUS del arnés y usar solo
  USB-C; no alimentar por las dos vías a la vez. Ver [`firmware-lilygo/README.md`](firmware-lilygo/README.md).

### Subir los archivos de fabricación de la PCB

```bash
cd herramientas
./exportar_fabricacion.sh        # escribe hardware/fabricacion/: Gerber, taladros, vistas y DRC
```

Deja listos los archivos para el fabricante:

- **Gerber y taladros:** [`hardware/fabricacion/cnc/`](hardware/fabricacion/cnc/), ya empaquetados en
  [`gerbers-medidor.zip`](hardware/fabricacion/cnc/gerbers-medidor.zip). Es el archivo que se sube a
  JLCPCB (*Order now → Add gerber file*). La placa es de **una cara**: al cotizar hay que mantener
  2 capas o pedir 1 capa según el proceso, y revisar la vista previa de cobre y serigrafía antes de
  pagar.
- **Transferencia por tóner** (fabricación propia, es la que usó el grupo):
  [`toner/1-cobre-B_Cu-1a1.pdf`](hardware/fabricacion/toner/1-cobre-B_Cu-1a1.pdf) y
  [`2-serigrafia-F_SilkS-espejo-1a1.pdf`](hardware/fabricacion/toner/2-serigrafia-F_SilkS-espejo-1a1.pdf).
  **Imprimir al 100 %, sin ajustar a la página**, o las huellas no coinciden.
- **Puentes de alambre** obligatorios en una sola cara: [`PUENTES.md`](hardware/fabricacion/PUENTES.md).
- La revisión vigente E.9 **no se fabrica como PCB**: son cinco tarjetas perforadas que se arman a
  mano con los [paquetes de construcción](hardware/perforadas-modulares/construction-packets/).

Si hay una PCB impresa de por medio, conviene seguir también el protocolo de
[`SEGURIDAD-Y-PRUEBAS.md`](hardware/perforadas-modulares/SEGURIDAD-Y-PRUEBAS.md) antes de energizar.

### Subir las piezas 3D a la impresora

Los proyectos de Bambu Studio ya laminados están en
[`freecad/revision-e7/bambu/`](freecad/revision-e7/bambu/) — abrir el `.3mf` y enviar a la impresora.
Antes de imprimir el juego completo conviene sacar las
[probetas de ajuste](freecad/revision-e7/pruebas-de-ajuste/), que verifican los alojamientos de imán,
los jacks SCT y el prensaestopas. Los STL sueltos están en
[`freecad/revision-e7/stl/`](freecad/revision-e7/stl/).

### Publicar la plataforma web

- **Render:** *New → Blueprint* y elegir el repositorio; usa [`render.yaml`](render.yaml) de la raíz.
- **Railway:** *Deploy from GitHub repo*, con *Root Directory* = `plataforma` y la variable `DEMO=1`.
- **Con Supabase** en vez de la demostración: quitar `DEMO`, poner `DATABASE_URL` y correr una vez
  `pnpm db:migrar`.

Pasos detallados en [`plataforma/README.md`](plataforma/README.md).

### Publicar el sitio y el kiosco

El flujo [`.github/workflows/pages.yml`](.github/workflows/pages.yml) compila `sitio/` y publica,
en el mismo despliegue de GitHub Pages, las páginas del stand:

| URL | Qué es |
|---|---|
| `/` | Sitio del proyecto (es a donde apuntan los QR impresos) |
| `/kiosko.html` | Presentación del iPad |
| `/pantalla.html` | Segunda pantalla HDMI / Raspberry Pi |
| `/stand/` | Página anterior del QR, conservada como respaldo |

Requiere una vez: **Settings → Pages → Source: GitHub Actions**. Si cambia la URL hay que regenerar
el QR y volver a imprimir los llaveros: `python3 stand/generar_qr.py https://otra-url/`.

---

## Estructura

```
medidor-energia-esp32/
├── docs/informe.md            informe académico completo
├── hardware/                  esquemático · PCB · BOM · fabricación
│   └── perforadas-modulares/  revisión vigente E.9: tarjetas T1–T5
├── firmware/                  ESP32 del medidor (PlatformIO)
├── firmware-lilygo/           terminal gráfico LilyGO T4-S3
├── firmware-demo-sender/      emisor de tramas de prueba
├── shared/                    trama ADR-001 compartida
├── freecad/                   modelos 3D (revision-e7/ es la vigente)
├── plataforma/                plataforma web (TanStack Start + Docker)
├── pronostico/                red LSTM en PyTorch
├── simulacion/                netlists de ngspice
├── herramientas/              generadores de esquemáticos, PCB, figuras y documentación
├── interfaz/                  diagrama de navegación de la LCD
├── sitio/                     sitio del proyecto en Astro
├── stand/                     kiosco del stand (QR, iPad, HDMI) y llaveros
├── video/revision-e7/         video de producto vigente
├── img/                       ilustraciones del informe
└── archivo/                   revisiones superadas (B, E.5 y su video)
```

Los archivos pesados y regenerables (renders, `.step`, `.mp4`, `.blend`, g-code, `node_modules`) no
están en Git: se publican como archivos de las releases o se regeneran con los scripts.

## Licencia y uso

Trabajo académico de la Universidad de la Costa. El medidor maneja **120 V de red**: la zona de red
está separada del resto y el protocolo de
[`SEGURIDAD-Y-PRUEBAS.md`](hardware/perforadas-modulares/SEGURIDAD-Y-PRUEBAS.md) es obligatorio
antes de energizar.
