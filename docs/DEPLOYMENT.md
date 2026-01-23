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

**Costo stimato**: ~$7-11/mese
- VPS: $6/mese (DigitalOcean Basic)
- Claude API: $1-5/mese (dipende dall'uso)
- Alpaca: Gratis (paper trading)

---

## Step 1: Creare SSH Key

La SSH key è come una "chiave digitale" per accedere al server in modo sicuro, senza password.

### Sul tuo PC (Mac/Linux)
Apri il **Terminal** e esegui:

```bash
# Controlla se hai già una chiave
ls ~/.ssh/

# Se NON hai id_ed25519.pub, creala:
ssh-keygen -t ed25519 -C "tua@email.com"
# Premi INVIO a tutte le domande (usa i default)

# Copia la chiave pubblica
cat ~/.ssh/id_ed25519.pub
```

### Su Windows
Apri **PowerShell** o **Git Bash**:

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

2. **Choose an image**: Ubuntu 24.04 LTS

3. **Choose Size**: 
   - **Basic** → **Regular** → **$6/mo** (1 GB RAM, 25 GB SSD)
   - ✅ Sufficiente per il bot

4. **Choose Region**: Scegli la più vicina a te (es: Frankfurt per EU)

5. **Authentication**: 
   - Seleziona **SSH Key**
   - Clicca **New SSH Key**
   - Incolla la chiave pubblica copiata prima
   - Dai un nome (es: "MacBook", "PC Casa")

6. **Hostname**: `ai-scalping-bot` (o quello che preferisci)

7. Clicca **Create Droplet**

8. **Copia l'indirizzo IP** che appare (es: `167.99.123.45`)

---

## Step 3: Deploy del Bot

### Connettiti al server

```bash
ssh root@<IP_DEL_DROPLET>
# Esempio: ssh root@167.99.123.45
```

Se chiede "Are you sure you want to continue connecting?" → scrivi `yes`

### Deploy automatico (consigliato)

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

# Per il data feed (può essere uguale a Claude)
ALPACA_API_KEY_GEMINI=pk_xxxxxxxxxxxxxxxxxx
ALPACA_SECRET_KEY_GEMINI=sk_xxxxxxxxxxxxxxxxxx

# Claude AI
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxx

# Modalità paper trading (IMPORTANTE: lascia True per test!)
PAPER_TRADING=True
```

**Salva**: `Ctrl+X` → `Y` → `Enter`

---

## Step 5: Avviare il Bot

```bash
cd /opt/ai-scalping
docker compose up -d
```

Verifica che sia partito:

```bash
docker compose ps
# Dovresti vedere: ai-scalping-bot   running

docker compose logs -f
# Vedi i log in tempo reale (Ctrl+C per uscire)
```

🎉 **Il bot è attivo!**

---

## Comandi Utili

### Gestione Bot

```bash
cd /opt/ai-scalping

# Stato del bot
docker compose ps

# Log in tempo reale
docker compose logs -f

# Ultime 100 righe di log
docker compose logs --tail 100

# Riavvia il bot
docker compose restart

# Ferma il bot
docker compose down

# Aggiorna il bot (pull nuova versione da GitHub)
git pull
docker compose up -d --build
```

### Backup Database

```bash
# Dal server: copia il DB in locale
scp root@<IP>:/opt/ai-scalping/trading_bot.db ./backup_$(date +%Y%m%d).db

# Esempio:
scp root@167.99.123.45:/opt/ai-scalping/trading_bot.db ./backup.db
```

### Ispezionare il Database

```bash
# Sul server
sqlite3 /opt/ai-scalping/trading_bot.db

# Query utili:
.tables                           # Mostra tabelle
SELECT * FROM trades;             # Tutti i trade
SELECT * FROM strategic_signals;  # Tutti i segnali
SELECT * FROM logs ORDER BY id DESC LIMIT 20;  # Ultimi log
.quit                             # Esci
```

---

## Troubleshooting

### Il bot non parte

```bash
# Controlla i log per errori
docker compose logs --tail 50

# Verifica che .env esista e abbia le chiavi
cat /opt/ai-scalping/.env
```

### Errore "Permission denied" su SSH

```bash
# Sul TUO PC, verifica i permessi della chiave
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
```

### Aggiungere SSH key da un altro PC

Dal PC che ha già accesso:

```bash
ssh root@<IP>
nano ~/.ssh/authorized_keys
# Aggiungi la nuova chiave pubblica su una nuova riga
# Salva: Ctrl+X, Y, Enter
```

### Il bot si ferma dopo un po'

Verifica che Docker sia configurato per il restart automatico:

```bash
docker compose ps
# Deve mostrare "restart: unless-stopped"
```

### Vedere quanto spazio disco usi

```bash
df -h           # Spazio disco totale
du -sh /opt/*   # Spazio per cartella
```

---

## Architettura

```
DigitalOcean Droplet ($6/mo)
├── Docker
│   └── ai-scalping-bot (container)
│       ├── Python 3.11
│       ├── src/main.py (entry point)
│       └── trading_bot.db (SQLite)
│
├── /opt/ai-scalping/
│   ├── .env (API keys - NON committato)
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── src/
│
└── Connessioni esterne:
    ├── Alpaca API (market data + orders)
    └── Anthropic API (Claude AI)
```

---

## Costi Dettagliati

| Servizio | Costo | Note |
|----------|-------|------|
| DigitalOcean Droplet | $6/mese | Basic 1GB RAM |
| DigitalOcean Backup | +$1.20/mese | Opzionale ma consigliato |
| Claude API (Haiku) | ~$0.25/1M input tokens | Molto economico |
| Alpaca | Gratis | Paper trading illimitato |

**Stima mensile**: $7-12 (dipende da quante chiamate API fai)

---

## Contatti e Supporto

- Repository: https://github.com/NabilTouri/ai-scalping
- Alpaca Docs: https://docs.alpaca.markets
- Anthropic Docs: https://docs.anthropic.com
