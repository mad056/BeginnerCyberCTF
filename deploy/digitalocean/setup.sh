#!/usr/bin/env bash
# Setup: clone repo, configure .env, bring up containers.
# Run as the 'deploy' user: bash setup.sh
set -euo pipefail

REPO_URL="${1:-https://github.com/YOUR_ORG/BeginnerCyberCTF.git}"
INSTALL_DIR="$HOME/ctf"

echo "=== Cloning repository ==="
git clone "$REPO_URL" "$INSTALL_DIR" 2>/dev/null || (cd "$INSTALL_DIR" && git pull)

cd "$INSTALL_DIR/infra"

echo "=== Configuring environment ==="
if [ ! -f .env ]; then
  cp .env.example .env
  # Generate a random secret key
  SECRET=$(openssl rand -hex 32)
  sed -i "s/change-me-to-a-random-string/$SECRET/" .env
  echo "  ✏️  Review .env settings before first run"
  echo "     nano $INSTALL_DIR/infra/.env"
fi

echo "=== Starting containers ==="
docker compose up -d

echo ""
echo "✅ CTFd is running on http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "Next steps:"
echo "  1. Open the URL above and complete the CTFd admin setup wizard"
echo "  2. Once you have your admin token (Admin → Settings → API Tokens), run:"
echo "       cd $INSTALL_DIR"
echo "       python3 scripts/generate_assets.py"
echo "       python3 scripts/import_challenges.py http://localhost:8000 YOUR_ADMIN_ACCESS_TOKEN"
echo "  3. If any challenge attachment under /files/... returns 404, run:"
echo "       python3 scripts/import_challenges.py http://localhost:8000 YOUR_ADMIN_ACCESS_TOKEN --update-existing --sync-files"
echo "  4. Configure account registration policy in Admin → Config → Accounts"
echo "  5. Enable Team Mode in Admin → Config → Settings"
