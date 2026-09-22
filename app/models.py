from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class RSVPStatus(StrEnum):
    attending = "attending"
    not_attending = "not_attending"
    maybe = "maybe"


@dataclass
class GuestResponse:
    id: str
    invitation_id: str
    guest_name: str
    guest_email: str
    status: RSVPStatus
    note: str | None
    manage_token: str
    created_at: datetime
    updated_at: datetime


@dataclass
class Invitation:
    id: str
    owner_email: str
    title: str
    description: str
    starts_at: datetime
    rsvp_deadline: datetime
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
    responses: dict[str, GuestResponse] = field(default_factory=dict)

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at

    def accepts_rsvp(self, now: datetime) -> bool:
        return now < self.rsvp_deadline and not self.is_expired(now)
