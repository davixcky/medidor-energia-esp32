-- Esquema de la plataforma del medidor en Supabase (Postgres).
-- Se aplica con `supabase db push` o con `pnpm db:migrar` (usa DATABASE_URL). Es idempotente.

-- Registros ADR-001 tal como llegan (1 Hz por nodo). t: época Unix en segundos (UTC).
create table if not exists registros (
  nodo text not null, t bigint not null, fw text,
  v double precision, i1 double precision, i2 double precision, i3 double precision,
  p1 double precision, p2 double precision, p3 double precision,
  q1 double precision, q2 double precision, q3 double precision,
  s1 double precision, s2 double precision, s3 double precision,
  fp1 double precision, fp2 double precision, fp3 double precision,
  f double precision, thd double precision,
  primary key (nodo, t)
);

-- Energía integrada por hora (inicio de la hora en época Unix UTC), en kWh por canal.
create table if not exists horas (
  nodo text not null, hora bigint not null,
  kwh1 double precision not null default 0, kwh2 double precision not null default 0,
  kwh3 double precision not null default 0, segundos double precision not null default 0,
  primary key (nodo, hora)
);

-- Umbral de alerta por canal: percentil 95 de los últimos 21 días, recalculado cada semana.
create table if not exists umbrales (
  nodo text not null, canal integer not null, valor double precision not null, calculado bigint not null,
  primary key (nodo, canal)
);

create table if not exists alertas (
  id bigint generated always as identity primary key,
  nodo text not null, canal integer not null, inicio bigint not null, fin bigint,
  pico double precision not null, umbral double precision not null,
  estado text not null default 'notificada' check (estado in ('notificada', 'revisada', 'descartada'))
);
create index if not exists alertas_nodo on alertas (nodo, inicio desc);

-- Solo el servidor de la plataforma escribe y lee, con la conexión directa (rol postgres).
-- RLS activo y sin políticas: la API pública de Supabase (clave anon) no puede leer ni escribir.
alter table registros enable row level security;
alter table horas enable row level security;
alter table umbrales enable row level security;
alter table alertas enable row level security;
