# alembic/env.py

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# --- Configuration Start ---

# 1. Add the project root directory to the Python path.
# This allows Alembic to find your 'app' package.
# The path is calculated relative to this env.py file's location.
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

# 2. Import your app's settings and the SQLAlchemy Base
from app.core.config import settings
from app.core.database import Base  # This Base now has all your models' metadata

# 3. This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

print("--- DEBUGGING alembic/env.py ---")
# Check if the path was added correctly
print(f"Current sys.path includes: {sys.path[0]}") 
# Check what tables the Base object knows about
print(f"Tables found in Base.metadata: {Base.metadata.tables.keys()}")
print("--- END DEBUGGING ---")

# 4. Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 5. Set the target_metadata for Alembic's 'autogenerate' support.
target_metadata = Base.metadata

# --- Configuration End ---


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # In offline mode, we use the URL directly from our settings.
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # In online mode, we override the URL from alembic.ini with our settings
    # and use our app's existing SQLAlchemy engine.
    
    # Create a configuration dictionary from our settings
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()