# DigitalOcean Droplet Deployment Guide

> Full end-to-end guide for deploying A.T.L.A.S. on a 2GB / 1 CPU DigitalOcean droplet.

---

## 1. Create the Droplet

1. Log in to [cloud.digitalocean.com](https://cloud.digitalocean.com)
2. Create Droplet:
   - **Image:** Ubuntu 24.04 LTS
   - **Size:** Basic — $12/mo (2 GB RAM / 1 CPU / 50 GB SSD)
   - **Region:** closest to your users
   - **Authentication:** SSH key (recommended) or password
3. Note the **IPv4 address** of your new droplet

---

## 2. Point Your Domain

In your DNS provider (e.g. Cloudflare, GoDaddy):

| Type | Name | Value |
|------|------|-------|
| A | `atlas` | `<droplet IPv4>` |

Wait for DNS propagation (~5–30 minutes).

---

## 3. Initial Server Setup

```bash
# SSH into droplet
ssh root@<droplet-ip>

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose plugin
apt install docker-compose-plugin -y

# Verify
docker --version
docker compose version
```

---

## 4. Clone and Configure

```bash
# Clone your repository
git clone https://github.com/yourusername/atlas.git /opt/atlas
cd /opt/atlas

# Copy and fill in the environment file
cp .env.example .env
nano .env
```

Fill in ALL values in `.env`:

```bash
# LLM
OPENROUTER_API_KEY=sk-or-...

# Microsoft Bot Framework
MICROSOFT_APP_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
MICROSOFT_APP_PASSWORD=your-client-secret

# Azure AD
AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_SECRET=your-azure-secret

# Jira
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your-service-account@yourcompany.com
JIRA_API_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=IT

# Brave Search
BRAVE_API_KEY=BSA...

# Admin Dashboard
ADMIN_USERNAME=atlas-admin
ADMIN_PASSWORD=<strong-random-password>

# Redis (Docker internal — no changes needed)
REDIS_URL=redis://redis:6379/0
```

---

## 5. SSL Certificate

```bash
# Install Certbot
apt install certbot -y

# Get certificate (replace with your domain)
certbot certonly --standalone -d atlas.yourcompany.com

# Certificates will be at:
# /etc/letsencrypt/live/atlas.yourcompany.com/fullchain.pem
# /etc/letsencrypt/live/atlas.yourcompany.com/privkey.pem
```

---

## 6. Update Nginx Config

```bash
nano /opt/atlas/nginx/nginx.conf
```

Replace `your-domain.com` with `atlas.yourcompany.com` in both server blocks and the certificate paths.

---

## 7. Start the Stack

```bash
cd /opt/atlas

# Build and start all services
docker compose up -d --build

# Verify all 3 containers are running
docker compose ps
```

Expected output:
```
NAME            IMAGE           STATUS          PORTS
atlas-app-1     atlas-app       Up              8000/tcp
atlas-redis-1   redis:7-alpine  Up              6379/tcp
atlas-nginx-1   nginx:alpine    Up              0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

---

## 8. Load Knowledge Base Guides

```bash
# Load the 5 starter guides into ChromaDB
docker compose exec app python -m knowledge_base.loader

# Expected output:
# Loaded: clear-browser-cookies.md
# Loaded: chrome-profile-setup.md
# Loaded: shared-mailbox-access.md
# Loaded: email-setup-new-device.md
# Loaded: password-reset.md
# Total guides loaded: 5
```

---

## 9. Verify Health

```bash
curl https://atlas.yourcompany.com/health
# Expected: {"status": "ok", "name": "A.T.L.A.S."}
```

---

## 10. Set Up Nightly Learning Processor (Cron)

The learning processor groups negative feedback and proposes knowledge base improvements.
Run it nightly at 2 AM server time:

```bash
crontab -e
```

Add this line:

```
0 2 * * * docker exec atlas-app-1 python -m learning.processor >> /var/log/atlas-learning.log 2>&1
```

Verify the container name matches (`docker compose ps` to check). Save and exit.

**Test it manually first:**

```bash
docker exec atlas-app-1 python -m learning.processor
# Expected: Processed N feedback entries, created M proposals.
```

---

## 11. SSL Auto-Renewal

Certbot installs a systemd timer by default. Verify it:

```bash
systemctl status certbot.timer
```

Add a post-renewal hook to reload Nginx after cert renewal:

```bash
mkdir -p /etc/letsencrypt/renewal-hooks/post
cat > /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh << 'EOF'
#!/bin/bash
docker exec atlas-nginx-1 nginx -s reload
EOF
chmod +x /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh
```

---

## 12. Useful Operations

```bash
# View live logs
docker compose logs -f app

# Restart app only (after code update)
docker compose pull app && docker compose up -d --no-deps app

# View learning processor logs
tail -f /var/log/atlas-learning.log

# Check memory usage (should be ~390MB total)
docker stats --no-stream

# Run tests in container
docker compose exec app python -m pytest tests/ -v

# Reload KB guides after adding new ones
docker compose exec app python -m knowledge_base.loader
```

---

## 13. Updating A.T.L.A.S.

```bash
cd /opt/atlas
git pull origin main
docker compose up -d --build
```

---

## Expected RAM Usage

| Service | RAM |
|---------|-----|
| FastAPI + Bot Framework | ~80 MB |
| LiteLLM | ~50 MB |
| ChromaDB (SQLite-backed) | ~100 MB |
| Redis | ~25 MB |
| Nginx | ~5 MB |
| OS overhead | ~100 MB |
| **Total** | **~360 MB** |

This leaves ~1.6 GB headroom on the 2 GB droplet.
