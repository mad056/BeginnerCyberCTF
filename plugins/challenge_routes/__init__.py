import os

from flask import Blueprint, make_response, send_from_directory

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


def load(app):
    """CTFd plugin entry point for serving static challenge pages."""
    bp = Blueprint(
        "challenge_routes",
        __name__,
        static_folder="static",
    )

    @bp.route("/challenges/<path:filename>")
    def challenge_files(filename):
        return send_from_directory(os.path.join(STATIC_DIR, "challenges"), filename)

    @bp.route("/challenges/11/")
    def challenge_11():
        html = """<!DOCTYPE html>
<html lang=\"en\">
<head><meta charset=\"UTF-8\"><title>Acme Corp Portal</title>
<style>
body{font-family:sans-serif;background:#0f172a;color:#e2e8f0;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;}
.box{background:#1e293b;padding:3rem;border-radius:12px;text-align:center;max-width:500px;}
h1{color:#38bdf8;margin-bottom:1rem;}
p{color:#94a3b8;line-height:1.6;}
</style>
</head>
<body>
<div class=\"box\">
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

    app.register_blueprint(bp)
