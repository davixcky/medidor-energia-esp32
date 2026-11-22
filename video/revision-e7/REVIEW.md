# Revisión del video E.7

Revisado el 2026-11-20 sobre `medidor-E7-producto.mp4`: hoja de contacto de
20 fotogramas (`contacto-final.png`) y `verificar.py` sin fallos
(`verificacion.json`). El video anterior (commit `1d3add8`) se descartó. Esta
versión sustituye la bisagra por cierre magnético y añade el difusor hexagonal.

## Qué se corrigió respecto al video anterior

- La tapa no tiene bisagra ni tornillos: cierra con imanes. En el video se
  levanta por atrás, bascula sobre su arista frontal y queda de pie con sus
  lengüetas en los bolsillos del gabinete; los tres arneses la siguen con su
  coca de holgura. Es la misma trayectoria que valida el CAD.
- La barra FCOB se ve a través del difusor hexagonal. El dibujo de celdas es
  un mapa de brillo según el espesor del difusor (0,3 / 0,5 / 1,1 mm), no una
  simulación óptica: la pieza impresa puede verse distinta.
- El LED de panel D8 queda siempre verde. Antes se pintaba ámbar y rojo, pero
  el firmware solo lo enciende y apaga con `digitalWrite`.
- La guarda de red permanece atornillada y se ve con la tapa cerrada.
- Aparecen la abertura del USB-C, los jacks de panel, el prensaestopa y los
  soportes de LCD, piezo, LED y FCOB.

## Mediciones del archivo

| Comprobación | Resultado |
|---|---|
| Video | H.264 High, 1920 × 1080, 24 fps, yuv420p |
| Fotogramas decodificados | 912 (38,0 s), sin errores de decodificación |
| Audio | AAC LC, 48 kHz, estéreo |
| Sonoridad | −16,2 LUFS integrados, pico real −1,4 dBTP, LRA 2,9 LU |
| Subtítulos | `mov_text`, español, 8 entradas |
| FCOB, cuatro segmentos | 369 fotogramas medidos; diferencia máxima de tono 1,8° |
| LED en ámbar | 1,00 Hz medido en 104 fotogramas; coincide con el firmware en todos |
| LED en rojo | 5,01 Hz medido en 75 fotogramas; coincide con el firmware en todos |
| LED en verde | fijo en los 48 fotogramas medidos |
| Estado final | fotograma 887 (36,92 s): tapa cerrada, cuatro segmentos en verde |
| Gabinete abierto | T1–T5 dentro de cuadro y sin tapar en el fotograma 638 |

No hubo escucha humana del audio: la revisión de sonido es métrica y de
decodificación. Los últimos 0,5 s funden a negro, por eso el estado final se
mide en 36,92 s.

## Revisión visual de la hoja de contacto

- 0–6 s: producto cerrado en verde, con la guarda naranja al fondo.
- 6–11 s: recorrido por LCD, pulsadores, encoder, LED y rejilla del piezo.
- 11–21 s: verde fijo, ámbar y rojo; la barra cambia de color completa y el
  LED aparece apagado en parte de los fotogramas de ámbar y rojo.
- 21–25 s: la tapa se suelta de los imanes y queda de pie al frente, vista
  desde atrás, con los arneses unidos a ella.
- 25–28 s: planta con los cinco rótulos T1–T5.
- 28–31 s: ESP32S, conectores JST-XH, bornera J5 y arneses.
- 31–34 s: zona de red con la guarda aclarada.
- 34–38 s: la tapa vuelve a su sitio y plano final en verde.

## Limitaciones conocidas

- En el plano de la zona de red el interior se distingue (ZMPT101B,
  portafusible, bornera J4 y cables) pero queda teñido de naranja y poco
  contrastado.
- El puerto USB-C solo se ve como abertura en la pared; ningún plano lo
  enfoca de cerca desde fuera. La vista `medidor-E7-trasera.png` sí lo muestra.
- La bornera J1 de T1 solo aparece en la planta, pequeña.
- Los imanes solo se ven como discos claros en las esquinas con la tapa
  levantada; ningún plano los enfoca de cerca. La vista
  `medidor-E7-cierre-magnetico.png` sí los muestra.
- Las pantallas LCD de «sin red» y «alerta» son ilustrativas.
- La tipografía «DejaVu Sans» no está instalada en este equipo; los títulos
  usan la fuente de sustitución del sistema.

Esta animación documenta la intención mecánica y funcional. No valida
aislamiento, calibración, temperatura ni seguridad del prototipo físico.
