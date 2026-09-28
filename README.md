# Study Tracker

Study Tracker is a web application where authenticated students can record and
manage their study sessions. Each session includes a subject, study time, date,
and optional notes. Users can only see and modify their own sessions.

## Deployed application

**[Open Study Tracker](https://study-tracker-a8v9.onrender.com)**

The app is deployed on Render and uses Supabase for authentication and database
storage. The deployment uses HTTPS, Gunicorn, and a generated production secret.

## Demo video

**YouTube demo:** (https://youtu.be/v5m8SEJEeOg)

## Features

- Account registration and email confirmation
- Login and logout
- Protected student dashboard
- Add, view, edit, and delete study sessions
- User-specific data protected by Supabase Row Level Security
- Responsive dark interface for desktop and mobile screens

## Technologies

- Python 3.10+
- Flask
- Supabase Auth
- Supabase PostgreSQL
- HTML, Jinja templates, and CSS
- Gunicorn
- Render deployment

## Local setup

```sh
git clone https://github.com/MadMenDew/study-tracker.git
cd study-tracker
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Add these values to `.env`:

```text
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_publishable_or_anon_key
FLASK_SECRET_KEY=a-long-random-secret
FLASK_COOKIE_SECURE=0
```

Run [schema.sql](schema.sql) once in the Supabase SQL Editor, then start Flask:

```sh
python -m flask --app app run
```

Open <http://127.0.0.1:5000>. Never commit `.env`, a `service_role` key, or any
other secret. Verify the database connection with:

```sh
python -m flask --app app check-supabase
```

Run the automated tests with:

```sh
python -m unittest discover -s tests -v
```

## Deployment

The repository includes [render.yaml](render.yaml), which defines the Render
service. Its build command is `pip install -r requirements.txt`, and its start
command runs Gunicorn. Provide the Supabase URL and publishable key as hosted
environment variables. Keep deploys to a minimum while developing so the free
hosting limits are not exceeded; deploy after the project is ready for review.
If deployment fails, check the Render logs, ask an AI coding tool for help, or
contact the course TAs.

After deployment, set Supabase Authentication → URL Configuration → Site URL to
the hosted login URL and test registration, login, database CRUD, logout, and
user-data isolation on the deployed URL.

