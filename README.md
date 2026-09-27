# Study Tracker

A simple study tracker for the Engineering Design 2 AI software assignment.

## Current status

Phases 1 and 2 are complete. The Flask home page works, the `study-tracker`
Supabase project is configured, and `schema.sql` has been applied. The live
Flask-to-Supabase connection check passed on September 25, 2026.
Phases 3 and 4 are complete, including live verification reported by the user.
Phase 5 edit/delete was verified by the user. Phase 6 styling is complete, with
a responsive dark theme, pink accents, clear forms, and session cards. All 33
tests pass. Deployment is next.

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

The user verified adding sessions, refresh persistence, and isolation between
two accounts.
Automated tests cover these application behaviors with a mocked backend; they
do not substitute for the live two-account database check.

## Edit and delete (Phase 5)

Use **Edit** beside a session to change its fields, then **Save changes** or
**Cancel**. Open **Delete** and choose **Confirm delete** to permanently remove
that session. Both operations require login, CSRF protection, and a matching
user ID on the lookup and mutation; Supabase row-level security also applies.
No database migration is required.

Live check: edit a session and refresh, delete a disposable session and refresh,
and verify a second account cannot open or modify the first account's session
using its ID. The user verified the live edit/delete flow; automated tests cover the routes,
validation, ownership filters, missing records, and backend failures.

## Local tests

```sh
python -m unittest discover -s tests -v
```

These tests use a mocked Supabase client. Run the live check above separately
after changing project settings or setting up another Supabase project.

## Deployment (Phase 7)

Deployment preparation is complete; the Render service and live verification
are pending. [render.yaml](render.yaml) configures a free Python web service,
Gunicorn, a generated session secret, and HTTPS-only session cookies.

1. Push the code to GitHub and create a Render Blueprint from this repository.
2. Provide `SUPABASE_URL` and the publishable `SUPABASE_KEY` when prompted.
   Keep `.env` local; do not upload it. Render generates its own `FLASK_SECRET_KEY`.
3. Once deployed, set Supabase Authentication → URL Configuration → Site URL
   to `https://YOUR-SERVICE.onrender.com/login`.
4. Test registration, email confirmation, login, all CRUD actions, logout, and
   isolation between two accounts on the hosted URL.

For manual service creation, use `pip install -r requirements.txt` to build and
`gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 60 app:app` to start.
Set `FLASK_COOKIE_SECURE=1`, a random `FLASK_SECRET_KEY`, and the Supabase settings.
See [Render's Flask deployment guide](https://render.com/docs/deploy-flask).

## Development plan

See [the MVP development plan](study_tracker_codex_plan.md).
