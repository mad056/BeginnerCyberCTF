"""Seed demo data: test users and teams for local development."""
import requests
import sys

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
TOKEN = sys.argv[2] if len(sys.argv) > 2 else "ctfd_admin_token"

HEADERS = {
    "Authorization": f"Token {TOKEN}",
    "Content-Type": "application/json",
}


def api(method, path, json=None):
    r = requests.request(method, f"{BASE_URL}{path}", headers=HEADERS, json=json)
    r.raise_for_status()
    return r.json()


def main():
    # Create teams
    teams = ["Alpha", "Bravo", "Charlie"]
    team_ids = {}
    for name in teams:
        resp = api("POST", "/api/v1/teams", {"name": name, "password": "team123"})
        team_ids[name] = resp["data"]["id"]
        print(f"  Team: {name} (id={team_ids[name]})")

    # Create test users
    users = [
        ("Alice", "Alpha"),
        ("Bob", "Alpha"),
        ("Charlie", "Bravo"),
        ("Diana", "Charlie"),
    ]
    for uname, tname in users:
        resp = api(
            "POST",
            "/api/v1/users",
            {
                "name": uname,
                "email": f"{uname.lower()}@test.local",
                "password": "test1234",
                "type": "user",
                "verified": True,
                "team_id": team_ids[tname],
            },
        )
        print(f"  User: {uname} → {tname} (id={resp['data']['id']})")

    print("✅ Demo data seeded.")


if __name__ == "__main__":
    main()
