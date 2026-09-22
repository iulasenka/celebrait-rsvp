# Celebrait RSVP

A lightweight invitation and RSVP application with a headless API and a small browser client.

## Run locally

Requires Python 3.12+.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
uvicorn app.main:app --reload
```

OpenAPI documentation is available at `http://localhost:8000/docs`.
The browser application is available at `http://localhost:8000/`.

## Browser application

The client is a static, dependency-free interface served by FastAPI. It uses hash navigation so each workflow is isolated without requiring a frontend build step:

- **My invitations**: see the current invitation and open host actions.
- **New invitation**: create an event with RSVP and expiry dates.
- **Invitation editor**: change event details and choose whether guests are notified.
- **Invitation preview**: see the guest-facing invitation before sharing it.
- **RSVPs**: view response counts and individual guest replies.
- **Guest reply**: open the invitation link, submit a response, and use the private edit link returned after submission to change it later.

After creating an invitation, its ID is stored in the browser for the local development session. The current API has no authentication, so this should be replaced with authenticated owner access before production.

## Test

```bash
pytest
```

## Run in a container

```bash
docker compose up --build
```

The API uses SQLite by default at `data/celebrait.db`, configurable with `RSVP_DATABASE_PATH`. See [docs/architecture.md](docs/architecture.md) for the persistence boundary and [docs/privacy.md](docs/privacy.md) for the UK/EU data-protection baseline.

## API shape

- `POST /v1/invitations` creates an invitation.
- `GET /v1/invitations` lists invitations for the authenticated user.
- `GET /v1/invitations/{id}` returns the guest-safe invitation.
- `PATCH /v1/invitations/{id}` modifies an invitation and accepts `notify_guests`.
- `POST /v1/invitations/{id}/responses` records an RSVP.
- `GET /v1/invitations/{id}/responses` lists responses for the host view.
- `GET /v1/invitations/{id}/responses/{manage_token}` restores a response through its private edit link.
- `PATCH /v1/invitations/{id}/responses/{manage_token}` edits a guest response.

Guest links use the form `/?invitation={id}#guest`. After the first response, the application generates a private edit link containing the response credential; guests do not enter that credential into the form.

The current prototype expects `Authorization: Bearer owner@example.com` for the invitation collection endpoint. The bearer value is validated as an email identity only; replace it with a JWT/OIDC verifier before production.

## Project layout

- `app/main.py`: FastAPI routes and static client mounting.
- `app/service.py`: invitation and RSVP lifecycle rules.
- `app/sqlite_store.py`: persistent SQLite adapter used by the running application.
- `app/static/`: browser UI, styles, and view navigation.
- `tests/`: domain unit tests.
- `docs/`: architecture and privacy notes.