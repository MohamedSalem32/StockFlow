from logging.config import fileConfig
from alembic import context

 
from app.db import Base
import app.models
target_metadata = Base.metadata

# 2) Alembic config
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
 

# 4) Use settings if you have it, or fall back to alembic.ini sqlalchemy.url
from sqlalchemy import create_engine, pool

try:
    from app.core.settings import settings  # noqa
    DB_URL = settings.DB_URL
except Exception:
    DB_URL = config.get_main_option("sqlalchemy.url")

def run_migrations_offline() -> None:
    context.configure(
        url=DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = create_engine(DB_URL, poolclass=pool.NullPool, future=True)
    with connectable.connect() as connection:
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
