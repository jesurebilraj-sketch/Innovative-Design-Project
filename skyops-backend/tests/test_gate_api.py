"""Test Gate API endpoints and availability check."""

from datetime import timedelta


def test_check_gate_availability_api_free(client, seed_data):
    """Verify checking availability for an unoccupied interval on Gate G02."""
    now = seed_data["now"]
    gate_g2 = seed_data["gate_g2"]

    payload = {
        "gate_id": gate_g2.id,
        "start_time": (now + timedelta(hours=5)).isoformat(),
        "end_time": (now + timedelta(hours=6)).isoformat(),
        "aircraft_size": "NARROW_BODY",
    }
    response = client.post("/api/v1/gates/check-availability", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["gate_id"] == gate_g2.id
    assert data["is_available"] is True
    assert data["has_conflict"] is False


def test_check_gate_availability_api_conflict(client, seed_data):
    """Verify checking availability for an occupied interval on Gate G01 detects conflict."""
    now = seed_data["now"]
    gate_g1 = seed_data["gate_g1"]

    # G01 has assignment from now - 15min to now + 45min
    payload = {
        "gate_id": gate_g1.id,
        "start_time": now.isoformat(),
        "end_time": (now + timedelta(minutes=30)).isoformat(),
        "aircraft_size": "NARROW_BODY",
    }
    response = client.post("/api/v1/gates/check-availability", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["gate_id"] == gate_g1.id
    assert data["is_available"] is False
    assert data["has_conflict"] is True
    assert "flt-002" in data["conflicting_flight_ids"]


def test_check_gate_availability_api_unknown_gate(client, seed_data):
    """Verify 404 response for checking availability on non-existent gate."""
    now = seed_data["now"]
    payload = {
        "gate_id": "non-existent-gate",
        "start_time": now.isoformat(),
        "end_time": (now + timedelta(hours=1)).isoformat(),
    }
    response = client.post("/api/v1/gates/check-availability", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "GATE_NOT_FOUND"
