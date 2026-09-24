from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app import main
from app.auth import create_jwt_token
from app.memory_store import InMemoryStore
from app.service import InvitationService


client = TestClient(main.app)


def test_invitation_list_requires_jwt_auth():
    service = InvitationService(InMemoryStore())
    main.app.dependency_overrides[main.get_service] = lambda: service
    try:
        user1_token = create_jwt_token("user-123")
        user2_token = create_jwt_token("user-456")

        payload = {
            "owner_email": "owner@example.com",
            "title": "User 1 event",
            "description": "",
            "starts_at": "2026-10-01T18:00:00Z",
            "rsvp_deadline": "2026-09-30T18:00:00Z",
            "expires_at": "2026-10-02T18:00:00Z",
        }
        other_payload = {**payload, "owner_email": "other@example.com", "title": "User 2 event"}

        assert client.post("/v1/invitations", json=payload, headers={"Authorization": f"Bearer {user1_token}"}).status_code == 201
        assert client.post("/v1/invitations", json=other_payload, headers={"Authorization": f"Bearer {user2_token}"}).status_code == 201

        response = client.get("/v1/invitations", headers={"Authorization": f"Bearer {user1_token}"})

        assert response.status_code == 200
        assert [item["title"] for item in response.json()] == ["User 1 event"]
        assert client.get("/v1/invitations").status_code == 401
    finally:
        main.app.dependency_overrides.clear()


def test_unauthenticated_guest_endpoints():
    service = InvitationService(InMemoryStore())
    main.app.dependency_overrides[main.get_service] = lambda: service
    try:
        user_token = create_jwt_token("user-123")
        payload = {
            "owner_email": "owner@example.com",
            "title": "Public event",
            "description": "",
            "starts_at": "2026-10-01T18:00:00Z",
            "rsvp_deadline": "2026-09-30T18:00:00Z",
            "expires_at": "2026-10-02T18:00:00Z",
        }

        response = client.post("/v1/invitations", json=payload, headers={"Authorization": f"Bearer {user_token}"})
        invitation_id = response.json()["id"]

        get_response = client.get(f"/v1/invitations/{invitation_id}")
        assert get_response.status_code == 200

        rsvp_payload = {
            "guest_name": "Ada",
            "guest_email": "ada@example.com",
            "status": "attending",
        }
        rsvp_response = client.post(f"/v1/invitations/{invitation_id}/responses", json=rsvp_payload)
        assert rsvp_response.status_code == 201
        manage_token = rsvp_response.json()["manage_token"]

        token_response = client.get(f"/v1/invitations/{invitation_id}/responses/{manage_token}")
        assert token_response.status_code == 200

        update_payload = {**rsvp_payload, "status": "not_attending"}
        patch_response = client.patch(f"/v1/invitations/{invitation_id}/responses/{manage_token}", json=update_payload)
        assert patch_response.status_code == 200
    finally:
        main.app.dependency_overrides.clear()


def test_authenticated_endpoints_require_auth():
    service = InvitationService(InMemoryStore())
    main.app.dependency_overrides[main.get_service] = lambda: service
    try:
        payload = {
            "owner_email": "owner@example.com",
            "title": "Event",
            "description": "",
            "starts_at": "2026-10-01T18:00:00Z",
            "rsvp_deadline": "2026-09-30T18:00:00Z",
            "expires_at": "2026-10-02T18:00:00Z",
        }

        assert client.post("/v1/invitations", json=payload).status_code == 401
        assert client.get("/v1/invitations").status_code == 401
        assert client.patch("/v1/invitations/fake-id", json={"title": "Updated"}).status_code == 401
        assert client.delete("/v1/invitations/fake-id").status_code == 401
        assert client.get("/v1/invitations/fake-id/responses").status_code == 401
    finally:
        main.app.dependency_overrides.clear()


def test_user_cannot_modify_other_user_invitation():
    service = InvitationService(InMemoryStore())
    main.app.dependency_overrides[main.get_service] = lambda: service
    try:
        user1_token = create_jwt_token("user-123")
        user2_token = create_jwt_token("user-456")

        payload = {
            "owner_email": "owner@example.com",
            "title": "User 1 event",
            "description": "",
            "starts_at": "2026-10-01T18:00:00Z",
            "rsvp_deadline": "2026-09-30T18:00:00Z",
            "expires_at": "2026-10-02T18:00:00Z",
        }

        response = client.post("/v1/invitations", json=payload, headers={"Authorization": f"Bearer {user1_token}"})
        invitation_id = response.json()["id"]

        patch_response = client.patch(
            f"/v1/invitations/{invitation_id}",
            json={"title": "Hacked"},
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        assert patch_response.status_code == 403

        delete_response = client.delete(f"/v1/invitations/{invitation_id}", headers={"Authorization": f"Bearer {user2_token}"})
        assert delete_response.status_code == 403

        responses_response = client.get(f"/v1/invitations/{invitation_id}/responses", headers={"Authorization": f"Bearer {user2_token}"})
        assert responses_response.status_code == 403
    finally:
        main.app.dependency_overrides.clear()


def test_deleted_invitation_returns_404():
    service = InvitationService(InMemoryStore())
    main.app.dependency_overrides[main.get_service] = lambda: service
    try:
        user_token = create_jwt_token("user-123")
        payload = {
            "owner_email": "owner@example.com",
            "title": "Event to delete",
            "description": "",
            "starts_at": "2026-10-01T18:00:00Z",
            "rsvp_deadline": "2026-09-30T18:00:00Z",
            "expires_at": "2026-10-02T18:00:00Z",
        }

        response = client.post("/v1/invitations", json=payload, headers={"Authorization": f"Bearer {user_token}"})
        invitation_id = response.json()["id"]

        delete_response = client.delete(f"/v1/invitations/{invitation_id}", headers={"Authorization": f"Bearer {user_token}"})
        assert delete_response.status_code == 204

        get_response = client.get(f"/v1/invitations/{invitation_id}")
        assert get_response.status_code == 404

        list_response = client.get("/v1/invitations", headers={"Authorization": f"Bearer {user_token}"})
        assert invitation_id not in [item["id"] for item in list_response.json()]
    finally:
        main.app.dependency_overrides.clear()
