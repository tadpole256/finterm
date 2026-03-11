from __future__ import annotations

from fastapi.testclient import TestClient


def test_broker_sync_accounts_and_reconciliation(client: TestClient) -> None:
    accounts_before = client.get("/api/v1/broker/accounts")
    assert accounts_before.status_code == 200
    assert accounts_before.json() == []

    sync_response = client.post("/api/v1/broker/sync")
    assert sync_response.status_code == 201
    sync_payload = sync_response.json()
    assert sync_payload["status"] == "completed"
    assert sync_payload["fetched_accounts"] >= 1
    assert sync_payload["fetched_positions"] >= 1

    accounts_after = client.get("/api/v1/broker/accounts")
    assert accounts_after.status_code == 200
    account_rows = accounts_after.json()
    assert account_rows
    assert account_rows[0]["provider"] == "mock_broker"
    assert account_rows[0]["position_count"] >= 1
    assert isinstance(account_rows[0]["positions"], list)

    reconciliation = client.get("/api/v1/broker/reconcile")
    assert reconciliation.status_code == 200
    payload = reconciliation.json()
    assert "summary" in payload
    assert payload["summary"]["broker_symbol_count"] >= 1
    assert "only_local" in payload
    assert "only_broker" in payload
