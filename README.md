# BeginnerCyberCTF

A beginner-friendly Capture The Flag platform built on [CTFd](https://ctfd.io/), designed for first-year  students with no technical background.

## Features

- **Shared event password** — students enter one password, pick a name, and join a team. No email/password registration.
- **10 beginner challenges** — view source, inspect element, base64, Caesar cipher, ROT13, robots.txt, image metadata, hidden spreadsheet tab, phishing email analysis, QR/OSINT.
- **Live scoreboard** — cumulative score over time, solves per challenge, first blood markers.
- **One-command deploy** — Docker Compose with CTFd, MariaDB, and Redis.

## Quick Start (Local)

```bash
cd infra
cp .env.example .env        # edit EVENT_PASSWORD and TEAM_NAMES
docker compose up -d
```

Open `http://localhost:8000`, complete the admin setup wizard, then:
1. Set theme to `ctf-theme` in Admin → Config → Theme
2. Disable public registration in Admin → Config → Accounts
3. Enable Team Mode in Admin → Config → Settings
4. Import challenges: `bash scripts/import_challenges.sh http://localhost:8000 YOUR_TOKEN`

Students go to `http://localhost:8000/join` to enter.

## Project Structure

```
infra/                  Docker Compose + env config
plugins/
  classroom_onboarding/ Custom /join page (event password + name + team)
  classroom_dashboard/  Leaderboard history API + challenge stats
theme/ctf-theme/        Branded Jinja2 theme
challenges/01-10/       Challenge definitions (ctfcli format) + assets
scripts/                Import, seed, and asset generation scripts
deploy/digitalocean/    Production deploy scripts + README
```

## Deploy to DigitalOcean

See [deploy/digitalocean/README.md](deploy/digitalocean/README.md).

## License

MIT
