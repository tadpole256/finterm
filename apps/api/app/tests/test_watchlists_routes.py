from fastapi.testclient import TestClient


def test_watchlist_crud_and_items(client: TestClient) -> None:
    create_response = client.post("/api/v1/watchlists", json={"name": "Test WL", "description": "tmp"})
    assert create_response.status_code == 201
    watchlist_id = create_response.json()["id"]

    add_item_response = client.post(
        f"/api/v1/watchlists/{watchlist_id}/items",
        json={"symbol": "NVDA", "tags": ["momentum"]},
    )
    assert add_item_response.status_code == 200
    assert add_item_response.json()["items"][0]["symbol"] == "NVDA"

    watchlists_response = client.get("/api/v1/watchlists")
    assert watchlists_response.status_code == 200
    payload = watchlists_response.json()
    assert len(payload) >= 2


def test_watchlist_reorder_and_delete_item(client: TestClient) -> None:
    response = client.get("/api/v1/watchlists")
    assert response.status_code == 200

    core = response.json()[0]
    item_ids = [item["id"] for item in core["items"]]
    reordered = list(reversed(item_ids))

    reorder_response = client.patch(
        f"/api/v1/watchlists/{core['id']}/items/reorder",
        json={"item_ids": reordered},
    )
    assert reorder_response.status_code == 200

    delete_response = client.delete(
        f"/api/v1/watchlists/{core['id']}/items/{reordered[0]}",
    )
    assert delete_response.status_code == 204
