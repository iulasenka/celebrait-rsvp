# Architecture

## Shape

Celebrait RSVP is a headless HTTP API. A separate web, mobile, or email client can consume the generated OpenAPI contract at `/docs` and `/openapi.json`.

The repository also includes a lightweight browser client served from `/`. It has no frontend build pipeline: `app/static/index.html` defines the views, `app/static/app.js` handles hash-based navigation and API calls, and `app/static/styles.css` provides the responsive visual system.

- `app/schemas.py` defines the public API contract and validates date relationships.
- `app/service.py` owns invitation lifecycle and RSVP business rules.
- `app/store.py` is the persistence boundary.
- `app/sqlite_store.py` is the running persistence adapter. It stores invitations and responses in SQLite and can be pointed at a container volume with `RSVP_DATABASE_PATH`. A production deployment may replace it with PostgreSQL while keeping the `RSVPStore` boundary.

## Browser views

The client separates the main workflows into view panels:

1. **Dashboard** lists the host's locally remembered invitation and exposes the next actions.
2. **Create** submits a new invitation with event, RSVP deadline, and expiry dates.
3. **Manage** edits invitation details and sends `notify_guests` explicitly.
4. **Preview** renders the guest-facing invitation before the host shares its ID.
5. **RSVPs** calls `GET /v1/invitations/{id}/responses` and displays response counts and guest rows.
6. **Guest reply** calls `POST` for a new response. The application returns a private edit link; opening it calls `GET` with the link credential to restore the response and `PATCH` to save changes. The credential is never entered into the form.

The API collection endpoint `GET /v1/invitations` derives the owner email from the `Authorization: Bearer ...` header and orders invitations by event start time. In this prototype the bearer value is only validated as an email identity; production must replace this with JWT/OIDC verification and authorization.

The browser stores only the current invitation object in local storage for the development experience. It is not an account system and must not be treated as host authorization. The server database is the source of truth for invitation links, so links continue to work across API reloads and process restarts.

## Lifecycle rules

- An invitation accepts new and edited responses only while `now < rsvp_deadline` and `now < expires_at`.
- `expires_at` is also the point at which the invitation should be hidden from guest clients.
- Invitation updates return explicit `guest_notification_queued` intent. An email/outbox adapter should enqueue notifications only when `notify_guests=true`.
- Guests edit responses using an unguessable management token. Tokens should be stored hashed in production and only shown once to the guest client.
- The current response list endpoint is intentionally simple and has no owner authentication; production access control must be added before exposing guest PII to an inviter.

## Production persistence

Use a relational schema with UUID/opaque IDs, UTC timestamps, and an outbox table:

- `invitations(id, owner_user_id, title, description, starts_at, rsvp_deadline, expires_at, created_at, updated_at)`
- `responses(id, invitation_id, guest_name, guest_email_encrypted, status, note_encrypted, manage_token_hash, created_at, updated_at)`
- `notification_outbox(id, invitation_id, event_type, payload, created_at, delivered_at)`

Apply migrations, foreign keys, indexes on `(invitation_id)` and `rsvp_deadline`, and database encryption at rest. Do not log request bodies or management tokens.
