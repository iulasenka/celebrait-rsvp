# Celebrait RSVP

A lightweight, headless invitation and RSVP API.

## Run locally

Requires Python 3.12+.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
uvicorn app.main:app --reload
```

OpenAPI documentation is available at `http://localhost:8000/docs`.

## Test

```bash
pytest
```

## Run in a container

```bash
docker compose up --build
```

The current API uses an in-memory development store. See [docs/architecture.md](docs/architecture.md) for the production persistence boundary and [docs/privacy.md](docs/privacy.md) for the UK/EU data-protection baseline.

## API shape

- `POST /v1/invitations` creates an invitation.
- `GET /v1/invitations/{id}` returns the guest-safe invitation.
- `PATCH /v1/invitations/{id}` modifies an invitation and accepts `notify_guests`.
- `POST /v1/invitations/{id}/responses` records an RSVP.
- `PATCH /v1/invitations/{id}/responses/{manage_token}` edits a guest response.