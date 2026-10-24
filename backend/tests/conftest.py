import os

# Must be set BEFORE the app is imported. No paid API calls are ever made by the test-suite.
os.environ.update({
    "APP_ENV": "test", "DATABASE_URL": "sqlite:///:memory:", "RATE_LIMIT_ENABLED": "false",
    "LLM_PROVIDER": "mock", "LLM_RETRY_BACKOFF_SECONDS": "0", "SECRET_KEY": "test-secret-key-test-secret-key-123456",
})

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.ai.mock import MockProvider  # noqa: E402
from app.api.deps import get_provider  # noqa: E402
from app.core.database import Base, get_db, make_engine  # noqa: E402
from app.main import app  # noqa: E402
import app.models  # noqa: E402,F401


@pytest.fixture()
def engine(tmp_path):
    # Set TEST_DATABASE_URL=postgresql+psycopg://... to run the whole suite against PostgreSQL.
    url = os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{tmp_path / 'test.db'}"
    eng = make_engine(url)
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def db(engine):
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    yield session
    session.close()


@pytest.fixture()
def provider():
    return MockProvider()


@pytest.fixture()
def make_client(engine, provider):
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def _db():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_provider] = lambda: provider
    clients = []

    def factory() -> TestClient:  # every client has its own cookie jar = its own logged-in user
        c = TestClient(app)
        clients.append(c)
        return c

    yield factory
    app.dependency_overrides.clear()


@pytest.fixture()
def client(make_client):
    c = make_client()
    r = c.post("/api/v1/auth/register", json={"email": "owner@example.com", "password": "correct-horse-1"})
    assert r.status_code == 201, r.text
    return c


@pytest.fixture()
def other(make_client):
    c = make_client()
    r = c.post("/api/v1/auth/register", json={"email": "intruder@example.com", "password": "correct-horse-2"})
    assert r.status_code == 201, r.text
    return c
