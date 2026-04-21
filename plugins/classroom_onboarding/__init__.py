import os
import secrets
import string

from flask import Blueprint, make_response, redirect, render_template, request, send_from_directory
from CTFd.cache import clear_standings
from CTFd.models import Teams, Users, db
from CTFd.utils.security.auth import login_user

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

EVENT_PASSWORD = os.environ.get("EVENT_PASSWORD", "cyber2026")


def _random_password(length: int = 32) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def load(app):
    """CTFd plugin entry point."""
    plugin_bp = Blueprint(
        "classroom_onboarding",
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    @plugin_bp.route("/join", methods=["GET"])
    def join_get():
        return render_template("join.html", error=None)

    @plugin_bp.route("/challenges/<path:filename>")
    def challenge_files(filename):
        """Serve static challenge pages at a predictable URL."""
        return send_from_directory(os.path.join(STATIC_DIR, "challenges"), filename)

    @plugin_bp.route("/challenges/11/")
    def challenge_11():
        """Network Tab challenge - flag is in the X-Flag response header."""
        html = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Acme Corp Portal</title>
<style>
body{font-family:sans-serif;background:#0f172a;color:#e2e8f0;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;}
.box{background:#1e293b;padding:3rem;border-radius:12px;text-align:center;max-width:500px;}
h1{color:#38bdf8;margin-bottom:1rem;}
p{color:#94a3b8;line-height:1.6;}
</style>
</head>
<body>
<div class="box">
  <h1>Acme Corp Portal</h1>
  <p>Welcome! Everything is running normally.</p>
  <p>Nothing to see here.</p>
</div>
</body>
</html>"""
        resp = make_response(html, 200)
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
        resp.headers["X-Flag"] = "flag{http_headers_hide_secrets}"
        return resp


    @plugin_bp.route("/join", methods=["POST"])
    def join_post():
        event_pw = request.form.get("event_password", "")
        display_name = request.form.get("display_name", "").strip()
        team_name = request.form.get("team_name", "").strip()

        # ── validation ──────────────────────────────────────────
        if not secrets.compare_digest(event_pw, EVENT_PASSWORD):
            return render_template("join.html", error="Wrong event password.")

        if not display_name or len(display_name) > 64:
            return render_template(
                "join.html", error="Please enter a display name (max 64 chars)."
            )

        if not team_name or len(team_name) > 64:
            return render_template(
                "join.html", error="Please enter a team name (max 64 chars)."
            )

        if Users.query.filter_by(name=display_name).first():
            return render_template(
                "join.html", error="That name is already taken. Pick another."
            )

        # ── get or create team ──────────────────────────────────
        team = Teams.query.filter_by(name=team_name).first()
        if team is None:
            team = Teams(
                name=team_name,
                password=_random_password(),
                hidden=False,
                banned=False,
            )
            db.session.add(team)
            db.session.flush()  # get team.id before user insert

        # ── create user ─────────────────────────────────────────
        fake_email = (
            f"{display_name.lower().replace(' ', '_')}"
            f"_{secrets.token_hex(4)}@ctf.local"
        )
        user = Users(
            name=display_name,
            email=fake_email,
            password=_random_password(),
            type="user",
            verified=True,
            hidden=False,
            banned=False,
            team_id=team.id,
        )
        db.session.add(user)
        db.session.commit()

        login_user(user)
        clear_standings()

        return redirect("/challenges")

    app.register_blueprint(plugin_bp)
