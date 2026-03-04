begin;

drop view if exists public.alerts_inbox_latest cascade;
drop view if exists public.alerts_latest cascade;
drop view if exists public.portfolio_snapshot_latest cascade;
drop view if exists public.top_movers_latest cascade;

create view public.top_movers_latest as
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
    select distinct market_id
    from public.market_universe
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
where l.yes_mid_now is not null
  and p.yes_mid_prev is not null;

create view public.portfolio_snapshot_latest as
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
    select distinct market_id
    from public.market_universe
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
where lm.yes_mid_now is not null
  and pm.yes_mid_prev is not null;

create view public.alerts_latest as
select
    user_id,
    market_id,
    question,
    side,
    mid_now,
    mid_prev,
    delta_mid,
    pnl,
    last_bucket,
    prev_bucket
from public.portfolio_snapshot_latest
where abs(delta_mid) >= 0.03;

create view public.alerts_inbox_latest as
select
    alert_type,
    user_id,
    market_id,
    question,
    side,
    mid_now,
    mid_prev,
    delta_mid,
    pnl,
    last_bucket,
    prev_bucket,
    abs_delta
from (
    select
        'portfolio'::text as alert_type,
        a.user_id,
        a.market_id,
        a.question,
        a.side,
        a.mid_now,
        a.mid_prev,
        a.delta_mid,
        a.pnl,
        a.last_bucket,
        a.prev_bucket,
        abs(a.delta_mid) as abs_delta
    from public.alerts_latest a
    union all
    select
        'watchlist'::text as alert_type,
        a.user_id,
        a.market_id,
        a.question,
        a.side,
        a.mid_now,
        a.mid_prev,
        a.delta_mid,
        a.pnl,
        a.last_bucket,
        a.prev_bucket,
        abs(a.delta_mid) as abs_delta
    from public.alerts_latest a
) t
order by abs_delta desc;

commit;
