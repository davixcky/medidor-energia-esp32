# Componentes comprados verificados · Medidor de energía E.7

Este archivo es entrada obligatoria para cualquier agente que modifique el esquema, T1–T5, el gabinete, el CAD o el video. Solo registra evidencia del pedido Sigma `2140187`, el albarán I+D `BV/OUT/31035` y aclaraciones expresas del comprador; los carritos no equivalen a compras.

## Componentes asignados al medidor

| Tienda | Producto y enlace | Compra verificada | Uso previsto | Condición de diseño |
|---|---|---:|---|---|
| Sigma | [74HCT245 DIP-20](https://www.sigmaelectronica.net/producto/74hct245/) | 4 compartidos | 1 para U3 del medidor | No usar 74HC245; el HCT garantiza el umbral adecuado con señal de 3,3 V. |
| Sigma | [Zócalo DIP-20](https://www.sigmaelectronica.net/categoria-producto/conectores-y-cableado/conectores-pcb-de-insercion/) | 2 compartidos | 1 para U3 | Confirmar ancho 7,62 mm. |
| Sigma | [Regleta hembra 1×40, 2,54 mm](https://www.sigmaelectronica.net/categoria-producto/conectores-y-cableado/conectores-pcb-de-insercion/headers-hembra/) | 4 compartidas | Sockets ESP32S/LCD | ESP32S V1.1 USB-C y LCD deben ser removibles. |
| I+D | [1N5819 Schottky DO-41](https://www.didacticaselectronicas.com/shop?search=1N5819) | 3 | D1; quedan repuestos | Respetar orientación y encapsulado DO-41. |
| I+D | [Capacitor cerámico 100 nF/50 V, `CC0.1UF50V`](https://www.didacticaselectronicas.com/shop/cc0-1uf50v-capacitor-ceramico-0-1uf-50v-104-10717) | 20 compartidos | Desacoples | Dieléctrico y tolerancia no publicados; no declararlos X7R verificados. |
| I+D | [LED verde difuso 5 mm, `LED-5-VE-D`](https://www.didacticaselectronicas.com/shop?search=LED-5-VE-D) | 2 | Indicadores según BOM | Modelar 5 mm difuso. |
| I+D | [LED rojo difuso 3 mm, `LED-3-RO-D`](https://www.didacticaselectronicas.com/shop?search=LED-3-RO-D) | 1 | Indicador según BOM | Modelar 3 mm difuso. |
| I+D | [LED verde alta intensidad 3 mm, `LED-3-VE-C`](https://www.didacticaselectronicas.com/shop?search=LED-3-VE-C) | 1 | Indicador de panel | Es tipo chorro, no difuso. |
| I+D | [Pulsador metálico momentáneo 12 mm, `SW12BP`](https://www.didacticaselectronicas.com/shop?search=SW12BP) | 3 | SW1, SW2 + 1 repuesto | Sin iluminación; prever tuerca y profundidad posterior pendiente de medir. |
| I+D | [Jack DC de chasis 5,5×2,5 mm, `CON-156A`](https://www.didacticaselectronicas.com/shop?search=CON-156A) | 2 | Entrada DC + repuesto | No modelar jack 5,5×2,1 mm. |
| I+D | [Electrolítico 680 µF/16 V, `CE680UF16V`](https://www.didacticaselectronicas.com/shop?search=CE680UF16V) | 2 | C16 + repuesto | Low-ESR no está verificado. |
| I+D | [Electrolítico 470 µF/35 V, `CE470UF35V`](https://www.didacticaselectronicas.com/shop?search=CE470UF35V) | 2 | C1 + repuesto | Usar su tamaño físico real al recibirlo; no la huella hipotética de 16 V. |
| I+D | [Bornera puente verde 8 posiciones, `BOR-BRIG-8P-VE`](https://www.didacticaselectronicas.com/shop/bor-brig-8p-ve-bornera-en-puente-terminal-a-tierra-8-posiciones-verde-23667) | 2 compartidas | Distribución de alimentación cuando corresponda | Rotular por función; una bornera verde no significa automáticamente PE/GND del circuito. |

## Compras del mismo albarán que no deben asignarse automáticamente al medidor

| Producto | Motivo |
|---|---|
| [P-20K logarítmico](https://www.didacticaselectronicas.com/shop/p-20k-potenciometro-rotativo-de-20k-6295), 2 unidades | El medidor usa encoder EC11 y ajustes definidos por su esquema; no sustituirlos por estos potenciómetros sin rediseño. |
| [WS-14595, dos parlantes 8 Ω/5 W en un mismo conector](https://www.didacticaselectronicas.com/shop/ws-14595-parlante-8%CF%89-5w-11102) | Corresponde al ecualizador, no al medidor. El medidor utiliza piezo/buzzer. |
| [Portafusible `CON-183AC`](https://www.didacticaselectronicas.com/shop/con-183ac-portafusible-aereo-corto-5x20mm-17096) y [fusibles rápidos `FC-3A`](https://www.didacticaselectronicas.com/shop/fc-3a-fusible-corto-de-vidrio-3a-250v-13601) | El fusible de la zona de red del medidor debe conservar el valor/tipo definido en su esquema. No reemplazarlo por 3 A rápido. |
| LM324N, zócalos DIP-14 y 1N4148 | Asignados principalmente al ecualizador según su BOM actual. |

## Distribución del pedido Sigma

- 4 × 74HCT245: uno para el medidor, uno para el ecualizador y dos repuestos.
- 2 × zócalos DIP-20: uno para cada proyecto.
- 4 × regletas hembra 1×40: cortar únicamente las secciones requeridas por ESP32S y LCD.
- 5 × LM324N y 4 × zócalos DIP-14: asignación del ecualizador.
- 10 × 1N4148: asignación principal del ecualizador.

## Restricciones para CAD y video

- El controlador debe mostrarse como ESP32S V1.1 de 38 pines con USB-C.
- El jack de alimentación verificado es 5,5×2,5 mm.
- Los pulsadores son metálicos de panel, 12 mm y sin iluminación.
- No dibujar el `WS-14595` dentro del medidor: este proyecto lleva el piezo especificado.
- T1–T5 deben utilizar solo los componentes asignados por el esquema/BOM; los repuestos no se montan.
- Mantener físicamente segregada y cubierta la zona de red.

## Pendiente de evidencia

Las líneas de Electronilab, CVR y otras tiendas todavía no quedan confirmadas por los documentos recibidos. Mantenerlas como planificadas hasta recibir factura/albarán o confirmación explícita del comprador.
