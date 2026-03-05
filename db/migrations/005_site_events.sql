create table if not exists app.site_events (
    id bigserial primary key,
    event_type text not null,
    email text,
    source text,
    lang text,
    path text,
    user_agent text,
    ip inet,
    details jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_site_events_created_at on app.site_events (created_at desc);
create index if not exists idx_site_events_type_created on app.site_events (event_type, created_at desc);
create index if not exists idx_site_events_email_created on app.site_events (email, created_at desc);
