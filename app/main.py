from fastapi import Depends, FastAPI, HTTPException, status

from .memory_store import InMemoryStore
from .schemas import InvitationCreate, InvitationUpdate, InvitationUpdateResult, InvitationView, RSVPCreate, RSVPView
from .service import DomainError, InvitationService

app = FastAPI(title="Celebrait RSVP API", version="0.1.0", description="Headless, privacy-conscious invitations and RSVPs.")
store = InMemoryStore()
service = InvitationService(store)


def get_service() -> InvitationService:
    return service


def handle_domain_error(error: DomainError) -> HTTPException:
    code = status.HTTP_404_NOT_FOUND if "not found" in str(error) else status.HTTP_409_CONFLICT
    return HTTPException(code, detail=str(error))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/invitations", response_model=InvitationView, status_code=status.HTTP_201_CREATED)
def create_invitation(data: InvitationCreate, invitations: InvitationService = Depends(get_service)):
    return invitations.create_invitation(data)


@app.get("/v1/invitations/{invitation_id}", response_model=InvitationView)
def get_invitation(invitation_id: str, invitations: InvitationService = Depends(get_service)):
    try:
        return invitations._get(invitation_id)
    except DomainError as error:
        raise handle_domain_error(error) from error


@app.patch("/v1/invitations/{invitation_id}", response_model=InvitationUpdateResult)
def update_invitation(invitation_id: str, data: InvitationUpdate, invitations: InvitationService = Depends(get_service)):
    try:
        invitation, notification_queued = invitations.update_invitation(invitation_id, data)
        return {"invitation": invitation, "guest_notification_queued": notification_queued}
    except DomainError as error:
        raise handle_domain_error(error) from error


@app.post("/v1/invitations/{invitation_id}/responses", response_model=RSVPView, status_code=status.HTTP_201_CREATED)
def create_response(invitation_id: str, data: RSVPCreate, invitations: InvitationService = Depends(get_service)):
    try:
        return invitations.create_response(invitation_id, data)
    except DomainError as error:
        raise handle_domain_error(error) from error


@app.patch("/v1/invitations/{invitation_id}/responses/{manage_token}", response_model=RSVPView)
def update_response(invitation_id: str, manage_token: str, data: RSVPCreate, invitations: InvitationService = Depends(get_service)):
    try:
        return invitations.update_response(invitation_id, manage_token, data)
    except DomainError as error:
        raise handle_domain_error(error) from error
