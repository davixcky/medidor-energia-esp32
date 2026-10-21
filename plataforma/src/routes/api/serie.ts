import { createFileRoute } from '@tanstack/react-router'
import { json, nodoDe } from '#/server/http'
import { serie } from '#/server/servicio'

/** GET /api/serie?nodo=&horas=24&paso=300 — promedios por intervalo de P1, P2, V y FP1. */
export const Route = createFileRoute('/api/serie')({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const q = new URL(request.url).searchParams
        const horas = Math.min(24 * 31, Math.max(1, Number(q.get('horas') ?? 24)))
        const paso = Math.max(1, Number(q.get('paso') ?? 300))
        return json(await serie(await nodoDe(request), horas, paso))
      },
    },
  },
})
