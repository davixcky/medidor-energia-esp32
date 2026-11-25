# Terminal de pantalla LilyGO T4-S3

Este firmware convierte la T4-S3 en un terminal gráfico del medidor. Usa su
radio únicamente para recibir ESP-NOW; no accede a Internet, no lee ADC, no
integra energía y no decide alarmas. Si el enlace cae,
muestra `SIN DATOS` y conserva la última lectura con su antigüedad.

No hay UART, SPI ni I2C entre procesadores. En el producto solo necesita
alimentación:

| LilyGO | Fuente protegida |
|---|---|
| VBUS | +5 V protegido |
| GND | GND |

No conectar a la vez VBUS del arnés y USB-C. Para programarla, desconectar el
arnés de VBUS y usar USB-C. Compilar con `pio run` desde esta carpeta.

La plataforma y librerías siguen las versiones probadas por el repositorio
oficial LilyGo-AMOLED-Series. El diseño usa la pantalla horizontal 600 × 450 y
recibe paquetes binarios versionados de menos de 250 bytes por ESP-NOW.

La interfaz horizontal tiene cuatro vistas manuales: resumen, análisis por
canal, energía/costo y flujo animado. Nunca cambia de pantalla por tiempo. Las
cuatro pestañas permanecen accesibles en el encabezado; no se usa ningún botón físico.
La interacción principal es tocar una tarjeta:
abre una vista detallada con cálculos y un botón grande `VOLVER`. También se
pueden tocar los indicadores de página y los estados `ESP` y `SD`; el gesto
horizontal queda como atajo secundario. La LilyGO deriva localmente factor de potencia,
potencia aparente/reactiva, reparto de carga, proyección diaria y costo a partir
de los valores crudos enviados por el ESP32 principal.

Cada pulsación imprime `TOUCH down x=... y=...` y `TOUCH up ...` por USB. Esto
permite comprobar el controlador y la orientación desde `pio device monitor`
si una zona no responde.

El arranque y las vistas incluyen animaciones no bloqueantes de flujo, pulso y
actividad. El encabezado usa la marca CUC vigente publicada por la propia
Universidad de la Costa en su página de imagen institucional:
<https://www.cuc.edu.co/imagen-institucional-unicosta>.

La microSD está habilitada. Al detectar una tarjeta FAT32 crea
`/telemetry.csv` y guarda cada paquete junto con los cálculos derivados. Si no
hay tarjeta al arrancar, intenta montarla nuevamente cada 15 segundos y muestra
su estado en la pantalla de flujo.

