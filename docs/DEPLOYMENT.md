# 🚀 Deployment Guide - AI Scalping Bot

Guida completa per deployare il bot su DigitalOcean (o qualsiasi VPS).

## Indice
- [Prerequisiti](#prerequisiti)
- [Step 1: Creare SSH Key](#step-1-creare-ssh-key)
- [Step 2: Creare Droplet DigitalOcean](#step-2-creare-droplet-digitalocean)
- [Step 3: Deploy del Bot](#step-3-deploy-del-bot)
- [Step 4: Configurare API Keys](#step-4-configurare-api-keys)
- [Step 5: Avviare il Bot](#step-5-avviare-il-bot)
- [Comandi Utili](#comandi-utili)
- [Troubleshooting](#troubleshooting)

---

## Prerequisiti

- Account [DigitalOcean](https://cloud.digitalocean.com) (o altro VPS provider)
- Account [Alpaca](https://alpaca.markets) con Paper Trading attivo
- API Key [Anthropic](https://console.anthropic.com) per Claude

**Costo stimato**: ~$8-12/mese
- VPS: $8/mese (DigitalOcean Basic)
- Claude API: $1-5/mese (dipende dall'uso)
- Alpaca: Gratis (paper trading)

---

## Step 1: Creare SSH Key

La SSH key è una "chiave digitale" per accedere al server in modo sicuro.

### Mac/Linux
```bash
# Controlla se hai già una chiave
ls ~/.ssh/

# Se NON hai id_ed25519.pub, creala:
ssh-keygen -t ed25519 -C "tua@email.com"
# Premi INVIO a tutte le domande

# Copia la chiave pubblica
cat ~/.ssh/id_ed25519.pub
```

### Windows (PowerShell)
```powershell
# Controlla se hai già una chiave
dir ~/.ssh/

# Se NON hai id_ed25519.pub, creala:
ssh-keygen -t ed25519 -C "tua@email.com"
# Premi INVIO a tutte le domande

# Copia la chiave pubblica
cat ~/.ssh/id_ed25519.pub
```

**Copia tutto l'output** (inizia con `ssh-ed25519 AAAA...`).

> ⚠️ **IMPORTANTE**: 
> - `id_ed25519` = chiave PRIVATA (non condividere MAI!)
> - `id_ed25519.pub` = chiave PUBBLICA (questa va su DigitalOcean)

---

## Step 2: Creare Droplet DigitalOcean

1. Vai su [DigitalOcean](https://cloud.digitalocean.com) → **Create** → **Droplets**

2. **Choose image**: Ubuntu 24.04 LTS

3. **Choose Size**: 
   - **Basic** → **Regular** → **$8/mo** (1 GB RAM, 25 GB SSD)
   - ✅ Sufficiente per bot + dashboard

4. **Choose Region**: Frankfurt (o la più vicina)

5. **Authentication**: 
   - Seleziona **SSH Key**
   - Clicca **New SSH Key**
   - Incolla la chiave pubblica
   - Dai un nome (es: "PC Casa")

6. **Hostname**: `ai-scalping-bot`

7. Clicca **Create Droplet**

8. **Copia l'indirizzo IP** (es: `167.99.123.45`)

---

## Step 3: Deploy del Bot

### Connettiti al server

```bash
ssh root@<IP_DEL_DROPLET>
# Esempio: ssh root@167.99.123.45
```

### Deploy automatico

```bash
curl -sSL https://raw.githubusercontent.com/NabilTouri/ai-scalping/main/deploy.sh | bash
```

Questo script:
- Aggiorna il sistema
- Installa Docker
- Clona il repository
- Prepara tutto per l'avvio

---

## Step 4: Configurare API Keys

```bash
cd /opt/ai-scalping
nano .env
```

Inserisci le tue chiavi:

```env
# Alpaca Paper Trading
ALPACA_API_KEY_CLAUDE=pk_xxxxxxxxxxxxxxxxxx
ALPACA_SECRET_KEY_CLAUDE=sk_xxxxxxxxxxxxxxxxxx

# Claude AI
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxx

# Modalità paper trading (IMPORTANTE: lascia True!)
PAPER_TRADING=True
```

**Salva**: `Ctrl+X` → `Y` → `Enter`

---

## Step 5: Avviare il Bot

```bash
cd /opt/ai-scalping
docker compose up -d
```

Verifica:

```bash
docker compose ps
# Dovresti vedere:
# - ai-scalping-bot       running
# - ai-scalping-dashboard running

docker compose logs -f trading-bot
# Log in tempo reale (Ctrl+C per uscire)
```

### Accedi alla Dashboard

Apri nel browser: `http://<IP_DROPLET>:8080`

Esempio: `http://167.99.123.45:8080`

🎉 **Il bot è attivo!**

---

## Comandi Utili

### Gestione Bot

```bash
cd /opt/ai-scalping

# Stato
docker compose ps

# Log bot
docker compose logs -f trading-bot

# Log dashboard
docker compose logs -f dashboard

# Riavvia tutto
docker compose restart

# Ferma tutto
docker compose down

# Aggiorna (nuova versione da GitHub)
./deploy.sh update
```

### Backup Database

```bash
# Dal TUO PC: copia il DB in locale
scp root@<IP>:/opt/ai-scalping/data/trading_bot.db ./backup_$(date +%Y%m%d).db
```

### Ispezionare il Database

```bash
# Sul server
sqlite3 /opt/ai-scalping/data/trading_bot.db

# Query utili:
.tables
SELECT * FROM trades;
SELECT * FROM strategic_signals ORDER BY id DESC LIMIT 5;
SELECT * FROM bot_status;
.quit
```

---

## Troubleshooting

### Bot non parte

```bash
# Controlla i log
docker compose logs --tail 50 trading-bot

# Verifica .env
cat /opt/ai-scalping/.env
```

### Dashboard non raggiungibile

```bash
# Verifica che sia running
docker compose ps

# Controlla log
docker compose logs dashboard

# Firewall (DigitalOcean)
# Assicurati che porta 8080 sia aperta
```

### "Permission denied" su SSH

```bash
# Sul TUO PC
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
```

### Reset database

```bash
cd /opt/ai-scalping
docker compose down
rm -f data/trading_bot.db
docker compose up -d
```

---

## Architettura

```
DigitalOcean Droplet ($8/mo)
├── Docker Compose
│   ├── ai-scalping-bot (container)
│   │   ├── Python 3.11 + main.py
│   │   └── Strategy + Execution loops
│   │
│   └── ai-scalping-dashboard (container)
│       ├── FastAPI + Uvicorn
│       └── Porta 8080
│
├── /opt/ai-scalping/
│   ├── .env (API keys)
│   ├── data/trading_bot.db (SQLite)
│   ├── docker-compose.yml
│   └── src/
│
└── Connessioni esterne:
    ├── Alpaca API (data + orders)
    └── Anthropic API (Claude)
```

---

## Costi

| Servizio | Costo | Note |
|----------|-------|------|
| DigitalOcean Droplet | $8/mese | Basic 1GB RAM |
| DigitalOcean Backup | +$1.60/mese | Opzionale |
| Claude API (Haiku) | ~$0.25/1M tokens | Molto economico |
| Alpaca | Gratis | Paper trading |

**Stima mensile**: $8-12

---

## Link Utili

- Repository: https://github.com/NabilTouri/ai-scalping
- Dashboard: `http://<IP>:8080`
- Alpaca Docs: https://docs.alpaca.markets
- Anthropic Docs: https://docs.anthropic.com
