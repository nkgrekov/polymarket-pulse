do $$
declare
    market_id_type text;
begin
    select c.data_type
    into market_id_type
    from information_schema.columns c
    where c.table_schema = 'public'
      and c.table_name = 'sent_alerts_log'
      and c.column_name = 'market_id';

    if market_id_type is not null and market_id_type <> 'text' then
        if not exists (
            select 1
            from information_schema.tables
            where table_schema = 'public'
              and table_name = 'sent_alerts_log_legacy'
        ) then
            execute 'alter table public.sent_alerts_log rename to sent_alerts_log_legacy';
        else
            execute 'drop table if exists public.sent_alerts_log';
        end if;
    end if;
end
$$;

create table if not exists public.sent_alerts_log (
    user_id text,
    market_id text,
    alert_type text,
    last_bucket timestamptz default now(),
    sent_at timestamptz default now(),
    primary key (user_id, market_id, alert_type, last_bucket)
);
