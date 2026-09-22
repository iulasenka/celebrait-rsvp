from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app import main
from app.memory_store import InMemoryStore
from app.service import InvitationService


client = TestClient(main.app)


def test_invitation_list_uses_bearer_identity():
    service = InvitationService(InMemoryStore())
    main.app.dependency_overrides[main.get_service] = lambda: service
    try:
        payload = {
            "owner_email": "owner@example.com",
            "title": "Owner event",
            "description": "",
            "starts_at": "2026-10-01T18:00:00Z",
            "rsvp_deadline": "2026-09-30T18:00:00Z",
            "expires_at": "2026-10-02T18:00:00Z",
        }
        other_payload = {**payload, "owner_email": "other@example.com", "title": "Other event"}
        assert client.post("/v1/invitations", json=payload).status_code == 201
        assert client.post("/v1/invitations", json=other_payload).status_code == 201

        response = client.get("/v1/invitations", headers={"Authorization": "Bearer owner@example.com"})

        assert response.status_code == 200
        assert [item["title"] for item in response.json()] == ["Owner event"]
        assert client.get("/v1/invitations").status_code == 401
    finally:
        main.app.dependency_overrides.clear()
