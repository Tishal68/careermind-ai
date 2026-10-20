import pytest
from app.core.request_limits import _expensive

@pytest.fixture(autouse=True)
def isolate_rate_limit_state():
    # Each fixture's user IDs belong to a different isolated database.
    _expensive.entries.clear()
    yield
    _expensive.entries.clear()


@pytest.fixture
def application_client(tmp_path, monkeypatch):
    import importlib
    from threading import Event
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.database import get_db
    main = importlib.import_module("app.main")
    router = importlib.import_module("app.api.router")
    engine = create_engine("sqlite:///" + str(tmp_path / "application.db"),
                           connect_args={"check_same_thread": False})
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(main, "engine", engine)
    monkeypatch.setattr(main, "SessionLocal", factory)
    monkeypatch.setattr(main, "start_dispatcher", lambda: Event())
    monkeypatch.setattr(router, "engine", engine)
    def database():
        with factory() as session:
            yield session
    main.app.dependency_overrides[get_db] = database
    try:
        with TestClient(main.app) as client:
            yield client
    finally:
        main.app.dependency_overrides.pop(get_db, None)
        engine.dispose()
