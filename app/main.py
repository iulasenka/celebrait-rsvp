from pathlib import Path
import os

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import EmailStr, TypeAdapter, ValidationError

from .schemas import InvitationCreate, InvitationUpdate, InvitationUpdateResult, InvitationView, RSVPCreate, RSVPView
from .service import DomainError, InvitationService
from .sqlite_store import SQLiteStore

app = FastAPI(title="Celebrait RSVP API", version="0.1.0", description="Headless, privacy-conscious invitations and RSVPs.")
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")
database_path = os.getenv("RSVP_DATABASE_PATH", "data/celebrait.db")
store = SQLiteStore(database_path)
service = InvitationService(store)
bearer_scheme = HTTPBearer(auto_error=False)
email_adapter = TypeAdapter(EmailStr)


def get_service() -> InvitationService:
    return service


def handle_domain_error(error: DomainError) -> HTTPException:
    code = status.HTTP_404_NOT_FOUND if "not found" in str(error) else status.HTTP_409_CONFLICT
    return HTTPException(code, detail=str(error))


def get_current_user_email(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> str:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Authorization header is required")
    try:
        return str(email_adapter.validate_python(credentials.credentials))
    except ValidationError as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer identity") from error


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def web_app():
    return FileResponse(static_dir / "index.html")


@app.post("/v1/invitations", response_model=InvitationView, status_code=status.HTTP_201_CREATED)
def create_invitation(data: InvitationCreate, invitations: InvitationService = Depends(get_service)):
    return invitations.create_invitation(data)


@app.get("/v1/invitations", response_model=list[InvitationView])
def list_invitations(
    current_user_email: str = Depends(get_current_user_email),
    invitations: InvitationService = Depends(get_service),
):
    return invitations.list_invitations(current_user_email)


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


@app.get("/v1/invitations/{invitation_id}/responses", response_model=list[RSVPView])
def list_responses(invitation_id: str, invitations: InvitationService = Depends(get_service)):
    try:
        return invitations.list_responses(invitation_id)
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
