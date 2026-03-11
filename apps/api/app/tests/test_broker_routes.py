from __future__ import annotations

from fastapi.testclient import TestClient


def test_broker_capabilities_and_order_preview(client: TestClient) -> None:
    capabilities = client.get("/api/v1/broker/capabilities")
    assert capabilities.status_code == 200
    payload = capabilities.json()
    assert payload["capabilities"]["provider"] == "mock_broker"
    assert payload["capabilities"]["supports_order_preview"] is True
    assert payload["capabilities"]["can_submit_orders"] is False
    assert payload["session"]["connected"] is True

    preview = client.post(
        "/api/v1/broker/orders/preview",
        json={
            "symbol": "AAPL",
            "side": "buy",
            "order_type": "market",
            "quantity": 10,
        },
    )
    assert preview.status_code == 200
    preview_payload = preview.json()
    assert preview_payload["symbol"] == "AAPL"
    assert preview_payload["can_submit"] is False
    assert preview_payload["restrictions"]


def test_broker_sync_reconcile_exceptions_and_resolution(client: TestClient) -> None:
    sync_response = client.post("/api/v1/broker/sync")
    assert sync_response.status_code == 201
    sync_payload = sync_response.json()
    assert sync_payload["status"] == "completed"
    assert sync_payload["fetched_accounts"] >= 1
    assert sync_payload["fetched_positions"] >= 1

    reconciliation = client.get("/api/v1/broker/reconcile")
    assert reconciliation.status_code == 200
    payload = reconciliation.json()
    assert "summary" in payload
    assert payload["summary"]["broker_symbol_count"] >= 1
    assert payload["open_exception_count"] >= 0

    exceptions = client.get("/api/v1/broker/reconciliation-exceptions")
    assert exceptions.status_code == 200
    rows = exceptions.json()
    assert isinstance(rows, list)
    if rows:
        exception_id = rows[0]["id"]
        resolve_response = client.patch(
            f"/api/v1/broker/reconciliation-exceptions/{exception_id}/resolve",
            json={"resolution_note": "Resolved in test"},
        )
        assert resolve_response.status_code == 200
        assert resolve_response.json()["status"] == "resolved"


def test_broker_order_event_creation_and_listing(client: TestClient) -> None:
    sync_response = client.post("/api/v1/broker/sync")
    assert sync_response.status_code == 201

    accounts = client.get("/api/v1/broker/accounts").json()
    assert accounts
    account_id = accounts[0]["id"]

    create_event = client.post(
        "/api/v1/broker/order-events",
        json={
            "broker_account_id": account_id,
            "external_order_id": "mock-order-001",
            "symbol": "AAPL",
            "side": "buy",
            "order_type": "limit",
            "status": "filled",
            "quantity": 5,
            "limit_price": 215.5,
            "filled_quantity": 5,
            "avg_fill_price": 215.4,
            "event_payload": {"venue": "SIM"},
            "create_journal_entry": True,
        },
    )
    assert create_event.status_code == 201
    assert create_event.json()["external_order_id"] == "mock-order-001"

    list_events = client.get("/api/v1/broker/order-events", params={"symbol": "AAPL"})
    assert list_events.status_code == 200
    events = list_events.json()
    assert events
    assert any(event["external_order_id"] == "mock-order-001" for event in events)
