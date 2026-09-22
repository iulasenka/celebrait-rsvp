from .models import GuestResponse, Invitation


class InMemoryStore:
    def __init__(self):
        self.invitations: dict[str, Invitation] = {}

    def save_invitation(self, invitation: Invitation) -> None:
        self.invitations[invitation.id] = invitation

    def list_invitations(self, owner_email: str) -> list[Invitation]:
        return [invitation for invitation in self.invitations.values() if invitation.owner_email == owner_email]

    def get_invitation(self, invitation_id: str) -> Invitation | None:
        return self.invitations.get(invitation_id)

    def save_response(self, response: GuestResponse) -> None:
        invitation = self.invitations[response.invitation_id]
        invitation.responses[response.id] = response

    def get_response_by_token(self, invitation_id: str, manage_token: str) -> GuestResponse | None:
        invitation = self.invitations.get(invitation_id)
        if invitation is None:
            return None
        return next((response for response in invitation.responses.values() if response.manage_token == manage_token), None)
