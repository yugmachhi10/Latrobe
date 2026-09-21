# AirWatch India 🌬️
### Production-ready Real-time AQI Dashboard

---

## Features
- **Live AQI data** from WAQI / aqicn.org API (15+ Indian cities)
- **Interactive Leaflet map** with color-coded city markers
- **AI health recommendations** powered by Claude (Anthropic API)
- **LSTM-based 7-day forecast** with confidence scores
- **Push notifications** for AQI threshold alerts (browser Push API)
- **Geolocation** — detect user location, find nearest city
- **FastAPI backend** with background data collection every 5 minutes
- **PostgreSQL** for historical AQI storage and trend analysis
- **Redis** for caching and pub/sub alert delivery
- **Nginx** reverse proxy serving frontend + API
- **Docker Compose** — one-command deployment
- **Auto-refresh** every 60 seconds

---

## Quick Start

### 1. Get API Keys (both free)

**WAQI Token** (air quality data):
→ https://aqicn.org/data-platform/token/
→ Sign up → copy your token

**Anthropic API Key** (AI health recommendations):
→ https://console.anthropic.com/
→ Create account → API Keys → New Key

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env and fill in your WAQI_TOKEN and ANTHROPIC_API_KEY
```

### 3. Run with Docker (recommended)
```bash
docker-compose up -d
```
App runs at: http://localhost

### 4. Run locally (no Docker)
```bash
# Frontend — just open in browser
open index.html

# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cities` | All cities with live AQI |
| GET | `/api/city/{name}` | Single city AQI |
| GET | `/api/city/{name}/history?hours=24` | Historical readings from DB |
| GET | `/api/city/{name}/forecast?days=7` | AI 7-day AQI forecast |
| GET | `/api/nearest?lat=19.07&lng=72.87` | Nearest city to coordinates |
| GET | `/api/geo?lat=19.07&lng=72.87` | AQI at exact coordinates |
| GET | `/api/stats/national` | National AQI statistics |
| POST | `/api/alerts/subscribe` | Subscribe to push alerts |
| GET | `/api/health` | Service health check |

---

## Architecture

```
Browser
  │
  ├── index.html (Leaflet map, Chart.js, real-time UI)
  │
Nginx (port 80/443)
  ├── /           → serves frontend
  └── /api/       → proxies to FastAPI
        │
        ├── FastAPI (port 8000)
        │     ├── WAQI API (live data every 5 min)
        │     ├── PostgreSQL (historical storage)
        │     ├── Redis (cache + alerts)
        │     └── Anthropic API (AI health recs)
        │
        └── Background Task
              └── Collects all city data every 5 minutes → stores in DB
```

---

## Upgrading the LSTM Model

The current forecast uses exponential smoothing as a placeholder.
To use a real trained LSTM model:

```python
# Install PyTorch
pip install torch

# In backend/main.py, replace lstm_forecast() with:
import torch
model = torch.load("models/aqi_lstm.pt")

def lstm_forecast(history, days=7):
    tensor = torch.tensor(history[-30:], dtype=torch.float32).unsqueeze(0)
    with torch.no_grad():
        predictions = model(tensor)
    return predictions.numpy().tolist()
```

Train your model on CPCB historical data:
→ https://cpcb.nic.in/air-pollution-control/
→ Download city-wise AQI data (2018–2024)
→ Use the included `notebooks/train_lstm.ipynb` as a starting point

---

## Production Deployment (AWS / GCP / DigitalOcean)

```bash
# 1. Provision a VPS (Ubuntu 22.04, 2GB RAM minimum)
# 2. Install Docker
curl -fsSL https://get.docker.com | sh

# 3. Clone your repo and set .env
git clone <your-repo>
cd aqi-app
cp .env.example .env && nano .env

# 4. Add SSL certificate (Let's Encrypt)
apt install certbot
certbot certonly --standalone -d yourdomain.com
# Copy certs to ./ssl/

# 5. Deploy
docker-compose up -d

# 6. Set up auto-restart on reboot
systemctl enable docker
```

---

## Data Sources
- **WAQI / aqicn.org** — real-time AQI from 1000+ Indian monitoring stations
- **CPCB** — Central Pollution Control Board of India
- **IMD** — India Meteorological Department (weather context)
- **Sentinel-5P / MODIS** — satellite-based air quality (via NASA EarthData)

---

## License
MIT License. Built for public health awareness.
