# Study Tracker

A simple study tracker for the Engineering Design 2 AI software assignment.

## Current status

Phases 1 and 2 are complete. The Flask home page works, the `study-tracker`
Supabase project is configured, and `schema.sql` has been applied. The live
Flask-to-Supabase connection check passed on September 25, 2026.
Authentication and study session management come in later phases.

## Local setup

Requires Python 3.10 or newer.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app app run
```

Open http://127.0.0.1:5000 in your browser. Press Ctrl+C to stop the server.

The home page still works without credentials. Keep credentials in `.env`, which
is excluded from Git.

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

## Local tests

```sh
python -m unittest discover -s tests -v
```

These tests use a mocked Supabase client. Run the live check above separately
after changing project settings or setting up another Supabase project.

## Development plan

See [the MVP development plan](study_tracker_codex_plan.md).
