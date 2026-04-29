-- ─────────────────────────────────────────────────────────
-- NODO One · Admin tracking setup
-- Ejecutar UNA sola vez en el Editor SQL de Supabase
-- ─────────────────────────────────────────────────────────

-- 1. Tabla de visitas (quién abrió cada propuesta)
create table if not exists visits (
  id         uuid        default gen_random_uuid() primary key,
  page       text        not null,
  device     text,
  referrer   text,
  created_at timestamptz default now()
);

-- 2. Tabla de interacciones con el demo de chat
create table if not exists demo_events (
  id         uuid        default gen_random_uuid() primary key,
  page       text        not null default 'propuesta_general',
  sector     text,
  created_at timestamptz default now()
);

-- 3. RLS: permitir insertar desde el frontend (anon)
alter table visits      enable row level security;
alter table demo_events enable row level security;

create policy "anon_insert_visits"
  on visits for insert to anon with check (true);

create policy "anon_select_visits"
  on visits for select to anon using (true);

create policy "anon_insert_demo"
  on demo_events for insert to anon with check (true);

create policy "anon_select_demo"
  on demo_events for select to anon using (true);

-- 4. Índices para filtrar por fecha rápido
create index if not exists visits_created_idx      on visits      (created_at desc);
create index if not exists demo_events_created_idx on demo_events (created_at desc);
