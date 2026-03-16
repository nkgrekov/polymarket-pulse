import argparse
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row


def resolve_pg_conn() -> str:
    pg = os.environ.get("PG_CONN")
    if pg:
        return pg
    for env_path in ("bot/.env", "trader_bot/.env"):
        path = Path(env_path)
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("PG_CONN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("PG_CONN not found in env, bot/.env, or trader_bot/.env")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manually activate a signed trader signer session.")
    parser.add_argument("session_token", help="Session token from /signer or /trader-connect")
    parser.add_argument("--signer-ref", default=None, help="Optional signer reference to store on wallet_links")
    parser.add_argument("--note", default=None, help="Optional operator note")
    args = parser.parse_args()

    pg_conn = resolve_pg_conn()
    with psycopg.connect(pg_conn, connect_timeout=10, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '10000ms'")
            cur.execute(
                """
                select *
                from trade.activate_signer_session(%s, %s, %s)
                """,
                (args.session_token, args.signer_ref, args.note),
            )
            row = cur.fetchone()
        conn.commit()

    if not row:
        raise RuntimeError("Activation returned no row")

    print("signer session activated")
    print(f"session_id={row['session_id']}")
    print(f"wallet_link_id={row['wallet_link_id']}")
    print(f"wallet_address={row['wallet_address']}")
    print(f"session_status={row['session_status']}")
    print(f"wallet_status={row['wallet_status']}")
    print(f"verified_at={row['verified_at']}")


if __name__ == "__main__":
    main()
