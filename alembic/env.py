"""Alembic environment configuration for CallGuard AI.

This file is executed by Alembic for both --autogenerate and migration runs.
It imports the SQLAlchemy Base and all ORM models so Alembic can detect
schema changes automatically.
"""
from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# ---------------------------------------------------------------------------
# Ensure the project root is on the import path so ``backend`` is importable.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Import Base + all models (side-effects populate Base.metadata)
# ---------------------------------------------------------------------------
from backend.models.database import Base  # noqa: E402
import backend.models.tables  # noqa: E402, F401  -- registers all ORM models

from backend.core.config import settings  # noqa: E402

# ---------------------------------------------------------------------------
# Alembic config object
# ---------------------------------------------------------------------------
config = context.config

# Override the sqlalchemy.url from our settings object so we never need to
# hard-code credentials in alembic.ini.
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging if present.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata object used for autogenerate support.
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline migration (no live DB connection required)
# ---------------------------------------------------------------------------

def run_migrations_offline() -> None:
    """Run migrations in offline mode.

    Generates SQL scripts without connecting to the database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migration (live DB connection)
# ---------------------------------------------------------------------------

def run_migrations_online() -> None:
    """Run migrations in online mode (default).

    Creates a connection from the Alembic config and runs migrations.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
