"""Database seed script populating demo airports, gates, flights, and rotations.

Seed data is designed to demonstrate:
1. Multi-leg aircraft rotations for turnaround pairing (e.g. PH-BVA arriving at RTM then departing).
2. Gate assignments with both free and occupied slots for conflict checking.
"""

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from datetime import datetime, timedelta, timezone
from app.db.session import SessionLocal, init_db
from app.db.models import Airport, Gate, Flight, GateAssignment, Weather


def seed_database():
    """Populate database with reproducible demo operational data."""
    init_db()
    db = SessionLocal()

    try:
        # Clear existing data if any
        db.query(GateAssignment).delete()
        db.query(Flight).delete()
        db.query(Gate).delete()
        db.query(Weather).delete()
        db.query(Airport).delete()
        db.commit()

        # 1. Airports
        ams = Airport(
            id="airport-ams",
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
            id="airport-rtm",
            iata_code="RTM",
            icao_code="EHRD",
            name="Rotterdam The Hague Airport",
            city="Rotterdam",
            country="Netherlands",
            latitude=51.9569,
            longitude=4.4372,
            timezone="Europe/Amsterdam",
        )
        jfk = Airport(
            id="airport-jfk",
            iata_code="JFK",
            icao_code="KJFK",
            name="John F. Kennedy International Airport",
            city="New York",
            country="United States",
            latitude=40.6413,
            longitude=-73.7781,
            timezone="America/New_York",
        )
        db.add_all([ams, rtm, jfk])
        db.commit()

        # 2. Gates at Rotterdam (RTM)
        gate_1 = Gate(
            id="gate-rtm-g01",
            airport_id="airport-rtm",
            gate_code="G01",
            terminal="Terminal 1",
            latitude=51.9570,
            longitude=4.4370,
            aircraft_size_limit="NARROW_BODY",
            is_active=True,
        )
        gate_2 = Gate(
            id="gate-rtm-g02",
            airport_id="airport-rtm",
            gate_code="G02",
            terminal="Terminal 1",
            latitude=51.9572,
            longitude=4.4373,
            aircraft_size_limit="WIDE_BODY",
            is_active=True,
        )
        gate_3 = Gate(
            id="gate-rtm-g03",
            airport_id="airport-rtm",
            gate_code="G03",
            terminal="Terminal 1",
            latitude=51.9575,
            longitude=4.4375,
            aircraft_size_limit="REGIONAL",
            is_active=True,
        )
        db.add_all([gate_1, gate_2, gate_3])
        db.commit()

        # 3. Flights demonstrating multi-leg turnaround on aircraft PH-BVA
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

        # Leg 1: Inbound flight from AMS to RTM on PH-BVA
        flight_in = Flight(
            id="flight-kl-101",
            flight_number="KL101",
            airline_code="KL",
            aircraft_id="PH-BVA",
            origin_airport_id="airport-ams",
            destination_airport_id="airport-rtm",
            scheduled_departure=now - timedelta(hours=2),
            scheduled_arrival=now - timedelta(hours=1),
            actual_departure=now - timedelta(hours=2),
            actual_arrival=now - timedelta(hours=1),
            status="LANDED",
            passenger_count=145,
            block_time_minutes=60,
        )

        # Leg 2: Turnaround outbound departure from RTM to JFK on PH-BVA
        flight_out = Flight(
            id="flight-kl-102",
            flight_number="KL102",
            airline_code="KL",
            aircraft_id="PH-BVA",
            origin_airport_id="airport-rtm",
            destination_airport_id="airport-jfk",
            scheduled_departure=now + timedelta(minutes=45),
            scheduled_arrival=now + timedelta(hours=8),
            status="SCHEDULED",
            passenger_count=160,
            block_time_minutes=435,
        )

        # Independent flight occupying Gate G01
        flight_other = Flight(
            id="flight-ba-404",
            flight_number="BA404",
            airline_code="BA",
            aircraft_id="G-EUPX",
            origin_airport_id="airport-rtm",
            destination_airport_id="airport-ams",
            scheduled_departure=now + timedelta(hours=2),
            scheduled_arrival=now + timedelta(hours=3),
            status="SCHEDULED",
            passenger_count=98,
        )

        db.add_all([flight_in, flight_out, flight_other])
        db.commit()

        # 4. Existing Gate Assignment on Gate G01
        # G01 is occupied between now and now + 1.5 hours by flight-other
        assignment_1 = GateAssignment(
            id="assign-01",
            flight_id="flight-ba-404",
            gate_id="gate-rtm-g01",
            assignment_type="SCHEDULED",
            score=0.85,
            valid_from=now,
            valid_to=now + timedelta(hours=1, minutes=30),
            reason="Scheduled departure occupancy",
        )
        db.add(assignment_1)

        # 5. Baseline weather record for RTM
        weather_rtm = Weather(
            id="weather-rtm-01",
            airport_id="airport-rtm",
            observed_at=now,
            temperature_c=14.5,
            precipitation_mm=0.0,
            rain_mm=0.0,
            visibility_km=10.0,
            wind_speed_mps=4.2,
            wind_direction_deg=220.0,
            pressure_hpa=1013.2,
            cloud_cover_pct=25.0,
            source="open-meteo",
        )
        db.add(weather_rtm)
        db.commit()

        print("Database seeded successfully with demo operational records.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
