"""Worker healthcheck: verify a fresh heartbeat exists for a service.

Usage: python docker/worker_healthcheck.py
Env:
  WATCHED_SERVICE       service name to check (e.g. telegram, followup)
  HEARTBEAT_INTERVAL    heartbeat interval seconds (default 30)
"""

import os
import sqlite3
import sys
from datetime import datetime, timezone

DB = os.environ.get("DB_PATH", "data/database.db")
service = os.environ.get("WATCHED_SERVICE", "")
interval = int(os.environ.get("HEARTBEAT_INTERVAL", "30"))
max_age = interval * 3

try:
    conn = sqlite3.connect(DB)
    row = conn.execute(
        "SELECT last_beat FROM service_heartbeats WHERE service = ?", (service,)
    ).fetchone()
    conn.close()
    if row is None or row[0] is None:
        sys.exit(1)
    last_beat = datetime.fromisoformat(row[0])
    if last_beat.tzinfo is None:
        last_beat = last_beat.replace(tzinfo=timezone.utc)
    if (datetime.now(timezone.utc) - last_beat).total_seconds() > max_age:
        sys.exit(1)
    sys.exit(0)
except Exception:  # noqa: BLE001
    sys.exit(1)
