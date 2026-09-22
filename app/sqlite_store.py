import sqlite3
from datetime import datetime

from .models import GuestResponse, Invitation, RSVPStatus


class SQLiteStore:
    def __init__(self, database_path: str = "data/celebrait.db"):
        self.database_path = database_path
        if database_path != ":memory:":
            from pathlib import Path

            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS invitations (
                    id TEXT PRIMARY KEY,
                    owner_email TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    starts_at TEXT NOT NULL,
                    rsvp_deadline TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS responses (
                    id TEXT PRIMARY KEY,
                    invitation_id TEXT NOT NULL REFERENCES invitations(id) ON DELETE CASCADE,
                    guest_name TEXT NOT NULL,
                    guest_email TEXT NOT NULL,
                    status TEXT NOT NULL,
                    note TEXT,
                    manage_token TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS responses_invitation_id_idx ON responses(invitation_id);
                CREATE INDEX IF NOT EXISTS responses_manage_token_idx ON responses(manage_token);
                """
            )

    def save_invitation(self, invitation: Invitation) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO invitations (id, owner_email, title, description, starts_at, rsvp_deadline, expires_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET owner_email=excluded.owner_email, title=excluded.title,
                    description=excluded.description, starts_at=excluded.starts_at,
                    rsvp_deadline=excluded.rsvp_deadline, expires_at=excluded.expires_at,
                    updated_at=excluded.updated_at
                """ ,
                self._invitation_values(invitation),
            )

    def list_invitations(self, owner_email: str) -> list[Invitation]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id FROM invitations WHERE owner_email = ? ORDER BY starts_at ASC",
                (owner_email,),
            ).fetchall()
        return [invitation for row in rows if (invitation := self.get_invitation(row["id"])) is not None]

    def get_invitation(self, invitation_id: str) -> Invitation | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM invitations WHERE id = ?", (invitation_id,)).fetchone()
            if row is None:
                return None
            responses = connection.execute("SELECT * FROM responses WHERE invitation_id = ?", (invitation_id,)).fetchall()
        invitation = Invitation(
            id=row["id"], owner_email=row["owner_email"], title=row["title"], description=row["description"],
            starts_at=self._date(row["starts_at"]), rsvp_deadline=self._date(row["rsvp_deadline"]),
            expires_at=self._date(row["expires_at"]), created_at=self._date(row["created_at"]),
            updated_at=self._date(row["updated_at"]),
        )
        invitation.responses = {response["id"]: self._response(response) for response in responses}
        return invitation

    def save_response(self, response: GuestResponse) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO responses (id, invitation_id, guest_name, guest_email, status, note, manage_token, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET guest_name=excluded.guest_name, guest_email=excluded.guest_email,
                    status=excluded.status, note=excluded.note, updated_at=excluded.updated_at
                """,
                (response.id, response.invitation_id, response.guest_name, response.guest_email, response.status.value,
                 response.note, response.manage_token, response.created_at.isoformat(), response.updated_at.isoformat()),
            )

    def get_response_by_token(self, invitation_id: str, manage_token: str) -> GuestResponse | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM responses WHERE invitation_id = ? AND manage_token = ?",
                (invitation_id, manage_token),
            ).fetchone()
        return self._response(row) if row else None

    @staticmethod
    def _invitation_values(invitation: Invitation) -> tuple[str, ...]:
        return (
            invitation.id, invitation.owner_email, invitation.title, invitation.description,
            invitation.starts_at.isoformat(), invitation.rsvp_deadline.isoformat(), invitation.expires_at.isoformat(),
            invitation.created_at.isoformat(), invitation.updated_at.isoformat(),
        )

    @staticmethod
    def _date(value: str) -> datetime:
        return datetime.fromisoformat(value)

    @classmethod
    def _response(cls, row: sqlite3.Row) -> GuestResponse:
        return GuestResponse(
            id=row["id"], invitation_id=row["invitation_id"], guest_name=row["guest_name"],
            guest_email=row["guest_email"], status=RSVPStatus(row["status"]), note=row["note"],
            manage_token=row["manage_token"], created_at=cls._date(row["created_at"]), updated_at=cls._date(row["updated_at"]),
        )
