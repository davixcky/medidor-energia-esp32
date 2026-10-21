import { createFileRoute } from '@tanstack/react-router'
import { json } from '#/server/http'
import { tablero } from '#/server/servicio'

/** GET /api/tablero?nodo= — todo lo que muestra el tablero en una sola respuesta. */
export const Route = createFileRoute('/api/tablero')({
  server: {
    handlers: {
      GET: async ({ request }) => json(await tablero(new URL(request.url).searchParams.get('nodo') ?? undefined)),
    },
  },
})
