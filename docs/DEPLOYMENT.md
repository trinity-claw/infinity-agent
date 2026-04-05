# Guia Definitivo de Deploy p/ VPS (Docker + Evolution API)

Este documento detalha o processo para implantação (deploy) do seu ecossistema **Infinity Agent** juntamente com a **Evolution API** em uma VPS (Virtual Private Server - ex: DigitalOcean, Hetzner, AWS, Hostinger). 

Este setup converte o que antes era uma "API Local" em um **Daemon Autônomo e Nativo de WhatsApp Businesses**.

---

## 1. Topologia da Arquitetura (Cloud)

O projeto usa **Docker Compose** para orquestrar dois serviços de forma simultânea e invisível ao final-user:
1. **Infinity-Agent**: Seu backend em FastAPI rodando o *LangGraph Swarm* (com RAG, ChromaDB e persistência SQLite).
2. **Evolution API**: Instância *headless* Node.js que mantém conexão oficial (Webhook) e extra-oficial (Baileys) com a plataforma Meta/WhatsApp Business.

A comunicação HTTP ocorre internamente via *rede docker*.

---

## 2. Preparando sua VPS

Ao adquirir pelo menos uma VPS (recomendável Linux Ubuntu 22.04 LTS com mínimo 2GB RAM / 1 vCPU), conecte-se a ela via SSH:

```bash
ssh root@seu_ip_da_vps
```

### Instale as Ferramentas Iniciais:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git docker.io docker-compose ufw curl nginx certbot python3-certbot-nginx
```

Habilite os serviços para iniciarem junto a máquina:
```bash
sudo systemctl enable docker nginx
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 22
sudo ufw enable
```

---

## 3. Clone e Configure o Projeto

Descarregue seu repositório oficial na VPS protegido:

```bash
cd /opt
git clone https://github.com/Seu-Usuario/infinity-agent.git
cd infinity-agent
```

Crie seu arquivo de ambiente na raiz do projeto:
```bash
cp .env.example .env
nano .env
```

### O que editar no `.env` para Produção:
```env
APP_ENV=production
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxx   # Obrigatório
ENABLE_GUARDRAILS=True

# --- WHATSAPP CONFIGURATIONS ---
WHATSAPP_ENABLED=True
WHATSAPP_API_URL=http://evolution-api:8080      # Nome interno do container Evolution
WHATSAPP_API_TOKEN=your_strong_api_key            # MESMA Global API KEY no compose
WHATSAPP_INSTANCE=infinity_bot
WHATSAPP_OPERATOR_NUMBER=5511999999999          # Número do Atendente Humano (Transbordo)
```

---

## 4. O `docker-compose.yml` Configurado

O seu arquivo compose (`docker-compose.yml`) já vai por padrão pronto para este deploy:

```yaml
services:
  infinity-agent:
    build: .
    container_name: infinity-agent
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - chroma_data:/app/data/chroma_db
      - sqlite_data:/app/data/sqlite_db  # <- Garante o Histórico de Conversas!
    restart: unless-stopped

  evolution-api:
    image: atendesmart/evolution-api:latest
    container_name: evolution-api
    ports:
      - "8080:8080"  # Porta do painel evolution
    environment:
      - SERVER_URL=http://localhost:8080
      - AUTHENTICATION_API_KEY=${AUTHENTICATION_API_KEY:-change_me_in_env}
    volumes:
      - evolution_instances:/evolution/instances # <- Guarda os QRCodes
    restart: unless-stopped

volumes:
  chroma_data:
  sqlite_data:
  evolution_instances:
```

### Levantamento do Ecossistema
Este comando inicia e reciclará instâncias sempre que a máquina reiniciar.
```bash
docker-compose up -d --build
```

---

## 5. Reverse Proxy E Certificados (NGINX)

Não podemos expor o Bot em HTTP padrão se formos plugar Webhooks oficiais Meta pra segurança de tráfego.

```bash
nano /etc/nginx/sites-available/bot
```

```nginx
server {
    listen 80;
    server_name seudominio.com; # Ou subdominio bot.seudominio.com

    # Roteia Evolution API
    location /evolution/ {
        proxy_pass http://localhost:8080/;
        proxy_set_header Host $host;
    }

    # Roteia Agente Infinity Principal
    location / {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d seudominio.com
```

---

## 6. Integrando as Pontas (A Sincronia de Webhooks e QR Code)

Este é o momento final.

### Passo 6.1 - Registrar a Instância (Gerar seu Número Base)
Se você for usar na Evolution API de forma "QR Code" padrão. Dispare isso do SEU computador local contra a sua VPS:

```bash
curl --request POST \
  --url https://seudominio.com/evolution/instance/create \
  --header 'apikey: your_strong_api_key' \
  --header 'content-type: application/json' \
  --data '{
    "instanceName": "infinity_bot",
    "qrcode": true,
    "integration": "WHATSAPP-BAILEYS"
}'
```
Ele retornará um **base64** do QRCode. Basta escaneá-lo usando o celular dedicado (WhatsApp Web).

### Passo 6.2 - Cadastrar o Webhook do LangGraph

Dispare para conectar o motor de IA que criamos `(router webhook.py)` para ser chamado automagicamente pela Evolution API:

```bash
curl --request POST \
  --url https://seudominio.com/evolution/webhook/set/infinity_bot \
  --header 'apikey: your_strong_api_key' \
  --header 'content-type: application/json' \
  --data '{
    "webhook": {
        "enabled": true,
        "url": "https://seudominio.com/v1/webhook",
        "events": [
            "MESSAGES_UPSERT"
        ]
    }
}'
```

Pronto. Mande um `"Oi"` para o número do QR Code escaneado e admire a "mágica" das Bounding Boxes do LangGraph trabalhando de forma síncrona com SQLite persistance direto no seu bolso.

