#!/usr/bin/env python3
"""
Import all challenges from challenges/ into a running CTFd instance.

Usage:
    python import_challenges.py http://localhost:8000 YOUR_ADMIN_TOKEN
"""
import os
import sys
import yaml
import requests

BASE_URL = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
TOKEN = sys.argv[2] if len(sys.argv) > 2 else ""

if not TOKEN:
    print("Usage: python import_challenges.py <ctfd_url> <admin_token>")
    print("Get a token from Admin -> Config -> Access Tokens in CTFd.")
    sys.exit(1)

HEADERS = {"Authorization": f"Token {TOKEN}", "Content-Type": "application/json"}
CHALLENGES_DIR = os.path.join(os.path.dirname(__file__), "..", "challenges")


def api_get(path):
    r = requests.get(f"{BASE_URL}{path}", headers=HEADERS)
    r.raise_for_status()
    return r.json()


def api_post(path, json=None, files=None, data=None):
    h = {"Authorization": f"Token {TOKEN}"}
    if files is None and data is None:
        h["Content-Type"] = "application/json"
    r = requests.post(f"{BASE_URL}{path}", headers=h, json=json, files=files, data=data)
    r.raise_for_status()
    return r.json()


def upload_file(challenge_id, file_path):
    with open(file_path, "rb") as f:
        fname = os.path.basename(file_path)
        resp = requests.post(
            f"{BASE_URL}/api/v1/files",
            headers={"Authorization": f"Token {TOKEN}"},
            data={"challenge": challenge_id, "type": "challenge"},
            files={"file": (fname, f)},
        )
    resp.raise_for_status()
    return resp.json()


def import_challenge(challenge_dir):
    yml_path = os.path.join(challenge_dir, "challenge.yml")
    with open(yml_path, encoding="utf-8") as f:
        ch = yaml.safe_load(f)

    name = ch["name"]
    print(f"  Importing: {name} ...", end=" ", flush=True)

    # Check if already exists
    existing = api_get("/api/v1/challenges?view=admin")
    for existing_ch in existing.get("data") or []:
        if existing_ch["name"] == name:
            print("already exists, skipping.")
            return

    # Create challenge
    payload = {
        "name": name,
        "category": ch.get("category", "Misc"),
        "description": ch.get("description", ""),
        "value": ch.get("value", 100),
        "type": ch.get("type", "standard"),
        "state": ch.get("state", "visible"),
    }
    resp = api_post("/api/v1/challenges", json=payload)
    ch_id = resp["data"]["id"]

    # Add flags
    for flag in ch.get("flags") or []:
        api_post("/api/v1/flags", json={
            "challenge": ch_id,
            "content": flag,
            "type": "static",
            "data": "",
        })

    # Add hints
    for hint in ch.get("hints") or []:
        api_post("/api/v1/hints", json={
            "challenge": ch_id,
            "content": hint.get("content", ""),
            "cost": hint.get("cost", 0),
        })

    # Upload asset files listed in challenge.yml
    for rel_path in ch.get("files") or []:
        abs_path = os.path.join(challenge_dir, rel_path)
        if os.path.exists(abs_path):
            upload_file(ch_id, abs_path)
        else:
            print(f"\n    WARNING: File not found: {rel_path}")

    print(f"done (id={ch_id})")


def main():
    try:
        api_get("/api/v1/challenges?view=admin")
    except Exception as e:
        print(f"Cannot reach CTFd at {BASE_URL}: {e}")
        print("Make sure CTFd is running and the token is valid.")
        sys.exit(1)

    dirs = sorted(
        d for d in os.listdir(CHALLENGES_DIR)
        if os.path.isdir(os.path.join(CHALLENGES_DIR, d))
        and os.path.exists(os.path.join(CHALLENGES_DIR, d, "challenge.yml"))
    )

    print(f"Found {len(dirs)} challenges to import into {BASE_URL}\n")
    for d in dirs:
        import_challenge(os.path.join(CHALLENGES_DIR, d))

    print("\nDone. Refresh the CTFd admin panel to verify.")


if __name__ == "__main__":
    main()
