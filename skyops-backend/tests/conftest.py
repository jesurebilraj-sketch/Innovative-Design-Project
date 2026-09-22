"""Test fixtures and database configuration."""

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.settings import settings
from app.db.models import Airport, Base, Flight, Gate, GateAssignment, Weather
from app.db.session import get_db
from app.main import app

# In-memory SQLite database for isolated test execution
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """Create all database tables before test suite executes."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator:
    """Provide a clean database session for each test, rolling back after completion."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session) -> Generator:
    """TestClient with database dependency overridden."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seed_data(db_session):
    """Seed test database with sample operational records."""
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

    # Airports
    ams = Airport(
        id="apt-ams",
        iata_code="AMS",
        icao_code="EHAM",
        name="Amsterdam Airport Schiphol",
        city="Amsterdam",
        country="Netherlands",
        latitude=52.3086,
        longitude=4.7639,
        timezone="Europe/Amsterdam",
    )
    rtm = Airport(
        id="apt-rtm",
        iata_code="RTM",
        icao_code="EHRD",
        name="Rotterdam The Hague Airport",
        city="Rotterdam",
        country="Netherlands",
        latitude=51.9569,
        longitude=4.4372,
        timezone="Europe/Amsterdam",
    )
    db_session.add_all([ams, rtm])
    db_session.commit()

    # Gates at RTM
    gate_g1 = Gate(
        id="gate-g1",
        airport_id="apt-rtm",
        gate_code="G01",
        terminal="Terminal 1",
        aircraft_size_limit="NARROW_BODY",
        is_active=True,
    )
    gate_g2 = Gate(
        id="gate-g2",
        airport_id="apt-rtm",
        gate_code="G02",
        terminal="Terminal 1",
        aircraft_size_limit="WIDE_BODY",
        is_active=True,
    )
    gate_g3 = Gate(
        id="gate-g3",
        airport_id="apt-rtm",
        gate_code="G03",
        terminal="Terminal 1",
        aircraft_size_limit="REGIONAL",
        is_active=False,  # Inactive gate
    )
    db_session.add_all([gate_g1, gate_g2, gate_g3])
    db_session.commit()

    # Inbound flight (PH-AAA arrives at RTM)
    f1 = Flight(
        id="flt-001",
        flight_number="KL101",
        airline_code="KL",
        aircraft_id="PH-AAA",
        origin_airport_id="apt-ams",
        destination_airport_id="apt-rtm",
        scheduled_departure=now - timedelta(hours=2),
        scheduled_arrival=now - timedelta(hours=1),
        actual_departure=now - timedelta(hours=2),
        actual_arrival=now - timedelta(hours=1),
        status="LANDED",
    )
    # Turnaround outbound flight (PH-AAA departs RTM after 60 min)
    f2 = Flight(
        id="flt-002",
        flight_number="KL102",
        airline_code="KL",
        aircraft_id="PH-AAA",
        origin_airport_id="apt-rtm",
        destination_airport_id="apt-ams",
        scheduled_departure=now,
        scheduled_arrival=now + timedelta(hours=1),
        status="SCHEDULED",
    )
    db_session.add_all([f1, f2])
    db_session.commit()

    # Gate G01 assignment for flight flt-002 between now - 15 min and now + 45 min
    assignment = GateAssignment(
        id="asg-001",
        flight_id="flt-002",
        gate_id="gate-g1",
        assignment_type="SCHEDULED",
        score=0.9,
        valid_from=now - timedelta(minutes=15),
        valid_to=now + timedelta(minutes=45),
        reason="Scheduled departure",
    )
    db_session.add(assignment)
    db_session.commit()

    return {
        "now": now,
        "airport_ams": ams,
        "airport_rtm": rtm,
        "gate_g1": gate_g1,
        "gate_g2": gate_g2,
        "gate_g3": gate_g3,
        "flight_1": f1,
        "flight_2": f2,
        "assignment_1": assignment,
    }


def create_mock_jwt(payload: dict, secret: str = settings.SUPABASE_JWT_SECRET) -> str:
    """Helper creating signed test HS256 JWT tokens."""
    header = {"alg": "HS256", "typ": "JWT"}
    h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signing_input = f"{h_b64}.{p_b64}".encode()
    sig = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode().rstrip("=")
    return f"{h_b64}.{p_b64}.{sig_b64}"
