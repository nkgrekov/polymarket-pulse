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
        left join ranked_auto ra using (market_id)
        where dr.market_id is not null
          and dr.market_id <> ''
        order by dr.market_id, dr.priority
    )
    select
        market_id,
        source,
        weight
    from desired;

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

comment on function public.refresh_market_universe(integer, text[], text[]) is
'Rebuilds market_universe from three sources: manual watchlist, user positions, and auto live/liquid markets with both latest and previous buckets.';

commit;
