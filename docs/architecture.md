# Architecture

## Shape

Celebrait RSVP is a headless HTTP API. A separate web, mobile, or email client can consume the generated OpenAPI contract at `/docs` and `/openapi.json`.

- `app/schemas.py` defines the public API contract and validates date relationships.
- `app/service.py` owns invitation lifecycle and RSVP business rules.
- `app/store.py` is the persistence boundary.
- `app/memory_store.py` is a development adapter. Production deployment should replace it with a transactional SQLite or PostgreSQL adapter.

## Lifecycle rules

- An invitation accepts new and edited responses only while `now < rsvp_deadline` and `now < expires_at`.
- `expires_at` is also the point at which the invitation should be hidden from guest clients.
- Invitation updates return explicit `guest_notification_queued` intent. An email/outbox adapter should enqueue notifications only when `notify_guests=true`.
- Guests edit responses using an unguessable management token. Tokens should be stored hashed in production and only shown once to the guest client.

## Production persistence

Use a relational schema with UUID/opaque IDs, UTC timestamps, and an outbox table:

- `invitations(id, owner_user_id, title, description, starts_at, rsvp_deadline, expires_at, created_at, updated_at)`
- `responses(id, invitation_id, guest_name, guest_email_encrypted, status, note_encrypted, manage_token_hash, created_at, updated_at)`
- `notification_outbox(id, invitation_id, event_type, payload, created_at, delivered_at)`

Apply migrations, foreign keys, indexes on `(invitation_id)` and `rsvp_deadline`, and database encryption at rest. Do not log request bodies or management tokens.
