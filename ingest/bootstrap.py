import os
import subprocess
import sys


def main() -> None:
    runtime = os.environ.get("INGEST_RUNTIME", "batch").strip().lower()

    if runtime == "batch":
        cmd = [sys.executable, "worker.py"]
    elif runtime == "live":
        cmd = [sys.executable, "live_worker.py"]
    else:
        raise SystemExit(f"Unsupported INGEST_RUNTIME={runtime!r}; expected 'batch' or 'live'")

    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
