"""Test Flight API endpoints and turnaround lookup."""

def test_list_flights(client, seed_data):
    """Verify listing flights."""
    response = client.get("/api/v1/flights/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    f_nums = [f["flight_number"] for f in data]
    assert "KL101" in f_nums
    assert "KL102" in f_nums


def test_list_flights_filtered_by_airport(client, seed_data):
    """Verify filtering flights by airport."""
    response = client.get("/api/v1/flights/?airport_id=apt-rtm")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_get_flight_details(client, seed_data):
    """Verify retrieving flight details with airports."""
    response = client.get("/api/v1/flights/flt-001")
    assert response.status_code == 200
    data = response.json()
    assert data["flight_number"] == "KL101"
    assert data["origin_airport"]["iata_code"] == "AMS"
    assert data["destination_airport"]["iata_code"] == "RTM"


def test_get_flight_not_found(client, seed_data):
    """Verify 404 response for non-existent flight."""
    response = client.get("/api/v1/flights/non-existent-id")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "FLIGHT_NOT_FOUND"


def test_get_flight_turnaround(client, seed_data):
    """Verify turnaround pairing via API."""
    response = client.get("/api/v1/flights/flt-001/turnaround")
    assert response.status_code == 200
    data = response.json()
    assert data["arriving_flight_id"] == "flt-001"
    assert data["departing_flight_id"] == "flt-002"
    assert data["departing_flight_number"] == "KL102"
    assert data["aircraft_id"] == "PH-AAA"
    assert data["status"] == "MATCHED"
    assert data["turnaround_buffer_minutes"] == 60.0
    assert data["is_feasible"] is True
