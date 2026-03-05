import os
import sys
import time
from datetime import datetime, timezone

from main import main as run_ingest_once


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sleep_seconds(interval: int, started_at: float) -> float:
    elapsed = time.time() - started_at
    return max(0.0, float(interval) - elapsed)


def run_loop() -> None:
    interval = int(os.environ.get("INGEST_INTERVAL_SECONDS", "900"))
    fail_sleep = int(os.environ.get("INGEST_FAIL_SLEEP_SECONDS", "30"))

    print(f"INFO: ingest worker started interval={interval}s fail_sleep={fail_sleep}s")
    while True:
        started_at = time.time()
        try:
            print(f"INFO: ingest tick started at {_utc_now()}")
            run_ingest_once()
            print(f"INFO: ingest tick finished at {_utc_now()}")
        except Exception as exc:
            print(f"ERROR: ingest tick failed at {_utc_now()}: {type(exc).__name__}: {exc}")
            time.sleep(fail_sleep)
            continue

        time.sleep(_sleep_seconds(interval, started_at))


if __name__ == "__main__":
    try:
        run_loop()
    except KeyboardInterrupt:
        print("INFO: ingest worker stopped by signal")
        sys.exit(0)
