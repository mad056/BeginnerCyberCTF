#!/usr/bin/env bash
# Import all challenges into CTFd using ctfcli.
# Alternative workflow: prefer scripts/import_challenges.py for deterministic update + file repair.
# Usage: ./import_challenges.sh https://your-ctfd-url ADMIN_TOKEN
set -euo pipefail

CTFD_URL="${1:?Usage: $0 <ctfd_url> <access_token>}"
TOKEN="${2:?Usage: $0 <ctfd_url> <access_token>}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CHALLENGES_DIR="$SCRIPT_DIR/../challenges"

# Install ctfcli if not present
if ! command -v ctf &> /dev/null; then
  echo "Installing ctfcli..."
  pip install ctfcli
fi

# Initialize ctfcli config
ctf init --url "$CTFD_URL" --access-token "$TOKEN" --name "BeginnerCyberCTF" 2>/dev/null || true

# Import each challenge
for dir in "$CHALLENGES_DIR"/*/; do
  if [ -f "$dir/challenge.yml" ]; then
    echo "Importing: $(basename "$dir")"
    ctf challenge install "$dir" || echo "  ⚠ Failed: $(basename "$dir")"
  fi
done

echo "✅ All challenges imported."
