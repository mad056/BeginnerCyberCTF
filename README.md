# BeginnerCyberCTF

A beginner-friendly Capture The Flag platform built on [CTFd](https://ctfd.io/), designed for first-year  students with no technical background.

## Features

- **12 beginner challenges** — beginner-friendly web, crypto, forensics, email, and OSINT tasks including view source, hidden content, encoding, ciphers, metadata, phishing analysis, and network inspection.
- **Challenge web pages** — custom challenge pages are available at `/challenges/*` through a dedicated routes plugin.
- **One-command deploy** — Docker Compose with CTFd, MariaDB, and Redis.

## Quick Start (Local)

```bash
cd infra
cp .env.example .env
docker compose up -d
```

Open `http://localhost:8000`, complete the admin setup wizard, then:
1. Configure accounts in Admin → Config → Accounts (registration policy and login flow)
2. Enable Team Mode in Admin → Config → Settings
3. Generate challenge assets: `python3 scripts/generate_assets.py`
4. Import challenges: `python3 scripts/import_challenges.py http://localhost:8000 YOUR_TOKEN`
5. If any challenge attachment under `/files/...` returns 404, repair and resync files:
  `python3 scripts/import_challenges.py http://localhost:8000 YOUR_TOKEN --update-existing --sync-files`

## Project Structure

```
infra/                  Docker Compose + env config
plugins/
  challenge_routes/     Serves /challenges/* static pages and challenge 11 header route
challenges/01-12/       Challenge definitions (ctfcli format) + assets
scripts/                Import, seed, and asset generation scripts
deploy/digitalocean/    Production deploy scripts + README
```

## Deploy to DigitalOcean

See [deploy/digitalocean/README.md](deploy/digitalocean/README.md).

## License

MIT
