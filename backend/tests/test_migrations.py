"""Runs the real Alembic migration on a throwaway database and checks it matches the ORM models."""
import os

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.core.config import get_settings
from app.core.database import Base, make_engine


def test_migration_matches_models(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'mig.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    try:
        backend_dir = os.path.dirname(os.path.dirname(__file__))
        cfg = Config(os.path.join(backend_dir, "alembic.ini"))
        cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
        command.upgrade(cfg, "head")
        insp = inspect(make_engine(url))
        for table in Base.metadata.sorted_tables:
            assert insp.has_table(table.name), table.name
            assert {c["name"] for c in insp.get_columns(table.name)} == {c.name for c in table.columns}, table.name
        command.downgrade(cfg, "base")
        assert not inspect(make_engine(url)).has_table("users")
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()
