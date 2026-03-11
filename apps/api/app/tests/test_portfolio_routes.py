from __future__ import annotations

from fastapi.testclient import TestClient


def test_portfolio_overview_returns_holdings_and_exposure(client: TestClient) -> None:
    response = client.get("/api/v1/portfolio/overview")
    assert response.status_code == 200

    payload = response.json()
    assert payload["portfolio"]["name"] == "Personal"
    assert payload["summary"]["position_count"] >= 2

    symbols = {holding["symbol"] for holding in payload["holdings"]}
    assert {"AAPL", "MSFT"}.issubset(symbols)

    aapl_holding = next(holding for holding in payload["holdings"] if holding["symbol"] == "AAPL")
    assert aapl_holding["note_count"] >= 1
    assert "Core" in aapl_holding["watchlists"]

    assert payload["exposures"]


def test_portfolio_transactions_create_and_delete(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/portfolio/transactions",
        json={
            "symbol": "NVDA",
            "side": "buy",
            "quantity": 3,
            "price": 880,
            "fees": 1.25,
            "notes": "Phase 4 test transaction",
        },
    )
    assert create_response.status_code == 201
    transaction_id = create_response.json()["id"]

    positions = client.get("/api/v1/portfolio/positions")
    assert positions.status_code == 200
    nvda_holding = next(
        holding for holding in positions.json()["holdings"] if holding["symbol"] == "NVDA"
    )
    assert nvda_holding["quantity"] == 3.0

    delete_response = client.delete(f"/api/v1/portfolio/transactions/{transaction_id}")
    assert delete_response.status_code == 204

    after_delete = client.get("/api/v1/portfolio/transactions")
    assert all(txn["id"] != transaction_id for txn in after_delete.json()["transactions"])


def test_portfolio_transactions_reject_unknown_symbol(client: TestClient) -> None:
    response = client.post(
        "/api/v1/portfolio/transactions",
        json={
            "symbol": "UNKNOWN",
            "side": "buy",
            "quantity": 1,
            "price": 100,
        },
    )
    assert response.status_code == 400
