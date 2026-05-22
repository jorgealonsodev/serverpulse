# Deployment Guide

**Deploy ServerPulse on a fresh Ubuntu 24.04 VPS. Estimated time: 30–45 minutes.**

## Prerequisites

- Ubuntu 24.04 LTS VPS (minimum 1 GB RAM, 10 GB disk)
- Domain name pointing to the VPS IP (for TLS certificates)
- SSH access as root

## Step 1: Create a Non-Root User

```bash
adduser deploy
usermod -aG sudo deploy
```

## Step 2: Harden SSH

Edit `/etc/ssh/sshd_config`:

```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

Restart SSH:

```bash
systemctl restart sshd
```

Add your SSH public key to `/home/deploy/.ssh/authorized_keys`:

```bash
mkdir -p /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
echo "ssh-ed25519 AAAA... your-key" > /home/deploy/.ssh/authorized_keys
chmod 600 /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh
```

Test the connection from your local machine before closing the root session:

```bash
ssh deploy@your-vps-ip
```

## Step 3: Configure Firewall (UFW)

```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
ufw status
```

## Step 4: Install fail2ban

```bash
sudo apt update
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

Create `/etc/fail2ban/jail.local`:

```ini
[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
```

```bash
sudo systemctl restart fail2ban
sudo fail2ban-client status sshd
```

## Step 5: Install Docker Engine + Compose

```bash
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo usermod -aG docker deploy
```

Verify:

```bash
docker --version
docker compose version
```

Log out and back in for the group membership to take effect.

## Step 6: Clone and Configure

```bash
git clone https://github.com/jorgealonsodev/serverpulse.git /opt/serverpulse
cd /opt/serverpulse
cp .env.example .env
```

Edit `.env` with production values:

```bash
# Generate a strong JWT secret (at least 32 bytes)
openssl rand -base64 48

# Edit .env
nano .env
```

Set at minimum:
- `JWT_SECRET` — output from `openssl rand -base64 48`
- `POSTGRES_PASSWORD` — strong database password
- `CORS_ORIGINS` — your domain (e.g., `https://monitor.example.com`)

## Step 7: TLS with Certbot

```bash
sudo apt install -y certbot
sudo certbot certonly --standalone -d monitor.example.com
```

Update Nginx configuration to use the certificates, or place a reverse proxy (e.g., Caddy, Traefik) in front of port 80. For a quick setup, you can use Nginx on the host:

```bash
sudo apt install -y nginx
sudo cp /opt/serverpulse/nginx/nginx.conf /etc/nginx/sites-available/serverpulse
# Edit the config to add SSL directives pointing to /etc/letsencrypt/live/monitor.example.com/
sudo ln -s /etc/nginx/sites-available/serverpulse /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Set up automatic renewal:

```bash
sudo systemctl enable certbot.timer
```

## Step 8: Start the Stack

```bash
cd /opt/serverpulse
docker compose up -d
docker compose ps
docker compose logs -f
```

Verify health:

```bash
curl http://localhost/health
```

Expected response: `{"status":"ok","db":"ok","redis":"ok"}`

## Step 9: Set Up Database Backups

Create a backup script at `/opt/serverpulse/scripts/backup_db.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="/opt/serverpulse/backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/serverpulse_${TIMESTAMP}.sql.gz"

docker compose exec -T postgres pg_dump -U "${POSTGRES_USER:-serverpulse}" "${POSTGRES_DB:-serverpulse}" \
  | gzip > "$BACKUP_FILE"

# Keep only the last 7 days of backups
find "$BACKUP_DIR" -name "serverpulse_*.sql.gz" -mtime +7 -delete

echo "Backup complete: $BACKUP_FILE"
```

Make it executable:

```bash
chmod +x /opt/serverpulse/scripts/backup_db.sh
```

Add a cron job:

```bash
crontab -e
```

Add this line:

```cron
0 3 * * * /opt/serverpulse/scripts/backup_db.sh >> /var/log/serverpulse-backup.log 2>&1
```

## CI/CD Secrets

For GitHub Actions deploy workflow, configure the secrets listed in [docs/secrets.md](secrets.md):

| Secret | Description |
|--------|-------------|
| `GHCR_TOKEN` | GitHub PAT with `write:packages` |
| `DEPLOY_HOST` | VPS hostname or IP |
| `DEPLOY_USER` | SSH user (`deploy`) |
| `DEPLOY_KEY` | SSH private key |

## Post-Deployment Checklist

- [ ] `/health` returns `{"status":"ok","db":"ok","redis":"ok"}`
- [ ] `/metrics` returns Prometheus-format data
- [ ] User registration works
- [ ] Server creation generates an API token
- [ ] Agent can ingest metrics (`curl -H "X-Agent-Token: ..." -X POST ...`)
- [ ] WebSocket connects with valid JWT
- [ ] TLS certificate is valid and auto-renews
- [ ] Backup cron runs and creates `.sql.gz` files
- [ ] fail2ban is active (`sudo fail2ban-client status`)
