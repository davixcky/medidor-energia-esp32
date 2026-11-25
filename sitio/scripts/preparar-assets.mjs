/**
 * Copia a sitio/public/ las ilustraciones que ya existen en el repositorio, para no
 * duplicarlas en Git. Se ejecuta solo antes de `astro dev` y `astro build`.
 *
 *   docs/img/ + sitio/stand/img/ -> public/img/      (mismo /img/ que espera el kiosco)
 *   renders E.9                ->  public/render/
 *   vistas de los esquemáticos ->  public/esquematicos/
 *
 * public/ está en .gitignore: es caché de construcción, no fuente.
 */
import { cp, mkdir, readdir, rm } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = resolve(AQUI, '../..');
const PUBLICO = resolve(AQUI, '../public');

/** Carpetas que se copian enteras al destino indicado. */
const CARPETAS = [
  ['docs/img', 'img'],
  ['sitio/stand/img', 'img'],
  ['hardware/perforadas-modulares/schematic-previews', 'esquematicos'],
];

/** Renders del gabinete vigente (E.9) que usa el sitio. */
const RENDERS = [
  'medidor-E7-cerrado.png',
  'medidor-E7-abierto.png',
  'medidor-E7-planta.png',
  'medidor-E7-trasera.png',
  'medidor-E7-tapa-interior.png',
  'medidor-E7-difusor.png',
  'medidor-E7-cierre-magnetico.png',
  'medidor-E8-pantalla-soporte-explotado.png',
  'medidor-E9-entradas-SCT.png',
  'medidor-E9-alimentacion-12V.png',
  'medidor-E9-ruta-alimentacion-interior.png',
  'tft-render-horizontal.png',
];

const faltantes = [];

async function copiarCarpeta(desde, hacia) {
  const origen = join(RAIZ, desde);
  if (!existsSync(origen)) {
    faltantes.push(desde);
    return 0;
  }
  const destino = join(PUBLICO, hacia);
  await mkdir(destino, { recursive: true });
  const entradas = await readdir(origen, { withFileTypes: true });
  let n = 0;
  for (const e of entradas) {
    if (e.name.startsWith('.')) continue;
    await cp(join(origen, e.name), join(destino, e.name), { recursive: true });
    n += 1;
  }
  return n;
}

async function copiarRenders() {
  const destino = join(PUBLICO, 'render');
  await mkdir(destino, { recursive: true });
  let n = 0;
  for (const nombre of RENDERS) {
    const origen = join(RAIZ, '3d/revision-e7', nombre);
    if (!existsSync(origen)) {
      faltantes.push(`3d/revision-e7/${nombre}`);
      continue;
    }
    await cp(origen, join(destino, nombre));
    n += 1;
  }
  return n;
}

// Se limpia primero para que un archivo borrado del repositorio no sobreviva en la caché.
await rm(PUBLICO, { recursive: true, force: true });
await mkdir(PUBLICO, { recursive: true });

let total = 0;
for (const [desde, hacia] of CARPETAS) {
  const n = await copiarCarpeta(desde, hacia);
  total += n;
  console.log(`  ${desde} -> public/${hacia}  (${n})`);
}
const nr = await copiarRenders();
total += nr;
console.log(`  3d/revision-e7 -> public/render  (${nr})`);

console.log(`${total} archivos preparados en sitio/public/`);

if (faltantes.length) {
  console.error(`\nFaltan ${faltantes.length} archivos esperados:`);
  for (const f of faltantes) console.error(`  ✗ ${f}`);
  process.exit(1);
}
