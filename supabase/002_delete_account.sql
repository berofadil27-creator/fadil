-- Phase 7.3 : suppression de son propre compte (exécuté le 2026-11-02). Supprime aussi l'historique (on delete cascade).
create or replace function public.delete_my_account() returns void language plpgsql security definer set search_path = '' as $fn$ begin if auth.uid() is null then raise exception 'not authenticated'; end if; delete from auth.users where id = auth.uid(); end; $fn$;
revoke execute on function public.delete_my_account() from public, anon;
grant execute on function public.delete_my_account() to authenticated;
