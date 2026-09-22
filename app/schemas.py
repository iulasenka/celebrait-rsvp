from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from .models import RSVPStatus


class InvitationCreate(BaseModel):
    owner_email: EmailStr
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=5000)
    starts_at: datetime
    rsvp_deadline: datetime
    expires_at: datetime

    @model_validator(mode="after")
    def validate_dates(self):
        if self.rsvp_deadline >= self.expires_at:
            raise ValueError("rsvp_deadline must be before expires_at")
        if self.starts_at >= self.expires_at:
            raise ValueError("starts_at must be before expires_at")
        return self


class InvitationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=5000)
    starts_at: datetime | None = None
    rsvp_deadline: datetime | None = None
    expires_at: datetime | None = None
    notify_guests: bool = False


class InvitationView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    starts_at: datetime
    rsvp_deadline: datetime
    expires_at: datetime
    created_at: datetime
    updated_at: datetime


class RSVPCreate(BaseModel):
    guest_name: str = Field(min_length=1, max_length=160)
    guest_email: EmailStr
    status: RSVPStatus
    note: str | None = Field(default=None, max_length=1000)


class RSVPView(RSVPCreate):
    id: str
    invitation_id: str
    created_at: datetime
    updated_at: datetime
    manage_token: str


class InvitationUpdateResult(BaseModel):
    invitation: InvitationView
    guest_notification_queued: bool
