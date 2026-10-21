import { createFileRoute } from '@tanstack/react-router'
import { json, nodoDe } from '#/server/http'
import { ultimo } from '#/server/servicio'

/** GET /api/ultimo?nodo= — último registro recibido. */
export const Route = createFileRoute('/api/ultimo')({
  server: { handlers: { GET: async ({ request }) => json((await ultimo(await nodoDe(request))) ?? null) } },
})
