from datetime import datetime, timezone

import pytest

from app.memory_store import InMemoryStore
from app.schemas import InvitationCreate, InvitationUpdate, RSVPCreate
from app.service import DomainError, InvitationService


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def invitation(service: InvitationService):
    return service.create_invitation(
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

    updated, queued = service.update_invitation(item.id, InvitationUpdate(title="Quiet update"), now=NOW)
    assert updated.title == "Quiet update"
    assert queued is False

    _, queued = service.update_invitation(item.id, InvitationUpdate(description="Venue changed", notify_guests=True), now=NOW)
    assert queued is True


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
