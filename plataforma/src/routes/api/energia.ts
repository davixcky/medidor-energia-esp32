import { createFileRoute } from '@tanstack/react-router'
import { json, nodoDe } from '#/server/http'
import { energia } from '#/server/servicio'

/** GET /api/energia?nodo= — energía de hoy, del mes por día y proyección del mes. */
export const Route = createFileRoute('/api/energia')({
  server: { handlers: { GET: async ({ request }) => json(await energia(await nodoDe(request))) } },
})
