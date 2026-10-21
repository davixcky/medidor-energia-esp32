/** Utilidades comunes de las rutas de la API. */
import { nodos } from './servicio'

export const json = (datos: unknown, status = 200) =>
  new Response(JSON.stringify(datos), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' } })

/** Nodo pedido en ?nodo=, o el primero que haya enviado datos. */
export async function nodoDe(request: Request): Promise<string> {
  const n = new URL(request.url).searchParams.get('nodo')
  return n || (await nodos())[0] || 'nodo01'
}
