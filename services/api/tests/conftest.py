import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import make_engine
from app.ingestion.import_company import persist
from app.main import create_app
from app.models.entities import Base

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures"


@pytest.fixture
def payload():
    return json.loads((FIXTURES / "nue-2025.json").read_text())


@pytest.fixture
def db_engine(tmp_path, payload):
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session, session.begin():
        persist(session, payload, "OFFLINE_FILING_SNAPSHOT")
    yield engine
    engine.dispose()


@pytest.fixture
def client(db_engine):
    with TestClient(create_app(db_engine)) as client:
        yield client
