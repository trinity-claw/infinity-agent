# Deployment Guide (Single VPS)

This guide deploys the full stack on one VPS:
- Infinity Agent API (FastAPI)
- Evolution API (WhatsApp bridge)
- Nginx reverse proxy + TLS

## 1) VPS Prerequisites

Recommended minimum:
- Ubuntu 22.04/24.04
- 2 GB RAM
- 1 vCPU

Install packages:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git docker.io docker-compose nginx certbot python3-certbot-nginx ufw
sudo systemctl enable docker nginx
```

Firewall:

```bash
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

## 2) Clone and Configure

```bash
cd /opt
git clone https://github.com/<your-org>/<your-repo>.git infinity-agent
cd infinity-agent
cp .env.example .env
```

Edit `.env`:
- set `OPENROUTER_API_KEY`
- set WhatsApp fields if using Evolution integration
- set `AUTHENTICATION_API_KEY` for Evolution API service auth

## 3) Start Services

```bash
docker compose up -d --build
```

This starts the core API service (`infinity-agent`).

If you also want to run Evolution API from this compose file:

```bash
docker compose --profile whatsapp up -d evolution-api
```

If Evolution API is already running in another stack/host, keep this profile disabled and only configure:
- `WHATSAPP_API_URL`
- `WHATSAPP_API_TOKEN`
- `WHATSAPP_INSTANCE`

Check health:

```bash
curl -sS http://127.0.0.1:8000/v1/health
```

## 4) Nginx Reverse Proxy

Create `/etc/nginx/sites-available/infinity-agent`:

```nginx
server {
  listen 80;
  listen [::]:80;
  server_name YOUR_DOMAIN;

  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

Enable and reload:

```bash
sudo ln -s /etc/nginx/sites-available/infinity-agent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Issue TLS certificate:

```bash
sudo certbot --nginx -d YOUR_DOMAIN
```

## 5) Evolution API Instance Setup

Assuming Evolution API is exposed on `http://127.0.0.1:8080` (or your configured URL).

Create instance:

```bash
export EVO_URL="http://127.0.0.1:8080"
export EVO_API_KEY="YOUR_EVOLUTION_API_KEY"
export INSTANCE="infinity_bot"

curl -sS -X POST "$EVO_URL/instance/create" \
  -H "Content-Type: application/json" \
  -H "apikey: $EVO_API_KEY" \
  -d "{\"instanceName\":\"$INSTANCE\",\"qrcode\":true,\"integration\":\"WHATSAPP-BAILEYS\"}"
```

Set webhook to backend:

```bash
curl -sS -X POST "$EVO_URL/webhook/set/$INSTANCE" \
  -H "Content-Type: application/json" \
  -H "apikey: $EVO_API_KEY" \
  -d '{
    "webhook": {
      "enabled": true,
      "url": "https://YOUR_DOMAIN/v1/webhook",
      "events": ["MESSAGES_UPSERT"],
      "webhook_by_events": false,
      "webhook_base64": false
    }
  }'
```

## 6) Operational Checks

- API health: `GET /v1/health`
- Chat endpoint: `POST /v1/chat`
- Evolution state:

```bash
curl -sS -H "apikey: $EVO_API_KEY" "$EVO_URL/instance/connectionState/$INSTANCE"
```

## 7) Persistence Notes

`docker-compose.yml` already mounts persistent volumes for:
- Chroma data
- SQLite checkpointer/state
- Evolution instances

Do not remove these volumes in production.
