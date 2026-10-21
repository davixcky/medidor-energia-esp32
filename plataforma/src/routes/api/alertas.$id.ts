import { createFileRoute } from '@tanstack/react-router'
import { json } from '#/server/http'
import { cambiarEstado, eventos } from '#/server/servicio'

/** PATCH /api/alertas/:id con {"estado": "notificada" | "revisada" | "descartada"}. */
export const Route = createFileRoute('/api/alertas/$id')({
  server: {
    handlers: {
      PATCH: async ({ request, params }) => {
        try {
          const { estado } = (await request.json()) as { estado: string }
          if (!(await cambiarEstado(Number(params.id), estado))) return json({ error: 'no existe' }, 404)
          eventos.emit('alerta', { id: Number(params.id), estado })
          return json({ ok: true })
        } catch (e) {
          return json({ error: (e as Error).message }, 400)
        }
      },
    },
  },
})
