import os
import pytest
from sqlalchemy import create_engine, text
from alembic import command
from app.core.migrations import migrate, migration_config, schema_current
from app.core.security import get_password_hash


def test_case_varied_login_and_duplicate_registration(application_client):
    client = application_client
    email_mixed = "Audit.Case@example.com"
    pwd = "SecurePassword123!"
    
    # 1. Register with mixed-case email
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": email_mixed,
        "full_name": "Audit Case User",
        "password": pwd
    })
    assert reg_resp.status_code == 201, reg_resp.text
    reg_data = reg_resp.json()
    assert reg_data["user"]["email"] == "audit.case@example.com"
    
    # 2. Duplicate registration with lowercase spelling is rejected
    dup_resp = client.post("/api/v1/auth/register", json={
        "email": "audit.case@example.com",
        "full_name": "Audit Case Lower",
        "password": pwd
    })
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.json()["detail"]
    
    # Duplicate registration with uppercase spelling is also rejected
    dup_upper = client.post("/api/v1/auth/register", json={
        "email": "AUDIT.CASE@EXAMPLE.COM",
        "full_name": "Audit Case Upper",
        "password": pwd
    })
    assert dup_upper.status_code == 400
    assert "already exists" in dup_upper.json()["detail"]

    # 3. Login with lowercase spelling succeeds
    login_lower = client.post("/api/v1/auth/login", json={
        "email": "audit.case@example.com",
        "password": pwd
    })
    assert login_lower.status_code == 200
    assert "access_token" in login_lower.json()

    # 4. Login with mixed case spelling succeeds
    login_mixed = client.post("/api/v1/auth/login", json={
        "email": "Audit.Case@example.com",
        "password": pwd
    })
    assert login_mixed.status_code == 200
    assert "access_token" in login_mixed.json()

    # 5. Login with uppercase spelling succeeds
    login_upper = client.post("/api/v1/auth/login", json={
        "email": "AUDIT.CASE@EXAMPLE.COM",
        "password": pwd
    })
    assert login_upper.status_code == 200
    assert "access_token" in login_upper.json()

    # 6. Wrong password still returns 401
    bad_login = client.post("/api/v1/auth/login", json={
        "email": "audit.case@example.com",
        "password": "WrongPassword999!"
    })
    assert bad_login.status_code == 401


@pytest.fixture
def migration_test_engine(tmp_path):
    url = os.getenv("POSTGRES_TEST_URL", "sqlite:///" + str(tmp_path / "email_migration.db"))
    engine = create_engine(url)
    if engine.dialect.name == "postgresql":
        assert engine.url.database == "careermind_test", "Refusing a non-test database"
        with engine.begin() as connection:
            connection.execute(text("DROP SCHEMA public CASCADE"))
            connection.execute(text("CREATE SCHEMA public"))
    yield engine
    engine.dispose()


def test_migration_normalizes_unnormalized_accounts_without_collisions(migration_test_engine):
    # Upgrade to 0002 (before email normalization migration)
    with migration_test_engine.begin() as connection:
        command.upgrade(migration_config(connection), "0002_session_version")
        connection.execute(text(
            "INSERT INTO users (id, email, hashed_password, session_version) "
            "VALUES (501, 'Mixed.Case@Example.Com', 'hash', 0)"
        ))
    
    # Run migrations to head (applies 0003)
    migrate(migration_test_engine)
    
    with migration_test_engine.connect() as connection:
        assert schema_current(connection)
        normalized = connection.execute(text("SELECT email FROM users WHERE id = 501")).scalar()
        assert normalized == "mixed.case@example.com"


def test_migration_detects_and_refuses_to_silently_merge_case_colliding_accounts(migration_test_engine):
    # Upgrade to 0002
    with migration_test_engine.begin() as connection:
        command.upgrade(migration_config(connection), "0002_session_version")
        # In SQLite or Postgres without lowercase unique index, insert two rows with same lowercase form
        connection.execute(text(
            "INSERT INTO users (id, email, hashed_password, session_version) "
            "VALUES (601, 'collision@example.com', 'hash1', 0)"
        ))
        connection.execute(text(
            "INSERT INTO users (id, email, hashed_password, session_version) "
            "VALUES (602, 'COLLISION@EXAMPLE.COM', 'hash2', 0)"
        ))
    
    # Running migrate must fail with RuntimeError indicating colliding accounts detected
    with pytest.raises(RuntimeError, match="Existing case-colliding accounts detected"):
        migrate(migration_test_engine)
    
    # Verify neither account was silently modified or merged
    with migration_test_engine.connect() as connection:
        rows = connection.execute(text("SELECT id, email FROM users WHERE id IN (601, 602) ORDER BY id")).fetchall()
        assert len(rows) == 2
        assert rows[0][1] == "collision@example.com"
        assert rows[1][1] == "COLLISION@EXAMPLE.COM"
