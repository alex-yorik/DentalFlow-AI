"""Safe SQLite backup: snapshot, integrity check, and retention rotation.

Uses sqlite3.Connection.backup(), which produces a consistent copy even while
the source database is being written (safe with WAL mode). Never copies the
live *.db file directly.
"""

import logging
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class BackupError(Exception):
    pass


def check_integrity(db_path: Path) -> str:
    """Run PRAGMA integrity_check and return the first result row()."""
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute("PRAGMA integrity_check;").fetchone()
        return str(row[0]) if row else "?"
    finally:
        conn.close()


def _stamp() -> str:
    return datetime.now(UTC).date().isoformat()


def create_backup(db_path: Path, backups_dir: Path) -> Path:
    """Snapshot db_path into backups_dir/database-<date>.db and verify integrity.

    Writes to a temp file first so a crash never leaves a truncated backup,
    then moves it into place (overwriting any same-day backup).
    """
    backups_dir.mkdir(parents=True, exist_ok=True)
    if not db_path.is_file():
        raise BackupError(f"source database not found: {db_path}")
    dest = backups_dir / f"database-{_stamp()}.db"
    tmp = backups_dir / f"database-{_stamp()}.db.tmp"
    try:
        src = sqlite3.connect(str(db_path))
        dst = sqlite3.connect(str(tmp))
        try:
            with dst:
                src.backup(dst)
        finally:
            src.close()
            dst.close()
        if check_integrity(tmp) != "ok":
            raise BackupError(f"integrity check failed: {tmp}")
        shutil.move(str(tmp), str(dest))
        logger.info("Backup created: %s", dest)
        return dest
    except sqlite3.Error as e:
        tmp.unlink(missing_ok=True)
        raise BackupError(f"backup failed: {e}") from e
    except BackupError:
        tmp.unlink(missing_ok=True)
        raise


def rotate(backups_dir: Path, retention_days: int) -> None:
    """Delete backups older than the last `retention_days` date-stamped files."""
    files = sorted(backups_dir.glob("database-*.db"))
    for stale in files[:-retention_days]:
        stale.unlink(missing_ok=True)
        logger.info("Rotated out: %s", stale)
