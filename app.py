import os
from pathlib import Path

import click
from dotenv import load_dotenv
from flask import Flask, g, render_template
from supabase import create_client
from supabase.client import ClientOptions

load_dotenv(Path(__file__).with_name(".env"))

app = Flask(__name__)
app.config.update(
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


@app.get("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run()
