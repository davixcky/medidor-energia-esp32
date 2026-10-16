import { createFileRoute } from '@tanstack/react-router'
import { json, nodoDe } from '#/server/http'
import { alertas } from '#/server/servicio'

/** GET /api/alertas?nodo= — últimas alertas de consumo. */
export const Route = createFileRoute('/api/alertas/')({
  server: { handlers: { GET: ({ request }) => json(alertas(nodoDe(request), 100)) } },
})
