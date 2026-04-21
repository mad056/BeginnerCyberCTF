# Deploying BeginnerCyberCTF to DigitalOcean

## Prerequisites
- A DigitalOcean account
- An SSH key added to your account

## Steps

### 1. Create a Droplet
- Image: **Ubuntu 22.04 LTS**
- Size: **Basic $6/mo** (1 vCPU, 1 GB RAM) — sufficient for ~50 students
- Region: closest to your class
- Add your SSH key

### 2. Provision the server
```bash
ssh root@YOUR_DROPLET_IP
curl -sSL https://raw.githubusercontent.com/YOUR_ORG/BeginnerCyberCTF/main/deploy/digitalocean/provision.sh | bash
```

### 3. Setup the application
```bash
su - deploy
bash <(curl -sSL https://raw.githubusercontent.com/YOUR_ORG/BeginnerCyberCTF/main/deploy/digitalocean/setup.sh)
```

Or clone manually:
```bash
su - deploy
git clone https://github.com/YOUR_ORG/BeginnerCyberCTF.git ~/ctf
cd ~/ctf/deploy/digitalocean
bash setup.sh
```

### 4. Configure
```bash
nano ~/ctf/infra/.env
# Set EVENT_PASSWORD, TEAM_NAMES, then restart:
cd ~/ctf/infra && docker compose restart
```

### 5. Admin setup
1. Open `http://YOUR_DROPLET_IP:8000` in your browser
2. Complete the CTFd setup wizard (set admin user/pass)
3. Go to **Admin → Config → Theme** → set to `ctf-theme`
4. Go to **Admin → Config → Accounts** → disable public registration
5. Go to **Admin → Config → Settings** → set Team Mode

### 6. Import challenges
```bash
cd ~/ctf/scripts
bash import_challenges.sh http://localhost:8000 YOUR_ADMIN_ACCESS_TOKEN
```

### 7. (Optional) Add HTTPS with Caddy
For production, put a reverse proxy in front. Add to `docker-compose.yml`:
```yaml
  caddy:
    image: caddy:2-alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy-data:/data
```

Create `infra/Caddyfile`:
```
yourdomain.com {
    reverse_proxy ctfd:8000
}
```

## Teardown
```bash
cd ~/ctf/infra && docker compose down -v
```
