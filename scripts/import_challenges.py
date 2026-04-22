#!/usr/bin/env python3
"""
Import all challenges from challenges/ into a running CTFd instance.

Usage:
    python import_challenges.py http://localhost:8000 YOUR_ADMIN_TOKEN
    python import_challenges.py http://localhost:8000 YOUR_ADMIN_TOKEN --update-existing
    python import_challenges.py http://localhost:8000 YOUR_ADMIN_TOKEN --update-existing --sync-files
"""
import argparse
import os
import sys
import yaml
import requests

def parse_args():
    parser = argparse.ArgumentParser(
        description="Import challenges from challenges/ into a running CTFd instance.")
    parser.add_argument(
        "ctfd_url",
        nargs="?",
        default="http://localhost:8000",
        help="Base URL for CTFd (default: http://localhost:8000)",
    )
    parser.add_argument(
        "admin_token",
        nargs="?",
        help="Admin API token from CTFd",
    )
    parser.add_argument(
        "--update-existing",
        action="store_true",
        help="Update existing challenges (name/category/description/value/type/state, flags, hints) instead of skipping",
    )
    parser.add_argument(
        "--sync-files",
        action="store_true",
        help="When used with --update-existing, replace challenge file attachments to match challenge.yml",
    )
    return parser.parse_args()


ARGS = parse_args()
BASE_URL = ARGS.ctfd_url.rstrip("/")
TOKEN = ARGS.admin_token or ""
UPDATE_EXISTING = ARGS.update_existing
SYNC_FILES = ARGS.sync_files

if not TOKEN:
    print("Usage: python import_challenges.py <ctfd_url> <admin_token> [--update-existing] [--sync-files]")
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


def api_patch(path, json=None):
    r = requests.patch(f"{BASE_URL}{path}", headers=HEADERS, json=json)
    r.raise_for_status()
    return r.json()


def api_delete(path):
    r = requests.delete(f"{BASE_URL}{path}", headers=HEADERS)
    r.raise_for_status()
    if r.text:
        return r.json()
    return {"success": True}


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


def upload_declared_files(challenge_id, challenge_dir, rel_paths):
    uploaded = 0
    for rel_path in rel_paths or []:
        abs_path = os.path.join(challenge_dir, rel_path)
        if os.path.exists(abs_path):
            upload_file(challenge_id, abs_path)
            uploaded += 1
        else:
            print(f"\n    WARNING: File not found: {rel_path}")
    return uploaded


def list_challenge_files(challenge_id):
    """
    Return file records that actually belong to this challenge.

    CTFd's GET /api/v1/files?challenge_id=X does not reliably filter by
    challenge, and uploaded files often have challenge=None in the response
    even when they are correctly linked.  Instead we use the challenge detail
    endpoint (which correctly lists owned file URLs) to discover which files
    belong to this challenge, then resolve each URL to a file record via the
    full file list.
    """
    try:
        detail = api_get(f"/api/v1/challenges/{challenge_id}")
        file_urls = detail.get("data", {}).get("files") or []
    except requests.HTTPError as e:
        print(f"\n    WARNING: Could not fetch challenge detail for {challenge_id}: {e}")
        return []

    if not file_urls:
        return []

    # Extract location (hash/filename) from each URL, stripping /files/ prefix
    # and any ?token=... query string.
    locations = set()
    for url in file_urls:
        path = url.split("?")[0]          # /files/<hash>/<filename>
        location = "/".join(path.split("/")[2:])  # <hash>/<filename>
        if location:
            locations.add(location)

    if not locations:
        return []

    # Fetch all file records and match by location.
    try:
        all_files_resp = api_get("/api/v1/files")
        all_files = all_files_resp.get("data") or []
    except requests.HTTPError as e:
        print(f"\n    WARNING: Could not list all files: {e}")
        return []

    return [f for f in all_files if f.get("location") in locations]


def replace_challenge_files(challenge_id, challenge_dir, rel_paths):
    existing_files = list_challenge_files(challenge_id)
    deleted = 0
    for item in existing_files:
        file_id = item.get("id")
        if file_id is None:
            continue
        api_delete(f"/api/v1/files/{file_id}")
        deleted += 1

    uploaded = upload_declared_files(challenge_id, challenge_dir, rel_paths)
    return deleted, uploaded


def replace_flags(challenge_id, flags):
    existing = api_get(f"/api/v1/flags?challenge_id={challenge_id}")
    for item in existing.get("data") or []:
        api_delete(f"/api/v1/flags/{item['id']}")

    for flag in flags or []:
        api_post("/api/v1/flags", json={
            "challenge": challenge_id,
            "content": flag,
            "type": "static",
            "data": "",
        })


def replace_hints(challenge_id, hints):
    existing = api_get(f"/api/v1/hints?challenge_id={challenge_id}")
    for item in existing.get("data") or []:
        api_delete(f"/api/v1/hints/{item['id']}")

    for hint in hints or []:
        api_post("/api/v1/hints", json={
            "challenge": challenge_id,
            "content": hint.get("content", ""),
            "cost": hint.get("cost", 0),
        })


def import_challenge(challenge_dir):
    yml_path = os.path.join(challenge_dir, "challenge.yml")
    with open(yml_path, encoding="utf-8") as f:
        ch = yaml.safe_load(f)

    name = ch["name"]
    print(f"  Importing: {name} ...", end=" ", flush=True)

    # Check if already exists
    existing = api_get("/api/v1/challenges?view=admin")
    existing_challenge = None
    for existing_ch in existing.get("data") or []:
        if existing_ch["name"] == name:
            existing_challenge = existing_ch
            break

    payload = {
        "name": name,
        "category": ch.get("category", "Misc"),
        "description": ch.get("description", ""),
        "value": ch.get("value", 100),
        "type": ch.get("type", "standard"),
        "state": ch.get("state", "visible"),
    }

    if existing_challenge is None:
        # Create challenge
        resp = api_post("/api/v1/challenges", json=payload)
        ch_id = resp["data"]["id"]

        replace_flags(ch_id, ch.get("flags"))
        replace_hints(ch_id, ch.get("hints"))

        # Upload asset files listed in challenge.yml
        upload_declared_files(ch_id, challenge_dir, ch.get("files"))

        print(f"done (created id={ch_id})")
        return

    if not UPDATE_EXISTING:
        print("already exists, skipping.")
        return

    ch_id = existing_challenge["id"]
    api_patch(f"/api/v1/challenges/{ch_id}", json=payload)
    replace_flags(ch_id, ch.get("flags"))
    replace_hints(ch_id, ch.get("hints"))

    if SYNC_FILES:
        deleted, uploaded = replace_challenge_files(ch_id, challenge_dir, ch.get("files"))
        print(f"done (updated, files synced: removed {deleted}, uploaded {uploaded})")
    elif ch.get("files"):
        print("done (updated, files unchanged; use --sync-files to repair/replace attachments)")
    else:
        print("done (updated)")


def main():
    if SYNC_FILES and not UPDATE_EXISTING:
        print("NOTE: --sync-files only applies when --update-existing is set.")

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

    if UPDATE_EXISTING and SYNC_FILES:
        mode = "create + update existing + sync files"
    elif UPDATE_EXISTING:
        mode = "create + update existing"
    else:
        mode = "create only"
    print(f"Found {len(dirs)} challenges to import into {BASE_URL} ({mode})\n")
    for d in dirs:
        import_challenge(os.path.join(CHALLENGES_DIR, d))

    print("\nDone. Refresh the CTFd admin panel to verify.")


if __name__ == "__main__":
    main()
