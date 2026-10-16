import { createFileRoute } from '@tanstack/react-router'
import { type Registro, decodificarLote, desdeJson, validar } from '#/server/adr001'
import { json } from '#/server/http'
import { ingerir } from '#/server/servicio'

/**
 * POST /api/ingesta — recibe registros ADR-001 del ESP32.
 * - application/octet-stream: uno o más registros de 40 B concatenados.
 * - application/json: un registro o una lista de registros con la misma forma.
 * Cabeceras: X-Nodo (identificador del nodo) y X-Firmware (versión, p. ej. fw-v1.0.0).
 */
export const Route = createFileRoute('/api/ingesta')({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const nodo = request.headers.get('x-nodo')?.trim() || 'nodo01'
        const fw = request.headers.get('x-firmware')
        let registros: Registro[]
        try {
          if ((request.headers.get('content-type') ?? '').includes('json')) {
            const cuerpo = await request.json()
            registros = (Array.isArray(cuerpo) ? cuerpo : [cuerpo]).map(desdeJson)
          } else {
            registros = decodificarLote(await request.arrayBuffer())
          }
        } catch (e) {
          return json({ error: (e as Error).message }, 400)
        }
        for (const [k, r] of registros.entries()) {
          const motivo = validar(r)
          if (motivo) return json({ error: `registro ${k}: ${motivo}` }, 422)
        }
        return json({ aceptados: ingerir(nodo, fw, registros) })
      },
    },
  },
})
