-- Run once in the Supabase SQL Editor for a new project.
begin;

create table public.study_sessions (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    subject text not null check (length(trim(subject)) > 0),
    minutes integer not null check (minutes > 0),
    study_date date not null,
    notes text,
    created_at timestamptz not null default now()
);

create index study_sessions_user_id_idx on public.study_sessions(user_id);
alter table public.study_sessions enable row level security;

-- Anonymous SELECT is allowed at the table level for the connection probe.
-- With no anonymous RLS policy, it cannot return any rows.
revoke all on public.study_sessions from anon, authenticated;
grant select on public.study_sessions to anon;
grant select, insert, update, delete on public.study_sessions to authenticated;

create policy "Read own sessions" on public.study_sessions
    for select to authenticated using ((select auth.uid()) = user_id);
create policy "Create own sessions" on public.study_sessions
    for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "Update own sessions" on public.study_sessions
    for update to authenticated using ((select auth.uid()) = user_id)
    with check ((select auth.uid()) = user_id);
create policy "Delete own sessions" on public.study_sessions
    for delete to authenticated using ((select auth.uid()) = user_id);

commit;
