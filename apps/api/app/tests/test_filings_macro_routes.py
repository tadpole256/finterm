from __future__ import annotations

from fastapi.testclient import TestClient


def test_filings_sync_and_read_routes(client: TestClient) -> None:
    sync_response = client.post("/api/v1/filings/sync")
    assert sync_response.status_code == 200
    sync_payload = sync_response.json()
    assert sync_payload["fetched_count"] >= 1
    assert sync_payload["inserted_count"] >= 1
    assert sync_payload["updated_summary_count"] >= 1

    filings_response = client.get("/api/v1/filings", params={"symbol": "AAPL"})
    assert filings_response.status_code == 200
    filings = filings_response.json()
    assert filings
    assert all(item["symbol"] == "AAPL" for item in filings)
    assert any(item["summary"] is not None for item in filings)

    detail_id = filings[0]["id"]
    detail_response = client.get(f"/api/v1/filings/{detail_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["id"] == detail_id
    assert "raw_text" in detail


def test_macro_sync_and_list_routes(client: TestClient) -> None:
    sync_response = client.post("/api/v1/macro/sync")
    assert sync_response.status_code == 200
    sync_payload = sync_response.json()
    assert sync_payload["series_upserted"] >= 1
    assert sync_payload["events_inserted"] >= 1

    series_response = client.get("/api/v1/macro/series")
    assert series_response.status_code == 200
    series = series_response.json()
    assert series
    assert any(item["code"] == "US_CPI_YOY" for item in series)

    events_response = client.get("/api/v1/macro/events", params={"days_ahead": 30})
    assert events_response.status_code == 200
    events = events_response.json()
    assert events
    assert any(event["title"] == "CPI (YoY)" for event in events)
