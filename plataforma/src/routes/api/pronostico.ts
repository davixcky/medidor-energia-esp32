import { createFileRoute } from '@tanstack/react-router'
import { json, nodoDe } from '#/server/http'
import { pronostico } from '#/server/servicio'

/** GET /api/pronostico?nodo=&h=48 — pronóstico horario del LSTM con intervalo del 90 %. */
export const Route = createFileRoute('/api/pronostico')({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const h = Math.min(48, Math.max(1, Number(new URL(request.url).searchParams.get('h') ?? 48)))
        return json(await pronostico(await nodoDe(request), h))
      },
    },
  },
})
