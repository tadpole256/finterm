from __future__ import annotations

from fastapi.testclient import TestClient


def test_screening_run_with_extended_filters(client: TestClient) -> None:
    response = client.get(
        "/api/v1/screening/run",
        params={
            "price_min": 100,
            "price_max": 900,
            "change_percent_min": -2,
            "change_percent_max": 2,
            "volume_min": 1000000,
            "asset_type": "equity",
            "sort_by": "price",
            "sort_direction": "desc",
            "limit": 5,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["results"]
    assert len(payload["results"]) <= 5
    assert all(item["asset_type"] == "equity" for item in payload["results"])


def test_saved_screen_crud_and_run(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/screening/screens",
        json={
            "name": "Tech Momentum",
            "criteria": {
                "sector": "Technology",
                "price_min": 100,
                "change_percent_min": -5,
                "sort_by": "change_percent",
                "sort_direction": "desc",
                "limit": 10,
            },
        },
    )
    assert create_response.status_code == 201
    screen_id = create_response.json()["id"]

    list_response = client.get("/api/v1/screening/screens")
    assert list_response.status_code == 200
    assert any(item["id"] == screen_id for item in list_response.json())

    run_response = client.post(f"/api/v1/screening/screens/{screen_id}/run")
    assert run_response.status_code == 200
    run_payload = run_response.json()
    assert run_payload["screen"]["id"] == screen_id
    assert isinstance(run_payload["results"], list)

    update_response = client.patch(
        f"/api/v1/screening/screens/{screen_id}",
        json={"name": "Tech Momentum Updated"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Tech Momentum Updated"

    delete_response = client.delete(f"/api/v1/screening/screens/{screen_id}")
    assert delete_response.status_code == 204
