import os
from pathlib import Path
import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / 'bot' / '.env')

pg_conn = os.environ.get('PG_CONN')
if not pg_conn:
    raise RuntimeError('PG_CONN missing')

sql = (ROOT / 'scripts' / 'ops' / 'db_smoke.sql').read_text()
with psycopg.connect(pg_conn, connect_timeout=10) as conn:
    with conn.cursor() as cur:
        cur.execute(sql)
        for metric, value in cur.fetchall():
            print(f'{metric}: {value}')
