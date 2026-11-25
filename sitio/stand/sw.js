// Guarda la presentación en el iPad para que funcione sin Wi-Fi en el stand.
//
// v4: la raíz del sitio ya no es esta carpeta, es el sitio del proyecto en Astro
// (ver .github/workflows/pages.yml). Se dejó de precargar './' e 'index.html'
// porque el kiosco no los necesita y sus hojas de estilo no están en esta lista.
// Subir el número de versión es lo que hace que el iPad descarte la copia anterior.
const CACHE = 'stand-v4';
const ARCHIVOS = [
  'kiosko.html', 'manifest.webmanifest',
  'img/qr.svg', 'img/icono.png', 'img/cerrado.jpg', 'img/abierto.jpg',
  'img/tablero.jpg', 'img/tablero-movil.jpg', 'img/bloques.jpg',
  'img/lstm-dia.jpg', 'img/esquematico.jpg', 'img/tft.png',
  'img/producto.mp4', 'img/producto-poster.jpg'
];
self.addEventListener('install', e => e.waitUntil(caches.open(CACHE).then(c => c.addAll(ARCHIVOS)).then(() => self.skipWaiting())));
self.addEventListener('activate', e => e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())));
// Safari pide el video por rangos (206); se responden desde la copia guardada.
async function conRango(req) {
  const r = await caches.match(req, { ignoreSearch: true });
  if (!r) return fetch(req);
  const rango = req.headers.get('range');
  if (!rango) return r;
  const buf = await r.arrayBuffer();
  const [, a, b] = /bytes=(\d*)-(\d*)/.exec(rango) || [];
  const ini = a ? +a : 0, fin = b ? +b : buf.byteLength - 1;
  return new Response(buf.slice(ini, fin + 1), { status: 206, headers: {
    'Content-Type': r.headers.get('Content-Type') || 'video/mp4',
    'Content-Range': `bytes ${ini}-${fin}/${buf.byteLength}`,
    'Content-Length': String(fin - ini + 1), 'Accept-Ranges': 'bytes' } });
}
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  if (e.request.headers.get('range')) { e.respondWith(conRango(e.request)); return; }
  e.respondWith(caches.match(e.request, { ignoreSearch: true }).then(r => r || fetch(e.request)));
});
