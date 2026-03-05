select 'users_total' as metric, count(*)::text as value from app.users
union all
select 'profiles_total', count(*)::text from bot.profiles
union all
select 'free_profiles', count(*)::text from bot.profiles where bot.current_plan(user_id)='free'
union all
select 'pro_profiles', count(*)::text from bot.profiles where bot.current_plan(user_id)='pro'
union all
select 'watchlist_total', count(*)::text from bot.watchlist
union all
select 'inbox_total', count(*)::text from bot.alerts_inbox_latest
union all
select 'sent_bot_today', count(*)::text from bot.sent_alerts_log where channel='bot' and sent_at >= date_trunc('day', now())
union all
select 'emails_confirmed', count(*)::text from app.email_subscribers where confirmed_at is not null and unsubscribed_at is null;
