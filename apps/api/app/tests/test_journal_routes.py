from __future__ import annotations

from fastapi.testclient import TestClient


def test_journal_entry_create_and_list(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/journal/entries",
        json={
            "symbol": "AAPL",
            "entry_type": "post_mortem",
            "title": "Trim review",
            "body": "Reduced exposure into event risk.",
            "tags": ["discipline", "risk"],
        },
    )
    assert create_response.status_code == 201
    payload = create_response.json()
    assert payload["symbol"] == "AAPL"
    assert payload["entry_type"] == "post_mortem"

    list_response = client.get("/api/v1/journal/entries", params={"symbol": "AAPL"})
    assert list_response.status_code == 200
    assert any(item["id"] == payload["id"] for item in list_response.json())
