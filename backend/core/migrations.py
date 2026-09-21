"""Alembic migration utilities."""
from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config


def run_migrations() -> None:
    """Run all pending Alembic migrations (upgrade to head)."""
    alembic_cfg = Config(str(Path(__file__).parent.parent.parent / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


def downgrade_migration(revision: str = "-1") -> None:
    """Downgrade by one revision (or to a specific revision label)."""
    alembic_cfg = Config(str(Path(__file__).parent.parent.parent / "alembic.ini"))
    command.downgrade(alembic_cfg, revision)


def generate_migration(message: str) -> None:
    """Auto-generate a new migration from model changes."""
    alembic_cfg = Config(str(Path(__file__).parent.parent.parent / "alembic.ini"))
    command.revision(alembic_cfg, message=message, autogenerate=True)
