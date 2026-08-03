import sqlite3
from pathlib import Path

import pytest

from src.storage.backup import BackupError, check_integrity, create_backup, rotate


def _make_db(path: Path, rows: int = 5) -> None:
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
    conn.executemany("INSERT INTO t (v) VALUES (?)", [(f"v{i}",) for i in range(rows)])
    conn.commit()
    conn.close()


class TestCreateBackup:
    def test_creates_snapshot_with_integrity(self, tmp_path: Path):
        src = tmp_path / "database.db"
        _make_db(src)

        dest = create_backup(src, tmp_path / "backups")

        assert dest.is_file()
        assert dest.name.startswith("database-") and dest.name.endswith(".db")
        assert check_integrity(dest) == "ok"

        conn = sqlite3.connect(str(dest))
        count = conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
        conn.close()
        assert count == 5

    def test_safe_with_wal_mode(self, tmp_path: Path):
        src = tmp_path / "database.db"
        conn = sqlite3.connect(str(src))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE t (v TEXT)")
        conn.commit()
        conn.close()

        dest = create_backup(src, tmp_path / "backups")

        assert dest.is_file()
        assert check_integrity(dest) == "ok"
        assert not list((tmp_path / "backups").glob("*.tmp"))

    def test_missing_source_raises_backup_error(self, tmp_path: Path):
        with pytest.raises(BackupError):
            create_backup(tmp_path / "missing.db", tmp_path / "backups")

    def test_no_tmp_left_on_failure(self, tmp_path: Path):
        with pytest.raises(BackupError):
            create_backup(tmp_path / "missing.db", tmp_path / "backups")
        assert not list((tmp_path / "backups").glob("*.tmp"))


class TestRotate:
    def test_keeps_newest_n(self, tmp_path: Path):
        bdir = tmp_path / "backups"
        bdir.mkdir()
        for i in range(1, 10):
            (bdir / f"database-2026-08-{i:02d}.db").write_bytes(b"x")

        rotate(bdir, 7)

        remaining = sorted(f.name for f in bdir.glob("database-*.db"))
        assert remaining == [f"database-2026-08-{i:02d}.db" for i in range(3, 10)]

    def test_no_delete_when_within_limit(self, tmp_path: Path):
        bdir = tmp_path / "backups"
        bdir.mkdir()
        for i in range(1, 4):
            (bdir / f"database-2026-08-{i:02d}.db").write_bytes(b"x")

        rotate(bdir, 7)

        assert len(list(bdir.glob("database-*.db"))) == 3


class TestCheckIntegrity:
    def test_returns_ok_for_valid_db(self, tmp_path: Path):
        db = tmp_path / "ok.db"
        _make_db(db)
        assert check_integrity(db) == "ok"
