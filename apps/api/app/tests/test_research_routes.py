from fastapi.testclient import TestClient


def test_notes_crud_search_and_delete(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/research/notes",
        json={
            "symbol": "AAPL",
            "title": "New research note",
            "content": "Track services attach and margin trend.",
            "note_type": "thesis",
            "theme": "quality",
        },
    )
    assert create_response.status_code == 201
    note_id = create_response.json()["id"]

    search_response = client.get("/api/v1/research/notes", params={"q": "services"})
    assert search_response.status_code == 200
    assert any(item["id"] == note_id for item in search_response.json())

    update_response = client.patch(
        f"/api/v1/research/notes/{note_id}",
        json={"content": "Updated thesis: monitor buyback cadence."},
    )
    assert update_response.status_code == 200
    assert "buyback" in update_response.json()["content"]

    delete_response = client.delete(f"/api/v1/research/notes/{note_id}")
    assert delete_response.status_code == 204


def test_thesis_crud(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/research/theses",
        json={
            "symbol": "MSFT",
            "title": "MSFT thesis",
            "status": "active",
            "summary": "Cloud margin durability thesis.",
        },
    )
    assert create_response.status_code == 201
    thesis_id = create_response.json()["id"]

    list_response = client.get("/api/v1/research/theses", params={"symbol": "MSFT"})
    assert list_response.status_code == 200
    assert any(item["id"] == thesis_id for item in list_response.json())

    update_response = client.patch(
        f"/api/v1/research/theses/{thesis_id}",
        json={"status": "watch"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "watch"

    delete_response = client.delete(f"/api/v1/research/theses/{thesis_id}")
    assert delete_response.status_code == 204


def test_note_synthesis_routes(client: TestClient) -> None:
    response = client.get("/api/v1/research/synthesis", params={"symbol": "AAPL"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["scope_symbol"] == "AAPL"
    assert payload["note_count"] >= 1
    assert payload["synthesized_thesis"]
    assert payload["open_questions"]

    ai_alias = client.get("/api/v1/ai/note-synthesis", params={"theme": "quality"})
    assert ai_alias.status_code == 200
    assert ai_alias.json()["scope_theme"] == "quality"


def test_ai_research_qa_with_citations(client: TestClient) -> None:
    response = client.get(
        "/api/v1/ai/research-qa",
        params={"question": "What are the main risks in AAPL?", "symbol": "AAPL"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "AAPL"
    assert payload["answer"]
    assert payload["coverage_count"] >= 1
    assert payload["citations"]
    assert payload["source_model"].startswith("hybrid-")
    assert "semantic_score" in payload["citations"][0]
