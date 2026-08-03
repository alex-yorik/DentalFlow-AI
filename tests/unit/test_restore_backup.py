import importlib.util
import sqlite3
from pathlib import Path

from alembic.command import upgrade
from alembic.config import Config

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ALEMBIC_CFG = PROJECT_ROOT / "src" / "storage" / "alembic.ini"

_spec = importlib.util.spec_from_file_location(
    "restore_backup", PROJECT_ROOT / "docker" / "restore_backup.py"
)
restore_backup_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(restore_backup_mod)
restore_backup = restore_backup_mod.restore_backup


def _migrate(path: Path, revision: str) -> None:
    cfg = Config(str(_ALEMBIC_CFG))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    upgrade(cfg, revision)


def _tables(path: Path) -> set[str]:
    conn = sqlite3.connect(str(path))
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        return {r[0] for r in rows}
    finally:
        conn.close()


class TestRestoreAppliesMigrations:
    def test_old_backup_is_migrated_to_latest(self, tmp_path: Path):
        src = tmp_path / "old_backup.db"
        _migrate(src, "002")
        assert "service_heartbeats" not in _tables(src)
        assert "leads" in _tables(src)

        dest = tmp_path / "database.db"
        rc = restore_backup(src, dest)

        assert rc == 0
        tables = _tables(dest)
        assert "leads" in tables
        assert "service_heartbeats" in tables
        assert "alembic_version" in tables

    def test_empty_backup_gets_full_schema(self, tmp_path: Path):
        src = tmp_path / "empty.db"
        conn = sqlite3.connect(str(src))
        conn.close()

        dest = tmp_path / "database.db"
        assert restore_backup(src, dest) == 0

        tables = _tables(dest)
        assert {"leads", "followup_tasks", "service_heartbeats"} <= tables

    def test_upgrade_failure_returns_nonzero(self, tmp_path: Path, monkeypatch):
        src = tmp_path / "old_backup.db"
        _migrate(src, "002")

        def boom(db_path):
            raise RuntimeError("migration exploded")

        monkeypatch.setattr(restore_backup_mod, "run_alembic_upgrade", boom)

        dest = tmp_path / "database.db"
        assert restore_backup(src, dest) == 1

    def test_missing_backup_returns_nonzero(self, tmp_path: Path):
        dest = tmp_path / "database.db"
        assert restore_backup(tmp_path / "nope.db", dest) == 1
