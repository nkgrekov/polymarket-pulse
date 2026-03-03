begin;

create or replace function public.refresh_market_universe(p_limit integer default 200)
returns integer
language plpgsql
as $$
declare
    v_limit integer := greatest(coalesce(p_limit, 200), 1);
    v_count integer := 0;
begin
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
    ranked as (
        select
            ms.market_id,
            max(ms.liquidity) as weight
        from public.market_snapshots ms
        join latest_bucket lb on lb.ts_bucket = ms.ts_bucket
        join public.markets m on m.market_id = ms.market_id
        join prev_bucket pb on pb.ts_bucket is not null
        where ms.yes_bid is not null
          and ms.yes_ask is not null
          and coalesce(m.status, 'active') = 'active'
          and exists (
              select 1
              from public.market_snapshots ms_prev
              where ms_prev.market_id = ms.market_id
                and ms_prev.ts_bucket = pb.ts_bucket
                and ms_prev.yes_bid is not null
                and ms_prev.yes_ask is not null
          )
        group by ms.market_id
        order by max(ms.liquidity) desc nulls last, ms.market_id
        limit v_limit
    )
    insert into public.market_universe as mu (market_id, source, weight, updated_at)
    select
        r.market_id,
        'auto'::text as source,
        r.weight,
        now() as updated_at
    from ranked r
    on conflict (market_id) do update
    set source = excluded.source,
        weight = excluded.weight,
        updated_at = excluded.updated_at;

    delete from public.market_universe mu
    where mu.source = 'auto'
      and not exists (
          select 1
          from (
              with latest_bucket as (
                  select max(ts_bucket) as ts_bucket
                  from public.market_snapshots
              ),
              prev_bucket as (
                  select max(ms_prev.ts_bucket) as ts_bucket
                  from public.market_snapshots ms_prev
                  join latest_bucket lb on true
                  where ms_prev.ts_bucket < lb.ts_bucket
              )
              select ms.market_id
              from public.market_snapshots ms
              join latest_bucket lb on lb.ts_bucket = ms.ts_bucket
              join public.markets m on m.market_id = ms.market_id
              join prev_bucket pb on pb.ts_bucket is not null
              where ms.yes_bid is not null
                and ms.yes_ask is not null
                and coalesce(m.status, 'active') = 'active'
                and exists (
                    select 1
                    from public.market_snapshots ms_prev
                    where ms_prev.market_id = ms.market_id
                      and ms_prev.ts_bucket = pb.ts_bucket
                      and ms_prev.yes_bid is not null
                      and ms_prev.yes_ask is not null
                )
              group by ms.market_id
              order by max(ms.liquidity) desc nulls last, ms.market_id
              limit v_limit
          ) ranked_now
          where ranked_now.market_id = mu.market_id
      );

    select count(*)
    into v_count
    from public.market_universe
    where source = 'auto';

    return v_count;
end;
$$;

commit;
