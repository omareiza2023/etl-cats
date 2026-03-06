import os
import sys
from dotenv import load_dotenv
from sqlalchemy import pool
from alembic import context

load_dotenv()

sys.path.insert(0, '.')

# ── Importar database y modelos ───────────────────────────────
from scripts.database import engine, Base
from scripts.models import Raza, Imagen, MetricasETL  # noqa: F401

# ── Configuración de Alembic ──────────────────────────────────
config = context.config
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Ejecuta migraciones en modo offline."""
    from scripts.database import DATABASE_URL
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecuta migraciones en modo online usando el engine existente."""
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()