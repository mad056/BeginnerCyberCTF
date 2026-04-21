from flask import Blueprint, jsonify
from CTFd.models import Awards, Solves, Teams, Challenges, db
from CTFd.utils.decorators import authed_only
from sqlalchemy import func


def load(app):
    """CTFd plugin entry point – classroom dashboard API."""
    bp = Blueprint(
        "classroom_dashboard",
        __name__,
    )

    @bp.route("/api/v1/classroom/leaderboard-history")
    @authed_only
    def leaderboard_history():
        """Return cumulative score time series per team, sorted by solve time."""
        solves = (
            db.session.query(
                Solves.team_id,
                Teams.name.label("team_name"),
                Solves.challenge_id,
                Challenges.value.label("points"),
                Solves.date,
            )
            .join(Teams, Teams.id == Solves.team_id)
            .join(Challenges, Challenges.id == Solves.challenge_id)
            .filter(Teams.hidden == False, Teams.banned == False)
            .order_by(Solves.date)
            .all()
        )

        # Build per-team cumulative series
        teams_data: dict[int, dict] = {}
        for s in solves:
            entry = teams_data.setdefault(
                s.team_id,
                {"team_id": s.team_id, "team_name": s.team_name, "scores": []},
            )
            prev = entry["scores"][-1]["cumulative"] if entry["scores"] else 0
            entry["scores"].append(
                {
                    "timestamp": s.date.isoformat(),
                    "challenge_id": s.challenge_id,
                    "points": s.points,
                    "cumulative": prev + s.points,
                }
            )

        return jsonify(list(teams_data.values()))

    @bp.route("/api/v1/classroom/challenge-stats")
    @authed_only
    def challenge_stats():
        """Return solve count per challenge and first blood info."""
        challenges = Challenges.query.filter_by(state="visible").all()
        result = []
        for ch in challenges:
            first_solve = (
                Solves.query.filter_by(challenge_id=ch.id)
                .order_by(Solves.date)
                .first()
            )
            solve_count = Solves.query.filter_by(challenge_id=ch.id).count()
            result.append(
                {
                    "id": ch.id,
                    "name": ch.name,
                    "value": ch.value,
                    "solves": solve_count,
                    "first_blood": {
                        "team": first_solve.team.name,
                        "date": first_solve.date.isoformat(),
                    }
                    if first_solve and first_solve.team
                    else None,
                }
            )
        return jsonify(result)

    app.register_blueprint(bp)
