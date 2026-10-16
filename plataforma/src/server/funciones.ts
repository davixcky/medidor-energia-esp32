/** Funciones de servidor que usa la página (TanStack Start las convierte en llamadas RPC en el cliente). */
import { createServerFn } from '@tanstack/react-start'
import { tablero } from './servicio'

export const leerTablero = createServerFn({ method: 'GET' })
  .validator((d: { nodo?: string } | undefined) => d ?? {})
  .handler(({ data }) => tablero(data.nodo))
