begin;

create or replace function public.refresh_market_universe(
    p_limit integer default 200,
    p_manual_ids text[] default array[]::text[],
    p_position_ids text[] default array[]::text[]
)
returns integer
language plpgsql
as $$
declare
    v_limit integer := greatest(coalesce(p_limit, 200), 1);
    v_count integer := 0;
begin
    create temporary table if not exists market_universe_desired (
        market_id text primary key,
        source text not null,
        weight numeric
    ) on commit drop;

    truncate market_universe_desired;

    insert into market_universe_desired (market_id, source, weight)
    with latest_bucket as (
        select max(ts_bucket) as ts_bucket
        from public.market_snapshots
    ),
    prev_bucket as (
        select max(ms.ts_bucket) as ts_bucket
        from public.market_snapshots ms
        join latest_bucket lb on true
        where ms.ts_bucket < lb.ts_bucket
    ),
    last_rows as (
        select
            ms.market_id,
            max(ms.liquidity) as weight
        from public.market_snapshots ms
        join latest_bucket lb on lb.ts_bucket = ms.ts_bucket
        where ms.yes_bid is not null
          and ms.yes_ask is not null
        group by ms.market_id
    ),
    prev_rows as (
        select distinct ms.market_id
        from public.market_snapshots ms
        join prev_bucket pb on pb.ts_bucket = ms.ts_bucket
        where ms.yes_bid is not null
          and ms.yes_ask is not null
    ),
    ranked_auto as (
        select
            l.market_id,
            l.weight
        from last_rows l
        join prev_rows p using (market_id)
        join public.markets m on m.market_id = l.market_id
        where coalesce(m.status, 'active') = 'active'
        order by l.weight desc nulls last, l.market_id
        limit v_limit
    ),
    desired_raw as (
        select unnest(coalesce(p_manual_ids, array[]::text[])) as market_id, 'manual'::text as source, 1 as priority
        union all
        select unnest(coalesce(p_position_ids, array[]::text[])) as market_id, 'position'::text as source, 2 as priority
        union all
        select market_id, 'auto'::text as source, 3 as priority
        from ranked_auto
    ),
    desired as (
        select distinct on (dr.market_id)
            dr.market_id,
            dr.source,
            ra.weight
        from desired_raw dr
        join public.markets m on m.market_id = dr.market_id
        left join ranked_auto ra on ra.market_id = dr.market_id
        where dr.market_id is not null
          and dr.market_id <> ''
          and coalesce(m.status, 'active') = 'active'
        order by dr.market_id, dr.priority
    )
    select
        d.market_id,
        d.source,
        d.weight
    from desired d;

    insert into public.market_universe as mu (market_id, source, weight, updated_at)
    select
        d.market_id,
        d.source,
        d.weight,
        now() as updated_at
    from market_universe_desired d
    on conflict (market_id) do update
    set source = excluded.source,
        weight = excluded.weight,
        updated_at = excluded.updated_at;

    delete from public.market_universe mu
    where not exists (
        select 1
        from market_universe_desired d
        where d.market_id = mu.market_id
    );

    select count(*)
    into v_count
    from public.market_universe;

    return v_count;
end;
$$;

create or replace view public.top_movers_latest as
with lb as (
    select last_bucket
    from public.global_bucket_latest
),
prev as (
    select max(ms.ts_bucket) as prev_bucket
    from public.market_snapshots ms
    join lb on true
    where ms.ts_bucket < lb.last_bucket
),
universe as (
    select distinct u.market_id
    from public.market_universe u
    join public.markets m on m.market_id = u.market_id
    where coalesce(m.status, 'active') = 'active'
),
last_rows as (
    select
        ms.market_id,
        max(((ms.yes_bid + ms.yes_ask) / 2::numeric)) as yes_mid_now
    from public.market_snapshots ms
    join lb on ms.ts_bucket = lb.last_bucket
    join universe u on u.market_id = ms.market_id
    group by ms.market_id
),
prev_rows as (
    select
        ms.market_id,
        max(((ms.yes_bid + ms.yes_ask) / 2::numeric)) as yes_mid_prev
    from public.market_snapshots ms
    join prev on ms.ts_bucket = prev.prev_bucket
    join universe u on u.market_id = ms.market_id
    group by ms.market_id
)
select
    l.market_id,
    m.question,
    (select last_bucket from lb) as last_bucket,
    (select prev_bucket from prev) as prev_bucket,
    l.yes_mid_now,
    p.yes_mid_prev,
    (l.yes_mid_now - p.yes_mid_prev) as delta_yes
from last_rows l
join prev_rows p using (market_id)
join public.markets m on m.market_id = l.market_id
where coalesce(m.status, 'active') = 'active'
  and l.yes_mid_now is not null
  and p.yes_mid_prev is not null;

create or replace view public.portfolio_snapshot_latest as
with lb as (
    select last_bucket
    from public.global_bucket_latest
),
prev as (
    select max(ms.ts_bucket) as prev_bucket
    from public.market_snapshots ms
    join lb on true
    where ms.ts_bucket < lb.last_bucket
),
universe as (
    select distinct u.market_id
    from public.market_universe u
    join public.markets m on m.market_id = u.market_id
    where coalesce(m.status, 'active') = 'active'
),
pos as (
    select
        p.user_id,
        p.market_id,
        p.side,
        p.size,
        p.avg_price
    from public.user_positions p
    join universe u on u.market_id = p.market_id
),
last_mid as (
    select
        ms.market_id,
        max(((ms.yes_bid + ms.yes_ask) / 2::numeric)) as yes_mid_now
    from public.market_snapshots ms
    join lb on ms.ts_bucket = lb.last_bucket
    join universe u on u.market_id = ms.market_id
    group by ms.market_id
),
prev_mid as (
    select
        ms.market_id,
        max(((ms.yes_bid + ms.yes_ask) / 2::numeric)) as yes_mid_prev
    from public.market_snapshots ms
    join prev on ms.ts_bucket = prev.prev_bucket
    join universe u on u.market_id = ms.market_id
    group by ms.market_id
)
select
    p.user_id,
    p.market_id,
    m.question,
    p.side,
    p.size,
    p.avg_price,
    (select last_bucket from lb) as last_bucket,
    (select prev_bucket from prev) as prev_bucket,
    lm.yes_mid_now as mid_now,
    pm.yes_mid_prev as mid_prev,
    0::numeric as pnl,
    (lm.yes_mid_now - pm.yes_mid_prev) as delta_mid
from pos p
join public.markets m on m.market_id = p.market_id
join last_mid lm on lm.market_id = p.market_id
join prev_mid pm on pm.market_id = p.market_id
where coalesce(m.status, 'active') = 'active'
  and lm.yes_mid_now is not null
  and pm.yes_mid_prev is not null;

create or replace view public.watchlist_snapshot_latest as
with lb as (
    select last_bucket
    from public.global_bucket_latest
),
prev as (
    select max(ms.ts_bucket) as prev_bucket
    from public.market_snapshots ms
    join lb on true
    where ms.ts_bucket < lb.last_bucket
),
universe as (
    select distinct u.market_id
    from public.market_universe u
    join public.markets m on m.market_id = u.market_id
    where coalesce(m.status, 'active') = 'active'
),
wl as (
    select
        w.user_id,
        w.market_id
    from public.user_watchlist w
    join universe u on u.market_id = w.market_id
),
last_mid as (
    select
        ms.market_id,
        max(((ms.yes_bid + ms.yes_ask) / 2::numeric)) as yes_mid_now
    from public.market_snapshots ms
    join lb on ms.ts_bucket = lb.last_bucket
    join universe u on u.market_id = ms.market_id
    group by ms.market_id
),
prev_mid as (
    select
        ms.market_id,
        max(((ms.yes_bid + ms.yes_ask) / 2::numeric)) as yes_mid_prev
    from public.market_snapshots ms
    join prev on ms.ts_bucket = prev.prev_bucket
    join universe u on u.market_id = ms.market_id
    group by ms.market_id
)
select
    w.user_id,
    w.market_id,
    m.question,
    (select last_bucket from lb) as last_bucket,
    (select prev_bucket from prev) as prev_bucket,
    lm.yes_mid_now as mid_now,
    pm.yes_mid_prev as mid_prev,
    (lm.yes_mid_now - pm.yes_mid_prev) as delta_mid
from wl w
join public.markets m on m.market_id = w.market_id
join last_mid lm on lm.market_id = w.market_id
join prev_mid pm on pm.market_id = w.market_id
where coalesce(m.status, 'active') = 'active'
  and lm.yes_mid_now is not null
  and pm.yes_mid_prev is not null;

create or replace view bot.watchlist_snapshot_latest as
with lb as (
  select last_bucket
  from public.global_bucket_latest
),
prev as (
  select max(ms.ts_bucket) as prev_bucket
  from public.market_snapshots ms
  join lb on true
  where ms.ts_bucket < lb.last_bucket
),
universe as (
  select distinct u.market_id
  from public.market_universe u
  join public.markets m on m.market_id = u.market_id
  where coalesce(m.status, 'active') = 'active'
),
last_mid as (
  select
    ms.market_id,
    max(((ms.yes_bid + ms.yes_ask) / 2::numeric)) as yes_mid_now
  from public.market_snapshots ms
  join lb on ms.ts_bucket = lb.last_bucket
  join universe u on u.market_id = ms.market_id
  group by ms.market_id
),
prev_mid as (
  select
    ms.market_id,
    max(((ms.yes_bid + ms.yes_ask) / 2::numeric)) as yes_mid_prev
  from public.market_snapshots ms
  join prev on ms.ts_bucket = prev.prev_bucket
  join universe u on u.market_id = ms.market_id
  group by ms.market_id
)
select
  w.user_id,
  w.market_id,
  m.question,
  (select last_bucket from lb) as last_bucket,
  (select prev_bucket from prev) as prev_bucket,
  lm.yes_mid_now as mid_now,
  pm.yes_mid_prev as mid_prev,
  (lm.yes_mid_now - pm.yes_mid_prev) as delta_mid
from bot.watchlist w
join public.markets m on m.market_id = w.market_id
join last_mid lm on lm.market_id = w.market_id
join prev_mid pm on pm.market_id = w.market_id
where coalesce(m.status, 'active') = 'active'
  and lm.yes_mid_now is not null
  and pm.yes_mid_prev is not null;

commit;
