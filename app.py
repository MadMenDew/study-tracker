import os
import re
import secrets
from datetime import date, timedelta
from functools import wraps
from pathlib import Path

import click
from dotenv import load_dotenv
from flask import Flask, g, render_template, request, session, redirect, url_for, flash, abort
from supabase import create_client
from supabase.client import ClientOptions
from supabase_auth.errors import AuthApiError

load_dotenv(Path(__file__).with_name(".env"))

app = Flask(__name__)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_COOKIE_SECURE") == "1",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
    MAX_CONTENT_LENGTH=16 * 1024,
    SECRET_KEY=os.environ.get("FLASK_SECRET_KEY"),
    SUPABASE_URL=os.environ.get("SUPABASE_URL", ""),
    SUPABASE_KEY=os.environ.get("SUPABASE_KEY", ""),
)


def get_supabase():
    """Keep each request's Auth state isolated from other visitors."""
    if "supabase" not in g:
        url = app.config["SUPABASE_URL"].strip()
        key = app.config["SUPABASE_KEY"].strip()
        if not url or not key:
            raise click.ClickException(
                "Set SUPABASE_URL and SUPABASE_KEY in .env before connecting."
            )
        try:
            g.supabase = create_client(
                url, key,
                options=ClientOptions(
                    persist_session=False, auto_refresh_token=False,
                    postgrest_client_timeout=10,
                ),
            )
        except Exception:
            raise click.ClickException(
                "Could not initialize Supabase. Check SUPABASE_URL and SUPABASE_KEY."
            ) from None
    return g.supabase


@app.cli.command("check-supabase")
def check_supabase():
    """Verify API access and the study_sessions schema without changing data."""
    client = get_supabase()
    try:
        client.table("study_sessions").select(
            "id,user_id,subject,minutes,study_date,notes,created_at"
        ).limit(0).execute()
    except Exception:
        # Avoid printing remote error details that could contain credentials.
        raise click.ClickException(
            "Supabase check failed. Check the project URL/key, network access, "
            "and that schema.sql has been run in Supabase."
        ) from None
    click.echo("Supabase connection succeeded; study_sessions is accessible.")


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def protect_forms():
    if request.method == "POST":
        expected = session.get("csrf_token", "")
        if not expected or not secrets.compare_digest(expected, request.form.get("csrf_token", "")):
            abort(400, "This form expired. Reload the page and try again.")


@app.after_request
def private_pages(response):
    if request.endpoint != "static":
        response.headers["Cache-Control"] = "no-store"
    return response


def login_required(view):
    @wraps(view)
    def protected(*args, **kwargs):
        token = session.get("access_token")
        if not token:
            return redirect(url_for("login"))
        try:
            client = get_supabase()
            user = client.auth.get_user(token).user
            if not user:
                raise ValueError("Missing user")
            g.user = user
            # Study-session queries use the verified user's JWT for RLS.
            client.postgrest.auth(token)
        except Exception:
            session.clear()
            flash("Your session expired or could not be verified. Please log in again.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return protected


def credentials():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return None
    if not password or len(password) > 128:
        return None
    return {"email": email, "password": password}


def start_session(auth_session):
    session.clear()
    session.permanent = True
    session["access_token"] = auth_session.access_token


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        values = credentials()
        if not values or len(values["password"]) < 8:
            flash("Enter a valid email and a password between 8 and 128 characters.")
            return render_template("register.html"), 400
        try:
            result = get_supabase().auth.sign_up(values)
        except Exception:
            flash("Registration could not be completed. Try again later, or log in if you already have an account.")
            return render_template("register.html"), 400
        if result.session:
            start_session(result.session)
            return redirect(url_for("index"))
        flash("Check your email to confirm your account, then return here to log in.")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        values = credentials()
        if not values:
            flash("Enter a valid email and password.")
            return render_template("login.html"), 400
        try:
            result = get_supabase().auth.sign_in_with_password(values)
            if not result.session:
                raise ValueError("Missing session")
        except AuthApiError as error:
            messages = {
                "email_not_confirmed": "Confirm your email before logging in. Open the confirmation email from Supabase (check spam too), click its link, then return here.",
                "invalid_credentials": "The email or password is incorrect. Please try again.",
                "over_request_rate_limit": "Too many login attempts. Please wait a few minutes and try again.",
            }
            flash(messages.get(error.code, "Unable to log in right now. Please try again later."))
            return render_template("login.html"), 400
        except Exception:
            flash("The authentication service could not be reached. Please try again shortly.")
            return render_template("login.html"), 400
        start_session(result.session)
        return redirect(url_for("index"))
    return render_template("login.html")


@app.post("/logout")
def logout():
    token = session.get("access_token")
    session.clear()
    if token:
        try:
            # This endpoint uses the user's JWT, not a service-role key.
            get_supabase().auth.admin.sign_out(token, scope="local")
        except Exception:
            flash("Signed out on this browser. The server could not revoke the remote session.")
    return redirect(url_for("login"))


@app.get("/")
@login_required
def index():
    return dashboard()


def dashboard(status=200):
    try:
        records = (get_supabase().table("study_sessions")
                   .select("id,subject,minutes,study_date,notes")
                   .eq("user_id", g.user.id)
                   .order("study_date", desc=True)
                   .order("created_at", desc=True).execute().data)
    except Exception:
        records = None
        flash("Your study sessions could not be loaded. Please refresh to try again.")
        status = 503
    return render_template("index.html", records=records, today=date.today().isoformat()), status


def study_session_values():
    subject = request.form.get("subject", "").strip()
    minutes_text = request.form.get("minutes", "").strip()
    study_date = request.form.get("study_date", "").strip()
    notes = request.form.get("notes", "").strip()
    errors = []
    if not subject or len(subject) > 120:
        errors.append("Enter a subject between 1 and 120 characters.")
    if not re.fullmatch(r"[0-9]{1,4}", minutes_text) or not 1 <= int(minutes_text) <= 1440:
        errors.append("Minutes must be a whole number between 1 and 1440.")
    try:
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", study_date):
            raise ValueError
        date.fromisoformat(study_date)
    except ValueError:
        errors.append("Enter a valid study date.")
    if len(notes) > 5000:
        errors.append("Keep notes to 5000 characters or fewer.")
    return {
        "subject": subject,
        "minutes": int(minutes_text) if not errors else None,
        "study_date": study_date,
        "notes": notes or None,
    }, errors


@app.post("/add")
@login_required
def add():
    values, errors = study_session_values()
    if errors:
        for error in errors:
            flash(error)
        return dashboard(400)
    try:
        get_supabase().table("study_sessions").insert({
            **values, "user_id": g.user.id,
        }).execute()
    except Exception:
        flash("We could not confirm that your session was saved. Check your list before trying again.")
        return dashboard(503)
    flash("Study session added.")
    return redirect(url_for("index"))


def owned_session(session_id):
    try:
        records = (get_supabase().table("study_sessions")
                   .select("id,subject,minutes,study_date,notes")
                   .eq("id", str(session_id)).eq("user_id", g.user.id)
                   .execute().data)
    except Exception:
        abort(503, "The session could not be loaded. Please try again.")
    if not records:
        abort(404, "Study session not found.")
    return records[0]


@app.route("/edit/<uuid:session_id>", methods=["GET", "POST"])
@login_required
def edit(session_id):
    record = owned_session(session_id)
    if request.method == "GET":
        return render_template("edit.html", record=record)
    values, errors = study_session_values()
    if errors:
        for error in errors:
            flash(error)
        return render_template("edit.html", record=record), 400
    try:
        result = (get_supabase().table("study_sessions").update(values)
                  .eq("id", str(session_id)).eq("user_id", g.user.id)
                  .execute())
    except Exception:
        flash("We could not confirm your changes were saved. Check your dashboard before trying again.")
        return render_template("edit.html", record=record), 503
    if not result.data:
        abort(404, "Study session not found.")
    flash("Study session updated.")
    return redirect(url_for("index"))


@app.post("/delete/<uuid:session_id>")
@login_required
def delete(session_id):
    owned_session(session_id)
    try:
        result = (get_supabase().table("study_sessions").delete()
                  .eq("id", str(session_id)).eq("user_id", g.user.id)
                  .execute())
    except Exception:
        flash("We could not confirm the deletion. Check your list before trying again.")
        return dashboard(503)
    if not result.data:
        abort(404, "Study session not found.")
    flash("Study session deleted.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run()
