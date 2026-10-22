import { createFileRoute, useRouter } from '@tanstack/react-router'
import { useEffect, useMemo, useState } from 'react'
import {
  Area, Bar, BarChart, CartesianGrid, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { leerTablero } from '#/server/funciones'

type Fila = Record<string, number | string | null>

export const Route = createFileRoute('/')({
  validateSearch: (s: Record<string, unknown>) => ({
    nodo: typeof s.nodo === 'string' ? s.nodo : undefined,
    tema: s.tema === 'light' || s.tema === 'dark' ? (s.tema as 'light' | 'dark') : undefined,
  }),
  loaderDeps: ({ search }) => ({ nodo: search.nodo }),
  loader: ({ deps }) => leerTablero({ data: { nodo: deps.nodo } }),
  component: Tablero,
})

// ---------------------------------------------------------------- formato (es-CO, hora de Colombia)
const ZH = 'America/Bogota'
const n = (x: number, d = 0) => x.toLocaleString('es-CO', { minimumFractionDigits: d, maximumFractionDigits: d })
const hora = (t: number) => new Date(t * 1000).toLocaleTimeString('es-CO', { timeZone: ZH, hour: '2-digit', minute: '2-digit', hour12: false })
const fechaHora = (t: number) =>
  new Date(t * 1000).toLocaleString('es-CO', { timeZone: ZH, weekday: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false })
const CANAL = ['', 'CH1', 'CH2']

function Mini({ datos, color }: { datos: number[]; color: string }) {
  if (datos.length < 2) return <svg className="mini" />
  const lo = Math.min(...datos), hi = Math.max(...datos), r = hi - lo || 1
  const pts = datos.map((v, k) => `${(k / (datos.length - 1)) * 200},${32 - ((v - lo) / r) * 30}`).join(' ')
  return (
    <svg className="mini" viewBox="0 0 200 34" preserveAspectRatio="none">
      <polygon points={`0,34 ${pts} 200,34`} fill={color} opacity={0.12} />
      <polyline points={pts} fill="none" stroke={color} strokeWidth={1.6} vectorEffect="non-scaling-stroke" />
    </svg>
  )
}

function Tablero() {
  const inicial = Route.useLoaderData()
  const router = useRouter()
  const { tema: temaUrl } = Route.useSearch()
  const [d, setD] = useState(inicial)
  const [vivo, setVivo] = useState<Fila | null>(inicial.ultimo as Fila | null)
  const [reciente, setReciente] = useState<Fila[]>([])
  const [ahora, setAhora] = useState(() => Date.now() / 1000)
  const [tema, setTema] = useState<'light' | 'dark' | null>(null)

  useEffect(() => { setD(inicial); setVivo(inicial.ultimo as Fila | null) }, [inicial])

  // Tiempo real: SSE con cada registro; el resto se recarga cada minuto o al cambiar una alerta.
  useEffect(() => {
    const es = new EventSource('/api/eventos')
    es.addEventListener('registro', (ev) => {
      const { nodo, registro: r } = JSON.parse((ev as MessageEvent).data)
      if (nodo !== d.nodo) return
      const fila: Fila = { t: r.t, v: r.v_rms, i1: r.i_rms[0], i2: r.i_rms[1], p1: r.p[0], p2: r.p[1], q1: r.q[0], s1: r.s[0], s2: r.s[1], fp1: r.fp[0], fp2: r.fp[1], f: r.f, thd: r.thd, fw: (d.ultimo as Fila | null)?.fw ?? null }
      setVivo(fila)
      setReciente((x) => [...x.slice(-119), fila])
    })
    es.addEventListener('alerta', () => router.invalidate())
    const reloj = setInterval(() => setAhora(Date.now() / 1000), 1000)
    const recarga = setInterval(() => router.invalidate(), 60_000)
    return () => { es.close(); clearInterval(reloj); clearInterval(recarga) }
  }, [d.nodo, router])

  useEffect(() => {
    // ?tema= en la dirección tiene prioridad sobre la preferencia guardada.
    let t: string | null | undefined = temaUrl
    if (!t) { try { t = localStorage.getItem('tema') } catch { t = null } }
    if (t === 'light' || t === 'dark') setTema(t)
  }, [temaUrl])
  useEffect(() => {
    if (!tema) return
    document.documentElement.dataset.theme = tema
    try { localStorage.setItem('tema', tema) } catch {}
  }, [tema])
  const alternarTema = () => setTema((t) => (t === 'dark' || (!t && matchMedia('(prefers-color-scheme: dark)').matches) ? 'light' : 'dark'))

  const u = vivo
  const edad = u ? ahora - (u.t as number) : Infinity
  const enLinea = edad < 15 // el nodo publica a 1 Hz; sin registros en 15 s se considera desconectado
  const fw = (u?.fw as string | null) ?? '—'
  const simulado = fw.includes('sim')
  const umbral1 = (d.umbrales as { canal: number; valor: number; calculado: number }[]).find((x) => x.canal === 1)
  const e = d.energia
  const serie = d.serie as { t: number; p1: number; p2: number; v: number; fp1: number }[]

  const chart = useMemo(() => {
    const filas: Record<string, unknown>[] = serie.map((s) => ({ t: s.t, p1: s.p1, p2: s.p2 }))
    if (d.pronostico.disponible) {
      for (const h of (d.pronostico as { horas: { hora: number; kwh: number; min: number; max: number }[] }).horas.slice(0, 24)) {
        filas.push({ t: h.hora + 1800, f: h.kwh * 1000, banda: [h.min * 1000, h.max * 1000] })
      }
    }
    return filas
  }, [serie, d.pronostico])
  const tFin = (u?.t as number) ?? ahora
  // Marcas cada 3 h alineadas con la hora local de Colombia.
  const marcas = useMemo(() => {
    const out: number[] = []
    const desde = tFin - 86400, paso = 3 * 3600
    let m = Math.ceil((desde - 5 * 3600) / paso) * paso + 5 * 3600
    for (; m <= tFin + 86400; m += paso) out.push(m)
    return out
  }, [tFin])
  // Energía acumulada desde la medianoche local, a partir de los promedios de 5 min.
  const energiaHoy = useMemo(() => {
    const medianoche = Math.floor((tFin - 5 * 3600) / 86400) * 86400 + 5 * 3600
    let acc = 0
    return serie.filter((x) => x.t >= medianoche).map((x) => (acc += (x.p1 * 300) / 3.6e6))
  }, [serie, tFin])

  const p1 = (u?.p1 as number) ?? 0, p2 = (u?.p2 as number) ?? 0
  const resto = Math.max(0, p1 - p2)
  const spark = (k: string) => (reciente.length > 5 ? reciente.map((r) => r[k] as number) : serie.slice(-60).map((s) => (s as unknown as Fila)[k] as number))

  const cambiarEstado = async (id: number, estado: string) => {
    await fetch(`/api/alertas/${id}`, { method: 'PATCH', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ estado }) })
    router.invalidate()
  }

  const dias = (e?.mes.dias ?? []).map((x) => ({ dia: Number(x.dia.slice(8)), kwh1: x.kwh1, kwh2: x.kwh2 }))
  const costo = 897 // COP/kWh, tarifa de referencia estrato 3 en Barranquilla

  return (
    <div className="wrap">
      <header className="top">
        <div className="brand">
          <svg width="34" height="34" viewBox="0 0 34 34" aria-hidden="true"><rect width="34" height="34" rx="9" fill="var(--accent)" /><path d="M19 5 9 19h7l-2 10 11-15h-7z" fill="#fff" /></svg>
          <div>
            <h1>Medidor de energía · {d.nodo}</h1>
            <p>Monofásico 120 V / 60 Hz · CH1 total del tablero · CH2 subcircuito</p>
          </div>
        </div>
        <div className="pills">
          {d.nodos.length > 1 && (
            <select className="estado-sel" value={d.nodo} onChange={(ev) => router.navigate({ to: '/', search: (s) => ({ nodo: ev.target.value, tema: s.tema }) })}>
              {d.nodos.map((x) => <option key={x}>{x}</option>)}
            </select>
          )}
          <span className="pill"><span className={`dot ${enLinea ? 'pulse' : 'off'}`} key={String(u?.t)} />{enLinea ? 'En línea' : 'Sin datos recientes'}</span>
          <span className="pill num">{u ? `Último registro ${hora(u.t as number)}` : 'Sin registros'}</span>
          <span className="pill fw num">{fw} · ADR-001</span>
          <button className="icon" onClick={alternarTema} title="Cambiar tema claro u oscuro" aria-label="Cambiar tema">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="4.5" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></svg>
          </button>
        </div>
      </header>

      {simulado && (
        <div className="sim" role="note">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ color: 'var(--warn)', flex: 'none', marginTop: 1 }}><path d="M12 3 2 21h20z" /><path d="M12 10v5M12 18v.5" /></svg>
          <div><b>Datos del simulador.</b> Los registros vienen del simulador, que genera las mismas tramas ADR-001 de 40 B que enviará el ESP32. Cuando el nodo real transmita, el tablero mostrará su versión de <i>firmware</i> y este aviso desaparecerá.</div>
        </div>
      )}

      {!u ? (
        <div className="card vacio">Aún no hay registros. Inicie el nodo o ejecute <code>pnpm simular --dias 21</code>.</div>
      ) : (
        <main className="grid">
          <section className="card kpi orden-1" id="ahora">
            <h2>Potencia actual <small>CH1, total</small></h2>
            <div className="val num">{n(p1 / 1000, 2)}<span>kW</span></div>
            <div className="sub num">{n(u.i1 as number, 2)} A · {n(u.s1 as number)} VA</div>
            <Mini datos={spark('p1')} color="var(--ch1)" />
          </section>
          <section className="card kpi orden-1">
            <h2>Energía de hoy <small>desde las 00:00</small></h2>
            <div className="val num">{n(e?.hoy.kwh1 ?? 0, 2)}<span>kWh</span></div>
            <div className="sub num">
              {e?.ayer_misma_hora ? `${(e.hoy.kwh1 >= e.ayer_misma_hora ? '+' : '')}${n(((e.hoy.kwh1 - e.ayer_misma_hora) / e.ayer_misma_hora) * 100)} % frente a ayer a esta hora` : 'sin dato de ayer'}
            </div>
            <Mini datos={energiaHoy} color="var(--ok)" />
          </section>
          <section className="card kpi secundario orden-5">
            <h2>Factor de potencia <small>CH1</small></h2>
            <div className="val num">{n(u.fp1 as number, 3)}</div>
            <div className="sub num">{(u.q1 as number) > 0 ? 'Inductivo' : 'Capacitivo'} · {n(u.q1 as number)} var</div>
            <Mini datos={spark('fp1')} color="var(--forecast)" />
          </section>
          <section className="card kpi secundario orden-5">
            <h2>Tensión de red <small>ZMPT101B</small></h2>
            <div className="val num">{n(u.v as number, 1)}<span>V</span></div>
            <div className="sub num">{n(((u.v as number) - 120) / 1.2, 1)} % de 120 V · {n(u.f as number, 2)} Hz</div>
            <Mini datos={spark('v')} color="var(--ch2)" />
          </section>

          <section className="card chart24 orden-2" id="dia">
            <h2>Potencia activa · últimas 24 h y pronóstico de 24 h <small>{d.pronostico.disponible ? 'LSTM' : 'sin pronóstico'}</small></h2>
            <div className="g24">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chart} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                  <CartesianGrid vertical={false} />
                  <XAxis dataKey="t" type="number" domain={[tFin - 86400, tFin + 86400]} tickFormatter={hora} ticks={marcas} />
                  <YAxis tickFormatter={(v) => (v >= 1000 ? `${n(v / 1000, 1)} kW` : `${v} W`)} width={56} />
                  <Tooltip content={<Punto />} />
                  <Area dataKey="banda" stroke="none" fill="var(--band)" isAnimationActive={false} connectNulls />
                  <Line dataKey="p1" stroke="var(--ch1)" dot={false} strokeWidth={1.6} isAnimationActive={false} />
                  <Line dataKey="p2" stroke="var(--ch2)" dot={false} strokeWidth={1.4} isAnimationActive={false} />
                  <Line dataKey="f" stroke="var(--forecast)" strokeDasharray="5 3" dot={false} strokeWidth={1.8} isAnimationActive={false} connectNulls />
                  {umbral1 && <ReferenceLine y={umbral1.valor} stroke="var(--threshold)" strokeDasharray="4 3" />}
                  <ReferenceLine x={tFin} stroke="var(--muted)" label={{ value: 'ahora', position: 'insideTopRight', fill: 'var(--muted)', fontSize: 11 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
            <div className="legend">
              <span><i style={{ background: 'var(--ch1)' }} />CH1 total (promedio de 5 min)</span>
              <span><i style={{ background: 'var(--ch2)' }} />CH2 subcircuito</span>
              <span><i className="fdash" />Pronóstico LSTM (potencia media por hora)</span>
              <span><i className="band" />Intervalo del 90 %</span>
              {umbral1 && <span><i className="dash" />Umbral de alerta CH1: {n(umbral1.valor)} W (P95, 21 días)</span>}
            </div>
            <p className="note">
              {d.pronostico.disponible
                ? <>Modelo: {(d.pronostico as { modelo: string }).modelo}. Temperatura de entrada: {(d.pronostico as { temperatura: string }).temperatura}, en el extremo alto de las temperaturas de entrenamiento (Sceaux, Francia: −10,5 a 31,7 °C); el intervalo usa el RMSE medido en la prueba con UCI.</>
                : <>Pronóstico no disponible: {(d.pronostico as { motivo: string }).motivo}.</>}
            </p>
          </section>

          <section className="card canales orden-3" id="circuitos">
            <h2>Desglose por canal <small>tiempo real</small></h2>
            {[
              { nom: 'CH1 · Total del tablero', w: p1, color: 'var(--ch1)', det: `${n(u.i1 as number, 2)} A de 60 A · FP ${n(u.fp1 as number, 2)}`, pct: 100 },
              { nom: 'CH2 · Subcircuito', w: p2, color: 'var(--ch2)', det: `${n(u.i2 as number, 2)} A de 30 A · FP ${n(u.fp2 as number, 2)} · ${n(p1 ? (p2 / p1) * 100 : 0)} % del total`, pct: p1 ? (p2 / p1) * 100 : 0 },
              { nom: 'Resto (CH1 − CH2)', w: resto, color: 'var(--resto)', det: `${n(p1 ? (resto / p1) * 100 : 0)} % del total · calculado por diferencia`, pct: p1 ? (resto / p1) * 100 : 0 },
            ].map((c) => (
              <div className="canal" key={c.nom}>
                <div className="nom"><i style={{ background: c.color }} />{c.nom}</div>
                <div className="w num">{n(c.w)} W</div>
                <div className="det num">{c.det}</div>
                <div className="bar"><div style={{ width: `${Math.min(100, c.pct)}%`, background: c.color }} /></div>
              </div>
            ))}
            <div className="calidad">
              <div><b className="num">{n(u.f as number, 2)} Hz</b><span>Frecuencia</span></div>
              <div><b className="num">{n(u.thd as number, 1)} %</b><span>THD de corriente</span></div>
              <div><b className="num">{n(u.q1 as number)} var</b><span>Reactiva CH1</span></div>
            </div>
          </section>

          <section className="card mes orden-4" id="mes">
            <h2>Energía del mes <small>CH1, por día</small></h2>
            <div className="mesgrid">
              <div>
                <div className="big num">{n(e?.mes.kwh ?? 0, 1)}<span>kWh medidos</span></div>
                {e?.proyeccion ? (
                  <div className="rng num">
                    Proyección del mes: <b>{n(e.proyeccion.kwh)} kWh</b> ({n(e.proyeccion.min)}–{n(e.proyeccion.max)}, 90 %)<br />
                    ≈ ${n(e.proyeccion.kwh * costo)} COP a ${costo}/kWh (estrato 3, referencia)
                  </div>
                ) : <div className="rng">La proyección necesita al menos un día completo.</div>}
              </div>
              <div style={{ height: 120 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={dias} margin={{ top: 4, right: 0, bottom: 0, left: 0 }}>
                    <XAxis dataKey="dia" tickLine={false} interval="preserveStartEnd" />
                    <Tooltip content={<Dia />} />
                    <Bar dataKey="kwh1" fill="var(--ch1)" radius={[2, 2, 0, 0]} isAnimationActive={false} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            <p className="note">
              Proyección: energía medida en el mes más el promedio de los últimos {e?.proyeccion?.dias_base ?? 0} días completos por los días que faltan;
              el intervalo usa la variación entre esos días.
            </p>
          </section>

          <section className="card alertas orden-4" id="alertas">
            <h2>Alertas de consumo <small>{(d.alertas as Fila[]).filter((a) => a.estado === 'notificada').length} sin revisar</small></h2>
            <p className="umbral">Regla: potencia sobre el umbral sostenida durante 5 min o más. Umbral: percentil 95 de los últimos 21 días, recalculado cada semana{umbral1 ? <> (CH1: <b>{n(umbral1.valor)} W</b>)</> : ' (se calcula con al menos un día de datos)'}.</p>
            {(d.alertas as Fila[]).length === 0 ? <div className="vacio">Sin alertas.</div> : (
              <table>
                <thead><tr><th>Inicio</th><th>Canal</th><th className="r">Pico</th><th className="r dur">Duración</th><th>Estado</th></tr></thead>
                <tbody>
                  {(d.alertas as Fila[]).map((a) => (
                    <tr key={a.id as number}>
                      <td className="num">{fechaHora(a.inicio as number)}</td>
                      <td>{CANAL[a.canal as number]}</td>
                      <td className="r num">{n(a.pico as number)} W</td>
                      <td className="r num dur">{a.fin ? `${n(((a.fin as number) - (a.inicio as number)) / 60)} min` : 'en curso'}</td>
                      <td>
                        <select className={`estado-sel chip ${a.estado}`} value={a.estado as string} onChange={(ev) => cambiarEstado(a.id as number, ev.target.value)} aria-label="Estado de la alerta">
                          <option value="notificada">Notificada</option>
                          <option value="revisada">Revisada</option>
                          <option value="descartada">Descartada</option>
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </main>
      )}
      <footer>Medidor de energía no invasivo · ESP32 + SCT-013-000 + ZMPT101B</footer>

      <nav className="tabs" aria-label="Secciones">
        {[['ahora', 'Ahora'], ['dia', 'Día'], ['mes', 'Mes'], ['circuitos', 'Circuitos'], ['alertas', 'Alertas']].map(([id, t]) => (
          <a href={`#${id}`} key={id}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="8" /></svg>{t}
          </a>
        ))}
      </nav>
    </div>
  )
}

function Punto({ active, payload, label }: { active?: boolean; payload?: { dataKey: string; value: number | number[] }[]; label?: number }) {
  if (!active || !payload?.length || label === undefined) return null
  const v = (k: string) => payload.find((p) => p.dataKey === k)?.value
  const b = v('banda') as number[] | undefined
  return (
    <div className="tt">
      <div><b>{hora(label)}</b></div>
      {v('p1') !== undefined && <div>CH1: {n(v('p1') as number)} W</div>}
      {v('p2') !== undefined && <div>CH2: {n(v('p2') as number)} W</div>}
      {v('f') !== undefined && <div>Pronóstico: {n(v('f') as number)} W {b && `(${n(b[0])}–${n(b[1])})`}</div>}
    </div>
  )
}

function Dia({ active, payload, label }: { active?: boolean; payload?: { value: number }[]; label?: number }) {
  if (!active || !payload?.length) return null
  return <div className="tt"><b>Día {label}</b>: {n(payload[0].value, 2)} kWh</div>
}
