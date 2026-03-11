from fastapi.testclient import TestClient


def test_dashboard_route(client: TestClient) -> None:
    response = client.get("/api/v1/market/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_provider"] == "mock"
    assert "market_snapshot" in payload
    assert "watchlists" in payload
    assert payload["morning_brief"]["headline"]


def test_instrument_search_route(client: TestClient) -> None:
    response = client.get("/api/v1/instruments/search", params={"q": "apple"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["results"]
    assert payload["results"][0]["symbol"] == "AAPL"


def test_security_workspace_route(client: TestClient) -> None:
    response = client.get("/api/v1/workspaces/security/AAPL")

    assert response.status_code == 200
    payload = response.json()
    assert payload["instrument"]["symbol"] == "AAPL"
    assert payload["bars"]
    assert payload["indicators"]["sma20"]
    assert "what_changed" in payload


def test_bars_route(client: TestClient) -> None:
    response = client.get("/api/v1/prices/bars/AAPL", params={"timeframe": "6M"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "AAPL"
    assert len(payload["bars"]) > 50
