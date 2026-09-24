from pathlib import Path
import os

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .auth import get_current_user
from .schemas import InvitationCreate, InvitationUpdate, InvitationUpdateResult, InvitationView, RSVPCreate, RSVPView
from .service import DomainError, InvitationService
from .sqlite_store import SQLiteStore

app = FastAPI(title="Celebrait RSVP API", version="0.1.0", description="Headless, privacy-conscious invitations and RSVPs.")
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")
database_path = os.getenv("RSVP_DATABASE_PATH", "data/celebrait.db")
store = SQLiteStore(database_path)
service = InvitationService(store)


def get_service() -> InvitationService:
    return service


def handle_domain_error(error: DomainError) -> HTTPException:
    error_msg = str(error).lower()
    if "not found" in error_msg:
        code = status.HTTP_404_NOT_FOUND
    elif "forbidden" in error_msg:
        code = status.HTTP_403_FORBIDDEN
    else:
        code = status.HTTP_409_CONFLICT
    return HTTPException(code, detail=str(error))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def web_app():
    return FileResponse(static_dir / "index.html")


@app.post("/v1/invitations", response_model=InvitationView, status_code=status.HTTP_201_CREATED)
def create_invitation(
    data: InvitationCreate,
    current_user: str = Depends(get_current_user),
    invitations: InvitationService = Depends(get_service)
):
    return invitations.create_invitation(current_user, data)


@app.get("/v1/invitations", response_model=list[InvitationView])
def list_invitations(
    current_user: str = Depends(get_current_user),
    invitations: InvitationService = Depends(get_service),
):
    return invitations.list_invitations(current_user)


@app.get("/v1/invitations/{invitation_id}", response_model=InvitationView)
def get_invitation(invitation_id: str, invitations: InvitationService = Depends(get_service)):
    try:
        return invitations.get_invitation_for_guest(invitation_id)
    except DomainError as error:
        raise handle_domain_error(error) from error


@app.patch("/v1/invitations/{invitation_id}", response_model=InvitationUpdateResult)
def update_invitation(
    invitation_id: str,
    data: InvitationUpdate,
    current_user: str = Depends(get_current_user),
    invitations: InvitationService = Depends(get_service)
):
    try:
        invitation, notification_queued = invitations.update_invitation(current_user, invitation_id, data)
        return {"invitation": invitation, "guest_notification_queued": notification_queued}
    except DomainError as error:
        raise handle_domain_error(error) from error


@app.delete("/v1/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invitation(
    invitation_id: str,
    current_user: str = Depends(get_current_user),
    invitations: InvitationService = Depends(get_service)
):
    try:
        invitations.delete_invitation(current_user, invitation_id)
    except DomainError as error:
        raise handle_domain_error(error) from error


@app.post("/v1/invitations/{invitation_id}/responses", response_model=RSVPView, status_code=status.HTTP_201_CREATED)
def create_response(invitation_id: str, data: RSVPCreate, invitations: InvitationService = Depends(get_service)):
    try:
        return invitations.create_response(invitation_id, data)
    except DomainError as error:
        raise handle_domain_error(error) from error


@app.get("/v1/invitations/{invitation_id}/responses", response_model=list[RSVPView])
def list_responses(
    invitation_id: str,
    current_user: str = Depends(get_current_user),
    invitations: InvitationService = Depends(get_service)
):
    try:
        return invitations.list_responses(current_user, invitation_id)
    except DomainError as error:
        raise handle_domain_error(error) from error


@app.get("/v1/invitations/{invitation_id}/responses/{manage_token}", response_model=RSVPView)
def get_response(invitation_id: str, manage_token: str, invitations: InvitationService = Depends(get_service)):
    try:
        return invitations.get_response(invitation_id, manage_token)
    except DomainError as error:
        raise handle_domain_error(error) from error


@app.patch("/v1/invitations/{invitation_id}/responses/{manage_token}", response_model=RSVPView)
def update_response(invitation_id: str, manage_token: str, data: RSVPCreate, invitations: InvitationService = Depends(get_service)):
    try:
        return invitations.update_response(invitation_id, manage_token, data)
    except DomainError as error:
        raise handle_domain_error(error) from error
