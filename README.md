# Study Tracker

A simple study tracker for the Engineering Design 2 AI software assignment.

## Current status

Phases 1 and 2 are complete. The Flask home page works, the `study-tracker`
Supabase project is configured, and `schema.sql` has been applied. The live
Flask-to-Supabase connection check passed on September 25, 2026.
Phase 3 authentication and Phase 4 create/read study sessions are implemented.
All 26 automated tests pass. Live registration and login have succeeded; live
logout, session persistence, and two-account isolation checks remain pending.
Edit and delete actions come in Phase 5.

## Local setup

Requires Python 3.10 or newer.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app app run
```

Open http://127.0.0.1:5000 in your browser. Press Ctrl+C to stop the server.

Configure `.env` using the setup below before using authentication. Keep
credentials in `.env`, which is excluded from Git. The dashboard requires login.

## Supabase setup (Phase 2)

1. Create a project in the [Supabase dashboard](https://supabase.com/dashboard).
2. Open its SQL Editor and run [schema.sql](schema.sql) once in the new project.
   This creates `study_sessions`, validation constraints, and row-level security
   policies limiting authenticated users to their own records.
3. Copy the environment template:

   ```sh
   cp .env.example .env
   ```

4. Set `SUPABASE_URL` to the project URL and `SUPABASE_KEY` to its publishable
   key (or legacy `anon` key). Do not use a secret or `service_role` key, which
   bypasses row-level security. Generate a separate `FLASK_SECRET_KEY` with
   `python -c 'import secrets; print(secrets.token_hex(32))'` and place it in `.env`.
5. Verify the connection:

   ```sh
   python -m flask --app app check-supabase
   ```

   Expected: `Supabase connection succeeded; study_sessions is accessible.`
   This read-only check verifies the API and expected columns without fetching
   study data. It does not test authentication or prove the access policies;
   those require separate users when authentication is implemented in Phase 3.
   If it fails, check the settings, project availability, and schema installation.

Client initialization follows the [Supabase Python documentation](https://supabase.com/docs/reference/python/initializing).
The schema uses [Supabase row-level security](https://supabase.com/docs/guides/database/postgres/row-level-security).

## Authentication (Phase 3)

- Open `/register` to create an account with an email and a password of at least
  8 characters. If Supabase requires email confirmation, confirm the email and
  return to `/login`. Existing accounts can use `/login` directly.
- In Supabase Authentication → URL Configuration, set Site URL to
  `http://127.0.0.1:5000/login` for local development (configured for this project).
  Use the deployed HTTPS login URL when deploying.
- The dashboard validates the access token with Supabase on every visit. The
  signed, HttpOnly, SameSite cookie stores only the access token, not passwords
  or refresh tokens. Login is required again when the token or one-hour cookie
  expires. Set `FLASK_COOKIE_SECURE=1` when deploying over HTTPS.
- Logout is a CSRF-protected POST. It clears the browser session and asks
  Supabase to revoke that login's remote session. Supabase access tokens remain
  valid until their expiry, so keep cookies private.
- Supabase's default email service may restrict delivery or rate-limit signup.
  Configure custom SMTP before supporting public registration.

Live acceptance check: register, confirm email if needed, log in, log out,
visit `/` and verify the redirect to `/login`, then log in again.

References: [Supabase signup](https://supabase.com/docs/reference/python/auth-signup),
[password login](https://supabase.com/docs/reference/python/auth-signinwithpassword),
and [logout](https://supabase.com/docs/reference/python/auth-signout).

## Study sessions (Phase 4)

After login, use the dashboard to add a subject (1–120 characters), whole
minutes (1–1440), a valid study date, and optional notes (up to 5000 characters).
Sessions appear newest study date first. Form input is preserved if validation
or saving fails. Refreshing the dashboard reads records from Supabase.

The server assigns the verified user's ID to inserts and filters reads by that
ID. Each query also uses the user's JWT so the existing row-level security
policies apply. No database migration is needed for this phase.

Live acceptance check: add a session, refresh to verify persistence, then sign
in with a second account and verify the first account's sessions are hidden.
Automated tests cover these application behaviors with a mocked backend; they
do not substitute for the live two-account database check.

## Local tests

```sh
python -m unittest discover -s tests -v
```

These tests use a mocked Supabase client. Run the live check above separately
after changing project settings or setting up another Supabase project.

## Development plan

See [the MVP development plan](study_tracker_codex_plan.md).
