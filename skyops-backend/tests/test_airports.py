"""Test Airport API endpoints."""

def test_list_airports(client, seed_data):
    """Verify listing all registered airports."""
    response = client.get("/api/v1/airports/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    iatas = [a["iata_code"] for a in data]
    assert "AMS" in iatas
    assert "RTM" in iatas


def test_get_airport_by_id(client, seed_data):
    """Verify retrieving airport by UUID."""
    response = client.get("/api/v1/airports/apt-ams")
    assert response.status_code == 200
    data = response.json()
    assert data["iata_code"] == "AMS"
    assert data["city"] == "Amsterdam"


def test_get_airport_by_iata(client, seed_data):
    """Verify retrieving airport by 3-letter IATA code."""
    response = client.get("/api/v1/airports/RTM")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "apt-rtm"
    assert data["name"] == "Rotterdam The Hague Airport"


def test_get_airport_not_found(client, seed_data):
    """Verify 404 response for non-existent airport."""
    response = client.get("/api/v1/airports/XYZ")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "AIRPORT_NOT_FOUND"


def test_list_airport_gates(client, seed_data):
    """Verify listing active gates for an airport."""
    response = client.get("/api/v1/airports/apt-rtm/gates")
    assert response.status_code == 200
    data = response.json()
    # G01 and G02 are active, G03 is inactive
    gate_codes = [g["gate_code"] for g in data]
    assert "G01" in gate_codes
    assert "G02" in gate_codes
    assert "G03" not in gate_codes
