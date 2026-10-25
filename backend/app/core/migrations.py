"""Versioned startup migrations for the supported single-instance deployment."""
from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

from app.models import Base

BASELINE = "0001_baseline"


def migration_config(connection):
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[2] / "migrations"))
    config.attributes["connection"] = connection
    return config


def schema_current(connection):
    config = migration_config(connection)
    return MigrationContext.configure(connection).get_current_heads() == (
        ScriptDirectory.from_config(config).get_current_head(),
    )


def migrate(engine):
    # SQLite deployment must have one migrator, before web/worker startup.
    # PostgreSQL serializes competing migrators using a transaction-scoped lock.
    with engine.begin() as connection:
        if connection.dialect.name == "postgresql":
            from sqlalchemy import text
            connection.execute(text("SELECT pg_advisory_xact_lock(741920601)"))
        config = migration_config(connection)
        context = MigrationContext.configure(connection)
        tables = set(inspect(connection).get_table_names()) - {"alembic_version"}
        if tables and not context.get_current_heads():
            # Adoption is intentionally limited to the exact pre-migration
            # release. Never mark an unknown or outdated schema as upgraded.
            head = ScriptDirectory.from_config(config).get_current_head()
            if head != BASELINE or compare_metadata(context, Base.metadata):
                raise RuntimeError(
                    "Unversioned database does not match the supported baseline. "
                    "Back it up and reconcile its schema before starting the application."
                )
            command.stamp(config, BASELINE)
        command.upgrade(config, "head")
        if connection.dialect.name == "postgresql":
            # Supabase exposes public tables through a Data API. These tables
            # belong exclusively to our backend owner; no client policies exist.
            quote = connection.dialect.identifier_preparer.quote
            for table in Base.metadata.sorted_tables:
                connection.exec_driver_sql(f"ALTER TABLE {quote(table.name)} ENABLE ROW LEVEL SECURITY")
        if not schema_current(connection):
            raise RuntimeError("Database schema revision is not current")
