# Study Tracker

A simple study tracker for the Engineering Design 2 AI software assignment.

## Current status

Phase 1: a Flask application with a basic home page. Authentication and study
session management will be added in later phases using Supabase.

## Local setup

Requires Python 3.10 or newer.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app app run
```

Open http://127.0.0.1:5000 in your browser. Press Ctrl+C to stop the server.

No credentials are needed for Phase 1. Keep future credentials in `.env`, which
is excluded from Git.

## Development plan

See [the MVP development plan](study_tracker_codex_plan.md).
