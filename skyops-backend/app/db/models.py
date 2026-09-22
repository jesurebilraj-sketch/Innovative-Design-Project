"""SQLAlchemy ORM models for SkyOps backend."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from app.db.session import Base


def generate_uuid() -> str:
    """Generate string UUID."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class Airport(Base):
    """Airport entity representing a civil aviation aerodrome."""
    __tablename__ = "airports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    iata_code = Column(String(3), unique=True, nullable=False, index=True)
    icao_code = Column(String(4), unique=True, nullable=True, index=True)
    name = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timezone = Column(String(50), nullable=False, default="UTC")
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    gates = relationship("Gate", back_populates="airport", cascade="all, delete-orphan")
    departing_flights = relationship("Flight", foreign_keys="Flight.origin_airport_id", back_populates="origin_airport")
    arriving_flights = relationship("Flight", foreign_keys="Flight.destination_airport_id", back_populates="destination_airport")
    weather_records = relationship("Weather", back_populates="airport", cascade="all, delete-orphan")


class Gate(Base):
    """Gate infrastructure entity at an airport."""
    __tablename__ = "gates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    airport_id = Column(String(36), ForeignKey("airports.id", ondelete="CASCADE"), nullable=False, index=True)
    gate_code = Column(String(20), nullable=False, index=True)
    terminal = Column(String(50), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    aircraft_size_limit = Column(String(30), nullable=False, default="NARROW_BODY")  # e.g., REGIONAL, NARROW_BODY, WIDE_BODY
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    airport = relationship("Airport", back_populates="gates")
    assignments = relationship("GateAssignment", back_populates="gate", cascade="all, delete-orphan")


class Flight(Base):
    """Scheduled or operational flight entity."""
    __tablename__ = "flights"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    flight_number = Column(String(20), nullable=False, index=True)
    airline_code = Column(String(10), nullable=False, index=True)
    aircraft_id = Column(String(50), nullable=True, index=True)  # Tail number / registration for turnaround pairing
    origin_airport_id = Column(String(36), ForeignKey("airports.id"), nullable=False, index=True)
    destination_airport_id = Column(String(36), ForeignKey("airports.id"), nullable=False, index=True)
    scheduled_departure = Column(DateTime(timezone=True), nullable=False, index=True)
    scheduled_arrival = Column(DateTime(timezone=True), nullable=False, index=True)
    actual_departure = Column(DateTime(timezone=True), nullable=True)
    actual_arrival = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(30), nullable=False, default="SCHEDULED")  # SCHEDULED, EN_ROUTE, LANDED, DELAYED, CANCELLED
    cancelled = Column(Boolean, nullable=False, default=False)
    diverted = Column(Boolean, nullable=False, default=False)
    passenger_count = Column(Integer, nullable=True)
    block_time_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    origin_airport = relationship("Airport", foreign_keys=[origin_airport_id], back_populates="departing_flights")
    destination_airport = relationship("Airport", foreign_keys=[destination_airport_id], back_populates="arriving_flights")
    predictions = relationship("Prediction", back_populates="flight", cascade="all, delete-orphan")
    gate_assignments = relationship("GateAssignment", back_populates="flight", cascade="all, delete-orphan")


class Weather(Base):
    """Weather observation or forecast snapshot for an airport location and time."""
    __tablename__ = "weather"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    airport_id = Column(String(36), ForeignKey("airports.id", ondelete="CASCADE"), nullable=False, index=True)
    observed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    temperature_c = Column(Float, nullable=True)
    precipitation_mm = Column(Float, nullable=True)
    rain_mm = Column(Float, nullable=True)
    visibility_km = Column(Float, nullable=True)
    wind_speed_mps = Column(Float, nullable=True)
    wind_direction_deg = Column(Float, nullable=True)
    pressure_hpa = Column(Float, nullable=True)
    cloud_cover_pct = Column(Float, nullable=True)
    source = Column(String(50), nullable=False, default="open-meteo")
    raw_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    airport = relationship("Airport", back_populates="weather_records")


class Prediction(Base):
    """Delay prediction record generated by an ML model or fallback predictor."""
    __tablename__ = "predictions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    flight_id = Column(String(36), ForeignKey("flights.id", ondelete="CASCADE"), nullable=False, index=True)
    generated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    delayed_probability = Column(Float, nullable=False)
    predicted_delay_minutes = Column(Float, nullable=False)
    arrival_delay_minutes = Column(Float, nullable=True)
    departure_delay_minutes = Column(Float, nullable=True)
    prediction_class = Column(String(30), nullable=False)  # DELAYED or ON_TIME
    input_snapshot = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    flight = relationship("Flight", back_populates="predictions")


class GateAssignment(Base):
    """Gate assignment or recommendation record with occupancy intervals."""
    __tablename__ = "gate_assignments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    flight_id = Column(String(36), ForeignKey("flights.id", ondelete="CASCADE"), nullable=False, index=True)
    gate_id = Column(String(36), ForeignKey("gates.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_type = Column(String(30), nullable=False, default="SCHEDULED")  # SCHEDULED, RECOMMENDED, REASSIGNED, MANUAL
    score = Column(Float, nullable=True)
    conflict_risk = Column(Float, nullable=True)
    valid_from = Column(DateTime(timezone=True), nullable=False, index=True)
    valid_to = Column(DateTime(timezone=True), nullable=False, index=True)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    flight = relationship("Flight", back_populates="gate_assignments")
    gate = relationship("Gate", back_populates="assignments")
