/** Aplica el esquema de supabase/migrations a la base de DATABASE_URL:  pnpm db:migrar */
import { cerrar, migrar } from '../src/server/db.ts'

await migrar()
await cerrar()
console.log('esquema aplicado')
