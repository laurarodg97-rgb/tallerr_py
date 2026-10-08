"""Configuracion de Alembic para la URL del entorno o de ``.env``."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import modelos  # noqa: F401 - registra todas las tablas en Base.metadata
from config import get_settings
from database import Base


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

database_url = get_settings().database_url
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Genera SQL de migracion sin abrir una conexion."""

    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Aplica la revision sobre la base de datos configurada."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        if connection.dialect.name == "sqlite":
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
