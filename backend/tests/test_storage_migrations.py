import os

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text

from app.core.migrations import migrate, schema_current, migration_config
from alembic import command
from app.models import Base


@pytest.fixture
def storage_engine(tmp_path):
    # POSTGRES_TEST_URL must refer to a disposable CI database.
    url = os.getenv("POSTGRES_TEST_URL", "sqlite:///" + str(tmp_path / "storage.db"))
    engine = create_engine(url)
    if engine.dialect.name == "postgresql":
        assert engine.url.database == "careermind_test", "Refusing a non-test database"
        with engine.begin() as connection:
            connection.execute(text("DROP SCHEMA public CASCADE"))
            connection.execute(text("CREATE SCHEMA public"))
    yield engine
    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(text("DROP SCHEMA public CASCADE"))
            connection.execute(text("CREATE SCHEMA public"))
    engine.dispose()


@pytest.mark.parametrize("legacy", [False, True])
def test_fresh_and_legacy_migration_preserve_data(storage_engine, legacy):
    if legacy:
        with storage_engine.begin() as connection:
            command.upgrade(migration_config(connection), "0001_baseline")
    else:
        migrate(storage_engine)
    with storage_engine.begin() as connection:
        connection.execute(text(
            "INSERT INTO users (id, email, hashed_password) VALUES (123, 'saved@example.com', 'private')"
        ))
    migrate(storage_engine)
    migrate(storage_engine)
    with storage_engine.connect() as connection:
        assert schema_current(connection)
        assert connection.execute(text("SELECT email FROM users WHERE id = 123")).scalar() == "saved@example.com"
        assert connection.execute(text("SELECT session_version FROM users WHERE id = 123")).scalar() == 0
        assert not compare_metadata(MigrationContext.configure(connection), Base.metadata)


def test_unknown_legacy_schema_is_not_stamped(storage_engine):
    with storage_engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
        connection.execute(text("INSERT INTO users (id) VALUES (7)"))
    with pytest.raises(RuntimeError, match="baseline"):
        migrate(storage_engine)
    with storage_engine.connect() as connection:
        assert connection.execute(text("SELECT id FROM users")).scalar() == 7
        assert "alembic_version" not in inspect(connection).get_table_names()


def test_unknown_revision_fails_closed(storage_engine):
    migrate(storage_engine)
    with storage_engine.begin() as connection:
        connection.execute(text("UPDATE alembic_version SET version_num = 'unknown_future'"))
    with pytest.raises(Exception, match="unknown_future"):
        migrate(storage_engine)
    with storage_engine.connect() as connection:
        assert not schema_current(connection)


def test_readiness_rejects_unversioned_schema(storage_engine, monkeypatch):
    import importlib
    router = importlib.import_module("app.api.router")
    monkeypatch.setattr(router, "engine", storage_engine)
    assert router.readiness().status_code == 503
    migrate(storage_engine)
    assert router.readiness() == {"status": "ready"}


def test_unversioned_databases_require_baseline_adoption_release(storage_engine):
    Base.metadata.create_all(storage_engine)
    with pytest.raises(RuntimeError, match="baseline"):
        migrate(storage_engine)
