# Plataforma del medidor de energía

Aplicación web del medidor: recibe los registros del ESP32, los guarda en Supabase (Postgres), calcula la
energía, las alertas y el pronóstico, y los muestra en un tablero en tiempo real. Está hecha con **TanStack Start** (React 19,
TypeScript y rutas por archivo de TanStack Router); el *frontend* y el *backend* viven en la misma
aplicación y se sirven con un solo proceso de Node.

## Arquitectura

```
ESP32 (firmware)  ──POST /api/ingesta (tramas ADR-001 de 40 B)──►  Servidor TanStack Start (Node ≥ 22.13)
pnpm simular      ──────────────── mismo formato ───────────────►   ├─ src/server/adr001.ts    decodificación y validación
                                                                    ├─ src/server/servicio.ts  energía, P95, alertas, pronóstico
                                                                    ├─ src/server/lstm.ts      inferencia del LSTM en TypeScript
                                                                    ├─ src/server/db.ts        conexión a Supabase (postgres.js)
                                                                    └─ src/routes/api/*        API REST y eventos SSE
Navegador  ◄── HTML con datos (función de servidor) + /api/eventos (SSE, 1 Hz) ──  src/routes/index.tsx (tablero)
```

- **Almacenamiento:** Postgres en Supabase, con el controlador `postgres` (postgres.js) y la cadena de
  conexión en `DATABASE_URL`. El esquema está en
  [`supabase/migrations/20261021000000_medidor.sql`](supabase/migrations/20261021000000_medidor.sql):
  `registros` (cada trama), `horas` (energía integrada por hora y canal), `umbrales` (P95 por canal) y
  `alertas`. Las tablas tienen RLS activo y sin políticas, de modo que la API pública de Supabase (clave
  `anon`) no las puede leer; solo el servidor, que se conecta directamente, lee y escribe.
- **Ingesta por lotes:** cada `POST /api/ingesta` se guarda en una transacción. Los registros se
  insertan de una vez (`ON CONFLICT DO NOTHING` descarta los repetidos) y la energía por hora se acumula
  en memoria antes de escribirla, para no hacer un viaje a la base por cada registro.
- **Energía:** cada registro aporta $P \cdot \Delta t$, donde $\Delta t$ es el tiempo hasta el registro
  anterior; las brechas de más de 60 s (nodo sin red) no se integran.
- **Alertas:** se abre una alerta cuando la potencia de un canal supera el umbral durante 5 min o más. El
  umbral es el percentil 95 de la potencia de los últimos 21 días; se calcula cuando hay al menos un día
  de datos y se recalcula cada 7 días. Cada alerta queda notificada, revisada o descartada.
- **Pronóstico:** el LSTM de `../pronostico` (24 h × 4 variables → 32 → 16 → 1) corre en el servidor
  en TypeScript con los pesos exportados a `src/server/lstm-pesos.json`. Una prueba compara su salida con
  la de PyTorch (diferencia menor que 1e-4). Pronostica 48 h de forma recursiva a partir de las últimas
  24 horas completas de CH1. El intervalo del 90 % usa el RMSE de la prueba con los datos de UCI.
- **Temperatura del pronóstico:** el modelo necesita la temperatura de cada hora. Por defecto se usa un
  perfil diario típico de Barranquilla (25 °C a las 5 h y 32 °C a las 14 h); `TEMP_CONSTANTE=28` fija un
  valor único. Esos valores quedan en el extremo alto del rango con el que se entrenó el modelo (Sceaux,
  Francia: de −10,5 a 31,7 °C, media de 10,7 °C), con pocos ejemplos, y el tablero lo advierte.
- **Hora local:** los días y las horas se calculan en la hora de Colombia (UTC−5).

## Cómo ejecutar

Requiere Node 22.13 o superior (probado con Node 25), pnpm y un proyecto de Supabase.

```bash
cd plataforma
pnpm install
cp .env.ejemplo .env                      # poner la cadena de conexión de Supabase en DATABASE_URL
pnpm db:migrar                            # crea las tablas (o: supabase db push)
pnpm build && pnpm start                  # servidor de producción en http://localhost:3000
pnpm simular --dias 21                    # en otra terminal: 21 días de histórico y luego 1 registro/s
```

- Desarrollo con recarga en caliente: `pnpm dev`.
- Pruebas: `pnpm test` (decodificación ADR-001, LSTM frente a PyTorch, energía, P95, alertas y pronóstico).
  Las del servicio necesitan un Postgres en `DATABASE_URL` y se omiten sin él; no conviene apuntarlas al
  proyecto de producción porque vacían las tablas. Para un Postgres local de pruebas:
  `pnpm db:prueba` y luego `DATABASE_URL=postgres://postgres:prueba@localhost:54329/postgres pnpm test`.
- Capturas del tablero: `pnpm capturas` (usa Chrome instalado; escribe en `../img/ui-tablero-*.png`).
- Exportar de nuevo los pesos del LSTM tras reentrenarlo: `pnpm exportar-lstm`.
- Variables (en `.env`): `DATABASE_URL` (obligatoria salvo con `DEMO=1`), `DEMO`, `PORT` (3000),
  `DB_CONEXIONES` (5), `TEMP_CONSTANTE`.
- Sin Supabase: `DEMO=1 pnpm start` (ver el modo de demostración, abajo).

El simulador genera el consumo de una vivienda de la costa Caribe (carga base, nevera que cicla, aire
acondicionado en CH2, picos de cocina) y envía **exactamente** lo que enviará el ESP32: tramas binarias
ADR-001 con las cabeceras `X-Nodo` y `X-Firmware`. Su versión de *firmware* termina en `-sim`, y el
tablero muestra un aviso mientras los datos vengan del simulador. Opciones: `--url`, `--nodo`, `--dias`,
`--paso` (segundos entre registros del histórico, 10 por defecto) y `--solo-historico`.

## Modo de demostración y despliegue (Railway / Render)

Con `DEMO=1` el servidor no necesita Supabase. Al primer pedido levanta un Postgres en memoria
([PGlite](https://pglite.dev)) con la misma migración, carga 21 días del simulador (un registro cada
30 s, unos 5 s de arranque) a través de la misma función de ingesta que usa el ESP32 y luego agrega un
registro por segundo. Energía, umbrales P95, alertas y pronóstico salen del mismo código que en
producción, y el tablero muestra el aviso de datos del simulador. `POST /api/ingesta` sigue
funcionando, pero lo recibido vive en memoria y se pierde al reiniciar. Los registros de más de 22 días
se borran cada hora para que la memoria no crezca (el proceso ocupa unos 180 MB).

El `Dockerfile` de esta carpeta construye la imagen (Node 22, pnpm, `pnpm build`) y sirve
`.output/server/index.mjs`, que escucha en `PORT`.

- **Railway:** *New Project → Deploy from GitHub repo* → elegir el repositorio. En el servicio, *Settings →
  Source → Root Directory* = `plataforma` (Railway detecta el `Dockerfile`); en *Variables*, `DEMO=1`; en
  *Settings → Networking*, *Generate Domain*. `railway.json` fija la comprobación de salud en `/api/ultimo`
  (para que Railway lo lea, *Settings → Config-as-code → Railway Config File* = `/plataforma/railway.json`).
- **Render:** *New → Blueprint* → elegir el repositorio; usa `render.yaml` de la raíz (servicio web con
  Docker, carpeta `plataforma`, plan gratuito, `DEMO=1`). El plan gratuito se duerme tras 15 min sin
  visitas y el primer pedido tarda en despertar; al despertar se vuelven a generar los datos.
- **Con Supabase en lugar de la demostración:** quitar `DEMO`, poner `DATABASE_URL` y correr una vez
  `pnpm db:migrar` desde una máquina con esa variable.

## Contrato ADR-001 (40 B, little-endian, sin relleno)

| Desplazamiento | Tipo | Campo | Escala |
|---:|---|---|---|
| 0 | `uint32` | `t` | 1 s (época Unix, UTC) |
| 4 | `int16` | `v_rms` | 0,01 V |
| 6 | `int16[3]` | `i_rms` (CH1, CH2, CH3 de reserva) | 0,01 A |
| 12 | `int16[3]` | `p` | 1 W |
| 18 | `int16[3]` | `q` | 1 var |
| 24 | `int16[3]` | `s` | 1 VA |
| 30 | `int16[3]` | `fp` | 0,0001 (−1…1 → −10000…10000) |
| 36 | `int16` | `f` | 0,01 Hz |
| 38 | `int16` | `thd` (corriente de CH1) | 0,01 % |

## API

| Método y ruta | Descripción |
|---|---|
| `POST /api/ingesta` | Cuerpo `application/octet-stream` con uno o más registros de 40 B concatenados (el *firmware* agrupa los que guardó sin red), o `application/json` con un registro o una lista. Cabeceras `X-Nodo` y `X-Firmware`. Responde `200 {"aceptados": n}`; los duplicados (mismo nodo y `t`) se ignoran. `400` si el cuerpo no es múltiplo de 40 B o el JSON está mal formado; `422` si un valor está fuera de rango. |
| `GET /api/tablero?nodo=` | Todo lo que muestra el tablero en una respuesta. |
| `GET /api/ultimo?nodo=` | Último registro. |
| `GET /api/serie?nodo=&horas=24&paso=300` | Promedios de P1, P2, V y FP1 por intervalo. |
| `GET /api/energia?nodo=` | Energía de hoy, de ayer a la misma hora, del mes por día y proyección del mes. |
| `GET /api/pronostico?nodo=&h=48` | Pronóstico horario del LSTM con intervalo del 90 %. |
| `GET /api/alertas?nodo=` | Últimas alertas. |
| `PATCH /api/alertas/:id` | `{"estado": "notificada" \| "revisada" \| "descartada"}`. |
| `GET /api/eventos` | *Server-Sent Events*: `registro` con cada registro nuevo y `alerta` al abrir o cambiar una alerta. |

Si se omite `nodo`, se usa el primer nodo que haya enviado datos.

Ejemplo con un registro binario guardado en `trama.bin`:

```bash
curl -X POST http://localhost:3000/api/ingesta -H 'Content-Type: application/octet-stream' \
     -H 'X-Nodo: nodo01' -H 'X-Firmware: fw-v1.0.0' --data-binary @trama.bin
```
