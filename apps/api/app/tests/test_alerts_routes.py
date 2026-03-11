from __future__ import annotations

from fastapi.testclient import TestClient


def test_alert_crud_evaluation_and_notifications(client: TestClient) -> None:
    baseline = client.get("/api/v1/alerts")
    assert baseline.status_code == 200
    baseline_count = len(baseline.json())

    created = client.post(
        "/api/v1/alerts",
        json={
            "symbol": "MSFT",
            "alert_type": "price_threshold",
            "rule": {"operator": ">=", "target": 420, "cooldown_minutes": 1, "interval_minutes": 1},
        },
    )
    assert created.status_code == 201
    created_payload = created.json()
    alert_id = created_payload["id"]
    assert created_payload["symbol"] == "MSFT"

    updated = client.patch(
        f"/api/v1/alerts/{alert_id}",
        json={"rule": {"operator": ">=", "target": 410, "cooldown_minutes": 1, "interval_minutes": 1}},
    )
    assert updated.status_code == 200
    assert updated.json()["rule"]["target"] == 410

    evaluated = client.post("/api/v1/alerts/evaluate")
    assert evaluated.status_code == 200
    assert evaluated.json()["evaluated_count"] >= 1
    assert evaluated.json()["triggered_count"] >= 1

    events = client.get("/api/v1/alerts/events")
    assert events.status_code == 200
    assert any(event["alert_id"] == alert_id for event in events.json())

    notifications = client.get("/api/v1/notifications")
    assert notifications.status_code == 200
    triggered_notification = next(
        note for note in notifications.json() if note["title"].startswith("Alert triggered:")
    )
    mark_read = client.patch(f"/api/v1/notifications/{triggered_notification['id']}/read")
    assert mark_read.status_code == 200
    assert mark_read.json()["status"] == "read"

    unread = client.get("/api/v1/notifications", params={"status": "unread"})
    assert unread.status_code == 200
    assert all(note["read_at"] is None for note in unread.json())

    deleted = client.delete(f"/api/v1/alerts/{alert_id}")
    assert deleted.status_code == 204

    final_list = client.get("/api/v1/alerts")
    assert len(final_list.json()) == baseline_count


def test_brief_generate_and_latest(client: TestClient) -> None:
    latest = client.get("/api/v1/briefs/latest")
    assert latest.status_code == 200

    generated = client.post("/api/v1/briefs/generate")
    assert generated.status_code == 201
    generated_payload = generated.json()
    assert generated_payload["headline"]
    assert generated_payload["bullets"]

    latest_after = client.get("/api/v1/briefs/latest")
    assert latest_after.status_code == 200
    assert latest_after.json()["id"] == generated_payload["id"]

    notifications = client.get("/api/v1/notifications")
    assert notifications.status_code == 200
    assert any(item["daily_brief_id"] == generated_payload["id"] for item in notifications.json())
