from datetime import datetime, timezone

import pytest

from app.memory_store import InMemoryStore
from app.schemas import InvitationCreate, InvitationUpdate, RSVPCreate
from app.service import DomainError, InvitationService
from app.sqlite_store import SQLiteStore


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def invitation(service: InvitationService, user_id: str = "user-123"):
    return service.create_invitation(
        user_id,
        InvitationCreate(
            owner_email="owner@example.com",
            title="Launch party",
            starts_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
            rsvp_deadline=datetime(2026, 1, 20, tzinfo=timezone.utc),
            expires_at=datetime(2026, 2, 2, tzinfo=timezone.utc),
        ),
        now=NOW,
    )


def test_update_returns_explicit_notification_intent():
    service = InvitationService(InMemoryStore())
    item = invitation(service)

    updated, queued = service.update_invitation("user-123", item.id, InvitationUpdate(title="Quiet update"), now=NOW)
    assert updated.title == "Quiet update"
    assert queued is False

    _, queued = service.update_invitation("user-123", item.id, InvitationUpdate(description="Venue changed", notify_guests=True), now=NOW)
    assert queued is True


def test_list_invitations_filters_by_user():
    service = InvitationService(InMemoryStore())
    first = invitation(service, "user-123")
    second = service.create_invitation(
        "user-456",
        InvitationCreate(
            owner_email="other@example.com",
            title="Other event",
            starts_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
            rsvp_deadline=datetime(2026, 2, 20, tzinfo=timezone.utc),
            expires_at=datetime(2026, 3, 2, tzinfo=timezone.utc),
        ),
        now=NOW,
    )

    results = service.list_invitations("user-123")

    assert [item.id for item in results] == [first.id]
    assert second.id not in [item.id for item in results]


def test_rsvp_deadline_stops_new_responses():
    service = InvitationService(InMemoryStore())
    item = invitation(service)
    data = RSVPCreate(guest_name="Ada", guest_email="ada@example.com", status="attending")

    with pytest.raises(DomainError, match="no longer accepting"):
        service.create_response(item.id, data, now=datetime(2026, 1, 20, tzinfo=timezone.utc))


def test_guest_can_edit_response_with_opaque_token():
    service = InvitationService(InMemoryStore())
    item = invitation(service)
    response = service.create_response(
        item.id,
        RSVPCreate(guest_name="Ada", guest_email="ada@example.com", status="maybe"),
        now=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    updated = service.update_response(
        item.id,
        response.manage_token,
        RSVPCreate(guest_name="Ada Lovelace", guest_email="ada@example.com", status="attending"),
        now=datetime(2026, 1, 3, tzinfo=timezone.utc),
    )
    assert updated.status == "attending"
    assert updated.guest_name == "Ada Lovelace"

    with pytest.raises(DomainError, match="response not found"):
        service.update_response(item.id, "wrong-token", updated, now=datetime(2026, 1, 3, tzinfo=timezone.utc))


def test_response_can_be_restored_from_private_edit_token():
    service = InvitationService(InMemoryStore())
    item = invitation(service)
    response = service.create_response(
        item.id,
        RSVPCreate(guest_name="Ada", guest_email="ada@example.com", status="attending"),
        now=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    restored = service.get_response(item.id, response.manage_token)
    assert restored.id == response.id
    assert restored.guest_email == "ada@example.com"


def test_rsvp_still_works_after_store_is_recreated(tmp_path):
    database_path = str(tmp_path / "celebrait.db")
    creator = InvitationService(SQLiteStore(database_path))
    item = invitation(creator)

    restarted_service = InvitationService(SQLiteStore(database_path))
    response = restarted_service.create_response(
        item.id,
        RSVPCreate(guest_name="Ada", guest_email="ada@example.com", status="attending"),
        now=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    assert response.invitation_id == item.id
    assert restarted_service.list_responses("user-123", item.id)[0].id == response.id


def test_user_can_only_manage_own_invitations():
    service = InvitationService(InMemoryStore())
    item = invitation(service, "user-123")

    with pytest.raises(DomainError, match="forbidden"):
        service.update_invitation("user-456", item.id, InvitationUpdate(title="Hacked"), now=NOW)

    with pytest.raises(DomainError, match="forbidden"):
        service.delete_invitation("user-456", item.id, now=NOW)

    with pytest.raises(DomainError, match="forbidden"):
        service.list_responses("user-456", item.id)


def test_deleted_invitations_are_filtered_from_list():
    service = InvitationService(InMemoryStore())
    first = invitation(service, "user-123")
    second = service.create_invitation(
        "user-123",
        InvitationCreate(
            owner_email="owner@example.com",
            title="Second event",
            starts_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
            rsvp_deadline=datetime(2026, 2, 20, tzinfo=timezone.utc),
            expires_at=datetime(2026, 3, 2, tzinfo=timezone.utc),
        ),
        now=NOW,
    )

    service.delete_invitation("user-123", first.id, now=NOW)
    results = service.list_invitations("user-123")

    assert [item.id for item in results] == [second.id]
    assert first.id not in [item.id for item in results]


def test_deleted_invitations_return_404():
    service = InvitationService(InMemoryStore())
    item = invitation(service, "user-123")

    service.delete_invitation("user-123", item.id, now=NOW)

    with pytest.raises(DomainError, match="not found"):
        service.get_invitation_for_guest(item.id)

    with pytest.raises(DomainError, match="not found"):
        service.update_invitation("user-123", item.id, InvitationUpdate(title="Update"), now=NOW)

    with pytest.raises(DomainError, match="not found"):
        service.create_response(
            item.id,
            RSVPCreate(guest_name="Ada", guest_email="ada@example.com", status="attending"),
            now=NOW,
        )
