<h1 align="center">Sergak AI — Industrial Safety Monitor</h1>

<p align="center">
  Turns a factory's existing CCTV into a real-time workplace-safety monitor.<br>
  Five YOLO detectors, a FastAPI backend, a live operator dashboard, and Telegram alerting.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white">
  <img src="https://img.shields.io/badge/Ultralytics_YOLOv8-111F68?style=flat-square">
  <img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square">
</p>

---

## The problem

Uzbek industrial plants already have hundreds of CCTV cameras installed, but the footage is only reviewed **after** an incident. One safety officer cannot watch forty feeds at once. Missing hard hats, phone use in restricted zones, falls and early-stage fires go unnoticed until they cost someone.

## What this does

Sergak AI attaches to the RTSP streams of cameras that are already on site, runs YOLO detectors over them continuously, and pushes an annotated snapshot to a Telegram group within seconds of a violation — while writing every event to a database the plant can audit later.

Nothing leaves the plant's network: inference runs on-premise.

---

## Detection modules

| Module | Detects | Status |
|---|---|---|
| **helmet** | Missing hard hat / PPE | Trained — **97.5% mAP@50**, 82.2% mAP@50-95 |
| **smoking** | Smoking in prohibited areas | Trained — 87.1% mAP@50, 54.9% mAP@50-95 |
| **phone** | Phone use in restricted zones | Trained, benchmark rerun in progress |
| **fall** | Person falling / lying down | Trained, benchmark rerun in progress |
| **fire_smoke** | Early-stage fire and smoke | Trained, benchmark rerun in progress |

Reported figures come from Ultralytics `model.val()` runs; see [Training](#training) for the setup behind them.

---

## Architecture

```
┌────────────────┐   RTSP    ┌──────────────────────────┐
│ Existing CCTV  │ ────────► │ camera_worker (per feed)  │
│ Hikvision NVR  │           │ reconnect · frame buffer  │
└────────────────┘           └────────────┬─────────────┘
                                          │
                                          ▼
                             ┌──────────────────────────┐
                             │   inference (YOLOv8)      │
                             │ helmet · phone · fall     │
                             │ fire/smoke · smoking      │
                             └────────────┬─────────────┘
                                          │ detections
                                          ▼
                             ┌──────────────────────────┐
                             │      alert_manager        │
                             │ dedup · cooldown · route  │
                             └────────────┬─────────────┘
                  ┌───────────────────────┼────────────────────────┐
                  ▼                       ▼                        ▼
        ┌──────────────────┐   ┌────────────────────┐   ┌───────────────────┐
        │  events + media  │   │  FastAPI REST API  │   │  Telegram worker  │
        │    (database)    │   │  → web dashboard   │   │   (aiogram bot)   │
        └──────────────────┘   └────────────────────┘   └───────────────────┘
```

---

## Features

**Monitoring**
- Multi-camera RTSP ingest with automatic reconnect
- Hikvision **NVR discovery** — scans the subnet and registers channels
- Per-camera module assignment (which detectors run on which feed)
- Event deduplication and alert cooldown so one violation is not sent forty times

**Operations**
- Web dashboard: live view, event feed, analytics, floor plan, reports
- Departments and users — violations are routed to the responsible department
- Role-based access with JWT
- Google OAuth sign-in and OTP e-mail verification
- In-app chat between operators

**Delivery**
- Telegram bot: annotated snapshot + camera, module and timestamp
- E-mail notifications
- Docker Compose deployment

---

## Repository layout

```
backend/
├── app/
│   ├── api/          auth · auth_google · cameras · chat · departments
│   │                 discovery · events · modules · nvr · settings · users
│   ├── core/         auth · config · database · email · inference
│   │                 otp · security · seed
│   ├── ml/           inference · camera_worker · alert_manager
│   ├── models/       SQLAlchemy models
│   └── workers/      telegram_bot.py
├── requirements.txt
├── config.yaml
└── Dockerfile

frontend/
├── index · login · register · cameras · events · analytics
│   modules · departments · users · reports · settings · chat · floorplan
└── assets/js/        api · app · auth · components · data · pages

kaska/                helmet dataset pipeline + training scripts
smoking/              smoking dataset pipeline + training scripts
docker-compose.yml
```

---

## Quick start

```bash
git clone https://github.com/Mardonaka05/sergak-ai.git
cd sergak-ai

cp backend/.env.example backend/.env    # fill in the values below
docker compose up -d
```

Dashboard: `http://localhost:8000` · API docs: `http://localhost:8000/docs`

<details>
<summary>Without Docker</summary>

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

</details>

### Configuration

| Variable | Description |
|---|---|
| `DATABASE_URL` | SQLite or MySQL connection string |
| `JWT_SECRET` | Random secret for token signing |
| `NVR_HOST` / `NVR_USER` / `NVR_PASS` | Hikvision NVR credentials for discovery |
| `RTSP_URLS` | Comma-separated stream URLs (if not using NVR discovery) |
| `BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Telegram alerting |
| `SMTP_USER` / `SMTP_PASSWORD` | E-mail notifications and OTP |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth |
| `CONF_THRESHOLD` | Detection confidence cutoff |
| `DEVICE` | `cuda:0` or `cpu` |

Model weights are not in this repository — download them from [Releases](../../releases) into `backend/models_pt/`.

---

## Training

Datasets were assembled from public sources plus frames pulled from the deployment cameras themselves, labelled in **CVAT** (self-hosted via Docker) and exported in YOLO format.

```bash
python kaska/scripts/train.py --data kaska/merged/data.yaml \
                              --model yolov8n.pt \
                              --epochs 50 --imgsz 640 --batch 16
```

Best helmet run — `yolov8n`, 640px, batch 16, 2 classes (`helmet`, `no_helmet`):

| Precision | Recall | mAP@50 | mAP@50-95 |
|---|---|---|---|
| 0.956 | 0.928 | **0.975** | 0.822 |

The single biggest gain came from adding frames sampled from the actual deployment cameras. Domain match beat dataset size and every hyperparameter change we tried.

---

## Deployment target

Designed to run on-premise on an **NVIDIA Jetson Orin NX** alongside the plant's existing PoE camera network, so no video leaves the site.

---

## Roadmap

- [ ] TensorRT export + INT8 quantization for Jetson
- [ ] Badge-based OCR worker identification for underground sites
- [ ] Rebuild the smoking dataset — current mAP@50-95 is too low to ship
- [ ] Per-shift reporting and export

---

## License

MIT — see [LICENSE](LICENSE).

## Author

**Mardonbek Sulaymonqulov** — AI / Computer Vision Engineer
[GitHub](https://github.com/Mardonaka05) · mardonbeksulaymonqulov156@gmail.com
