#!/bin/sh
# Self-healing first boot: restore the committed seed if the schema is missing.
set -e
rc=0
python - <<'PY' || rc=$?
import sys
import time

import psycopg

from backend.app import config

ok = None
for _ in range(30):
    try:
        with psycopg.connect(config.settings.database_url) as conn:
            ok = conn.execute("SELECT to_regclass('public.parts')").fetchone()[0]
        break
    except Exception:  # noqa: BLE001
        time.sleep(1)
else:
    sys.exit(1)
sys.exit(0 if ok else 3)
PY
if [ "$rc" = "3" ]; then
  echo "schema missing - restoring committed seed"
  python backend/ingest.py --load-seed
elif [ "$rc" != "0" ]; then
  echo "database never became reachable" >&2
  exit "$rc"
fi
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
