import { createFileRoute } from '@tanstack/react-router'
import { eventos } from '#/server/servicio'

/**
 * GET /api/eventos — Server-Sent Events. Envía `registro` con cada registro nuevo (1 Hz por nodo)
 * y `alerta` cuando se abre una alerta o cambia su estado.
 */
export const Route = createFileRoute('/api/eventos')({
  server: {
    handlers: {
      GET: ({ request }) => {
        const enc = new TextEncoder()
        let limpiar = () => {}
        const stream = new ReadableStream({
          start(ctrl) {
            const enviar = (tipo: string) => (datos: unknown) => {
              try { ctrl.enqueue(enc.encode(`event: ${tipo}\ndata: ${JSON.stringify(datos)}\n\n`)) } catch { limpiar() }
            }
            const onReg = enviar('registro')
            const onAl = enviar('alerta')
            eventos.on('registro', onReg)
            eventos.on('alerta', onAl)
            const latido = setInterval(() => { try { ctrl.enqueue(enc.encode(': latido\n\n')) } catch { limpiar() } }, 15000)
            ctrl.enqueue(enc.encode('retry: 3000\n\n'))
            limpiar = () => {
              clearInterval(latido)
              eventos.off('registro', onReg)
              eventos.off('alerta', onAl)
            }
            request.signal.addEventListener('abort', () => { limpiar(); try { ctrl.close() } catch {} })
          },
          cancel() { limpiar() },
        })
        return new Response(stream, {
          headers: { 'content-type': 'text/event-stream', 'cache-control': 'no-cache, no-transform', connection: 'keep-alive', 'x-accel-buffering': 'no' },
        })
      },
    },
  },
})
