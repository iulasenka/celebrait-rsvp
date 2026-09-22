from datetime import datetime, timezone
from secrets import token_urlsafe
from uuid import uuid4

from .models import GuestResponse, Invitation
from .schemas import InvitationCreate, InvitationUpdate, RSVPCreate
from .store import RSVPStore


class DomainError(Exception):
    pass


class InvitationService:
    def __init__(self, store: RSVPStore):
        self.store = store

    def create_invitation(self, data: InvitationCreate, now: datetime | None = None) -> Invitation:
        now = now or datetime.now(timezone.utc)
        invitation = Invitation(
            id=str(uuid4()), owner_email=str(data.owner_email), title=data.title,
            description=data.description, starts_at=data.starts_at,
            rsvp_deadline=data.rsvp_deadline, expires_at=data.expires_at,
            created_at=now, updated_at=now,
        )
        self.store.save_invitation(invitation)
        return invitation

    def update_invitation(self, invitation_id: str, data: InvitationUpdate, now: datetime | None = None) -> tuple[Invitation, bool]:
        invitation = self._get(invitation_id)
        values = data.model_dump(exclude_unset=True, exclude={"notify_guests"})
        candidate = {**invitation.__dict__, **values}
        if candidate["rsvp_deadline"] >= candidate["expires_at"]:
            raise DomainError("rsvp_deadline must be before expires_at")
        if candidate["starts_at"] >= candidate["expires_at"]:
            raise DomainError("starts_at must be before expires_at")
        for key, value in values.items():
            setattr(invitation, key, value)
        invitation.updated_at = now or datetime.now(timezone.utc)
        self.store.save_invitation(invitation)
        return invitation, data.notify_guests

    def create_response(self, invitation_id: str, data: RSVPCreate, now: datetime | None = None) -> GuestResponse:
        invitation = self._get(invitation_id)
        now = now or datetime.now(timezone.utc)
        if not invitation.accepts_rsvp(now):
            raise DomainError("this invitation is no longer accepting RSVPs")
        response = GuestResponse(
            id=str(uuid4()), invitation_id=invitation_id, guest_name=data.guest_name,
            guest_email=str(data.guest_email), status=data.status, note=data.note,
            manage_token=token_urlsafe(32), created_at=now, updated_at=now,
        )
        self.store.save_response(response)
        return response

    def update_response(self, invitation_id: str, manage_token: str, data: RSVPCreate, now: datetime | None = None) -> GuestResponse:
        invitation = self._get(invitation_id)
        response = self.store.get_response_by_token(invitation_id, manage_token)
        if response is None:
            raise DomainError("response not found")
        now = now or datetime.now(timezone.utc)
        if not invitation.accepts_rsvp(now):
            raise DomainError("this invitation is no longer accepting RSVP changes")
        response.guest_name = data.guest_name
        response.guest_email = str(data.guest_email)
        response.status = data.status
        response.note = data.note
        response.updated_at = now
        self.store.save_response(response)
        return response

    def _get(self, invitation_id: str) -> Invitation:
        invitation = self.store.get_invitation(invitation_id)
        if invitation is None:
            raise DomainError("invitation not found")
        return invitation
