-- Phase 7.2 : historique des analyses (exécuté dans le SQL Editor Supabase le 2026-11-02).
-- Seul le rapport est stocké, jamais le contenu analysé. RLS : chacun ne voit que ses analyses.
create table if not exists public.analyses (id uuid primary key, user_id uuid not null default auth.uid() references auth.users(id) on delete cascade, content_type text not null check (content_type in ('text','image','video')), conclusion text not null check (conclusion in ('likely_ai','likely_human','inconclusive')), result jsonb not null, created_at timestamptz not null default now());
create index if not exists analyses_user_created on public.analyses (user_id, created_at desc);
alter table public.analyses enable row level security;
drop policy if exists "own select" on public.analyses;
drop policy if exists "own insert" on public.analyses;
drop policy if exists "own delete" on public.analyses;
create policy "own select" on public.analyses for select to authenticated using ((select auth.uid()) = user_id);
create policy "own insert" on public.analyses for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "own delete" on public.analyses for delete to authenticated using ((select auth.uid()) = user_id);
revoke all on public.analyses from anon;
grant select, insert, delete on public.analyses to authenticated;
