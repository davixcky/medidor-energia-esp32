import { createFileRoute } from '@tanstack/react-router'
import { json, nodoDe } from '#/server/http'
import { ultimo } from '#/server/servicio'

/** GET /api/ultimo?nodo= — último registro recibido. */
export const Route = createFileRoute('/api/ultimo')({
  server: { handlers: { GET: ({ request }) => json(ultimo(nodoDe(request)) ?? null) } },
})
