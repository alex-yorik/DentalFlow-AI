"""Restore a SQLite backup into data/database.db.

Usage:
    python docker/restore_backup.py [path/to/backup.db]

If no path is given, the most recent backup in data/backups is used.
The live DB file is replaced via sqlite3 backup API (never a raw copy),
after verifying integrity of the source backup, then alembic migrations
are run so the restored (possibly old) schema is brought to `head`.

IMPORTANT: stop the application services first so the DB is not being
written during restore (see docs/backup_runbook.md).
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.storage.backup import check_integrity
from src.storage.database import DB_PATH, run_alembic_upgrade

BACKUPS_DIR = Path("data/backups")


def find_latest(backups_dir: Path) -> Path | None:
    files = sorted(backups_dir.glob("database-*.db"))
    return files[-1] if files else None


def restore_backup(src: Path, db_path: Path = DB_PATH) -> int:
    """Replace db_path from a backup and migrate its schema to the latest revision."""
    if src is None or not src.is_file():
        print(f"No backup found to restore: {src}", file=sys.stderr)
        return 1

    if check_integrity(src) != "ok":
        print(f"Backup integrity check FAILED, aborting: {src}", file=sys.stderr)
        return 1

    tmp = db_path.parent / "database.db.restore"
    conn_src = sqlite3.connect(str(src))
    conn_dst = sqlite3.connect(str(tmp))
    try:
        with conn_dst:
            conn_src.backup(conn_dst)
    finally:
        conn_src.close()
        conn_dst.close()

    tmp.replace(db_path)
    print(f"Restored {db_path} from {src}")

    try:
        run_alembic_upgrade(db_path)
    except Exception as e:  # noqa: BLE001
        print(
            f"Alembic upgrade FAILED after restore: {e}\n"
            "Run migrations manually: python -m alembic upgrade head",
            file=sys.stderr,
        )
        return 1
    print("Database schema migrated to latest revision")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) > 2:
        print("Usage: python docker/restore_backup.py [path/to/backup.db]", file=sys.stderr)
        return 2

    src = Path(argv[1]) if len(argv) == 2 else find_latest(BACKUPS_DIR)
    return restore_backup(src, DB_PATH)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
