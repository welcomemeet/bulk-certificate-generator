import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.database import Base, get_db
from app.main import app


# Create a unique temporary SQLite database for the test session.
fd, db_path = tempfile.mkstemp(
    prefix="bulk_certificate_test_",
    suffix=".db",
)

os.close(fd)


TEST_DATABASE_URL = f"sqlite:///{db_path}"


engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
)


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture(
    scope="session",
    autouse=True,
)
def setup_database():
    """
    Create all database tables before the test suite starts.
    """
    Base.metadata.create_all(
        bind=engine
    )

    yield

    engine.dispose()

    try:
        Path(db_path).unlink()
    except PermissionError:
        pass


@pytest.fixture()
def test_session_factory():
    """
    Provide the same database session factory
    used by the FastAPI test client.
    """
    return TestingSessionLocal


@pytest.fixture()
def client():
    """
    FastAPI test client using the test SQLite database.
    """

    def override_get_db():
        db = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[
        get_db
    ] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()