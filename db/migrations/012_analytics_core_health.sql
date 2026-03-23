create or replace view public.analytics_core_health_latest as
with latest_bucket as (
  select max(ts_bucket) as latest_bucket
  from public.market_snapshots
),
prev_bucket as (
  select max(ms.ts_bucket) as prev_bucket
  from public.market_snapshots ms, latest_bucket lb
  where ms.ts_bucket < lb.latest_bucket
),
latest_health as (
  select sh.ts_bucket, sh.rows, sh.yes_quoted, sh.yes_coverage_pct
  from public.snapshot_health sh
  join latest_bucket lb on lb.latest_bucket = sh.ts_bucket
),
universe as (
  select count(*)::bigint as universe_count
  from public.market_universe
),
latest_universe as (
  select count(distinct ms.market_id)::bigint as latest_universe_coverage
  from public.market_snapshots ms
  join latest_bucket lb on lb.latest_bucket = ms.ts_bucket
  join public.market_universe mu on mu.market_id = ms.market_id
),
prev_universe as (
  select count(distinct ms.market_id)::bigint as prev_universe_coverage
  from public.market_snapshots ms
  join prev_bucket pb on pb.prev_bucket = ms.ts_bucket
  join public.market_universe mu on mu.market_id = ms.market_id
),
latest_movers as (
  select
    count(*)::bigint as movers_latest_count,
    count(*) filter (where abs(delta_yes) > 0)::bigint as movers_latest_nonzero,
    max(abs(delta_yes))::numeric as movers_latest_max_abs_delta
  from public.top_movers_latest
),
hour_movers as (
  select
    count(*)::bigint as movers_1h_count,
    count(*) filter (where abs(delta_yes_1h) > 0)::bigint as movers_1h_nonzero,
    max(abs(delta_yes_1h))::numeric as movers_1h_max_abs_delta
  from public.top_movers_1h
),
day_movers as (
  select
    count(*)::bigint as movers_24h_count,
    count(*) filter (where abs(delta_yes_24h) > 0)::bigint as movers_24h_nonzero,
    max(abs(delta_yes_24h))::numeric as movers_24h_max_abs_delta
  from public.top_movers_24h
)
select
  now() as measured_at,
  lb.latest_bucket,
  pb.prev_bucket,
  extract(epoch from (now() - lb.latest_bucket))::bigint as latest_bucket_lag_seconds,
  lh.rows as latest_bucket_rows,
  lh.yes_quoted as latest_yes_quoted,
  lh.yes_coverage_pct as latest_yes_coverage_pct,
  u.universe_count,
  lu.latest_universe_coverage,
  pu.prev_universe_coverage,
  lm.movers_latest_count,
  lm.movers_latest_nonzero,
  lm.movers_latest_max_abs_delta,
  hm.movers_1h_count,
  hm.movers_1h_nonzero,
  hm.movers_1h_max_abs_delta,
  dm.movers_24h_count,
  dm.movers_24h_nonzero,
  dm.movers_24h_max_abs_delta
from latest_bucket lb
left join prev_bucket pb on true
left join latest_health lh on true
left join universe u on true
left join latest_universe lu on true
left join prev_universe pu on true
left join latest_movers lm on true
left join hour_movers hm on true
left join day_movers dm on true;

comment on view public.analytics_core_health_latest is
'Read-only health snapshot for the canonical Layer II analytical core: market_snapshots, market_universe, snapshot_health, and top_movers_* outputs.';
