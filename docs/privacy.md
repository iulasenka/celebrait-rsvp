# Privacy and UK/EU data protection baseline

This document is an engineering baseline, not legal advice. Before production, the controller should confirm the lawful basis, notices, retention periods, and contracts with a UK/EU privacy professional.

## Data minimisation

Collect only invitation content and guest contact details needed to administer the event. Avoid special-category data. Store UTC timestamps and separate operational identifiers from guest PII.

## Required controls

- Define the controller and processors, lawful basis, purpose, retention schedule, and deletion workflow.
- Provide a privacy notice and guest access/correction/deletion process.
- Encrypt PII in transit and at rest; hash response management tokens.
- Redact PII, invitation content, and tokens from application logs, traces, backups, and analytics.
- Restrict inviter access to their own invitations through authenticated ownership checks.
- Add rate limiting, token expiry/revocation, CSRF protection for browser clients, secure headers, and dependency scanning.
- Maintain audit events without copying guest notes or email addresses into the audit payload.
- Implement processor agreements, international transfer safeguards, incident response, and breach notification procedures.
- Set automated retention jobs for expired invitations and deleted guest data, including backups where feasible.

The current SQLite adapter persists data across restarts. It is suitable for local development and a single-container prototype, but production deployments still need encryption at rest, backups, access controls, migrations, and a reviewed retention/deletion process.

## Current prototype limitations

The browser client is suitable for local demonstration only. It currently keeps the selected invitation ID and public invitation fields in local storage, exposes response management tokens through private edit links, and does not authenticate host requests. Before handling real personal data, add authenticated sessions, server-side authorization, encrypted persistence, hashed and revocable tokens, redacted notifications/logging, and documented retention and erasure workflows.
