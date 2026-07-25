# hinglish-asr-streamlit
# 🎙️ Hinglish ASR — Automatic Speech Recognition for Code-Mixed Hindi-English

<div align="center">

![Banner](https://img.shields.io/badge/Hinglish%20ASR-ESP32--S3%20%C2%B7%20Whisper-1a1816?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTIgMkM2LjQ4IDIgMiA2LjQ4IDIgMTJzNC40OCAxMCAxMCAxMCAxMC00LjQ4IDEwLTEwUzE3LjUyIDIgMTIgMnptLTEgMTRINXYtMmg2djJ6bTMtNEg1di0yaDl2MnptMy00SDV2LTJoMTJ2MnoiIGZpbGw9IndoaXRlIi8+PC9zdmc+)

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Modal](https://img.shields.io/badge/Backend-Modal%20Serverless-62DE61?style=flat-square)](https://modal.com)
[![Whisper](https://img.shields.io/badge/Model-Whisper%20large--v3--turbo-412991?style=flat-square&logo=openai&logoColor=white)](https://openai.com/research/whisper)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![GCET](https://img.shields.io/badge/Institution-GCET%20%C2%B7%20AKTU-orange?style=flat-square)](https://galgotiacollege.edu)

**A Streamlit web interface for real-time Hinglish (Hindi-English code-mixed) speech transcription,  
powered by OpenAI Whisper deployed on Modal serverless infrastructure.**

[Live Demo](#deployment) · [API Docs](#api-reference) · [Quick Start](#quick-start) · [Architecture](#architecture)

</div>

---

## 📖 Table of Contents

- [What is This?](#what-is-this)
- [Why Hinglish ASR?](#why-hinglish-asr)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
- [API Reference](#api-reference)
- [Endpoint Fallback Strategy](#endpoint-fallback-strategy)
- [Supported Audio Formats](#supported-audio-formats)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Research Context](#research-context)
- [Credits & Team](#credits--team)
- [License](#license)

---

## What is This?

This repository is the **web frontend** for a Hinglish Automatic Speech Recognition (ASR) system. It provides a clean, minimal Streamlit interface that lets users:

1. Upload any audio file containing Hinglish speech
2. Send it to a Modal-hosted Whisper inference endpoint
3. Get back an accurate transcription in seconds

The backend model (`whisper-large-v3-turbo`) runs as a serverless FastAPI function on Modal, with GPU inference on demand. The frontend communicates via a simple `multipart/form-data` POST request.

This project is part of broader research on **edge-device ASR for code-mixed Indian languages**, targeting deployment on ESP32-S3 microcontrollers.

---

## Why Hinglish ASR?

Hinglish — the natural mixing of Hindi and English in everyday Indian speech — is one of the most commonly spoken but least supported language variants in ASR systems. Standard English or Hindi-only models fail at code-switched utterances like:

> *"Bhai, kal meeting ka time change ho gaya, 3 baje aana instead of 2."*

Whisper `large-v3-turbo`, with its multilingual pretraining, handles this mixing significantly better than monolingual alternatives. This project makes that capability accessible through a simple web interface.

---

## Features

- **Upload & transcribe** — WAV, MP3, M4A, WEBM, OGG, FLAC, OPUS (up to 25 MB)
- **Audio preview** — listen to your file before transcribing
- **Auto fallback** — primary endpoint → fallback endpoint on credit exhaustion (429) or unavailability (503), transparent to user
- **Session history** — all transcriptions logged in the sidebar with timestamps
- **Download result** — save transcription as `.txt`
- **Zero idle API calls** — API is called only on explicit user action, never in background
- **Minimal UI** — clean ePaper-inspired aesthetic, no clutter

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        User (Browser)                        │
│                  Streamlit Web App  ← this repo              │
│                                                              │
│   1.  Upload audio file (WAV / MP3 / WEBM / ...)            │
│   2.  Click  "Transcribe →"                                  │
│   3.  View transcription + copy / download                   │
└───────────────────────┬──────────────────────────────────────┘
                        │
              POST /transcribe
              multipart/form-data
              field: file=<audio_bytes>
                        │
             ┌──────────▼──────────┐
             │   PRIMARY ENDPOINT  │
             │   Kirti · Modal     │  ahamkirtivardhansingh
             │   FastAPI + Whisper │  hinglish-asr-api
             └──────────┬──────────┘
                        │
              HTTP 429 / 503 / timeout?
              → automatic silent fallback
                        │
             ┌──────────▼──────────┐
             │   FALLBACK ENDPOINT │
             │   Dhruv · Modal     │  dhruv-04
             │   FastAPI + Whisper │  esp32-whisper-hinglish
             └──────────┬──────────┘
                        │
             ┌──────────▼──────────┐
             │  whisper-large-v3   │
             │  -turbo  inference  │
             │  (Modal GPU A10G)   │
             └──────────┬──────────┘
                        │
              {"transcription": "..."}
                        │
             ┌──────────▼──────────┐
             │   Streamlit UI      │
             │   Typewriter output │
             │   + history log     │
             └─────────────────────┘
```

### Component Breakdown

| Component | Technology | Role |
|---|---|---|
| Web UI | Streamlit + custom CSS | User interface, audio upload, result display |
| HTTP client | `requests` | Single POST per transcription session |
| ASR inference | Whisper large-v3-turbo | Speech-to-text model |
| Serving | Modal FastAPI | Serverless GPU inference endpoint |
| Primary endpoint | Kirti's Modal workspace | First-choice API target |
| Fallback endpoint | Dhruv's Modal workspace | Auto-activated on primary failure |

---

## Project Structure

```
hinglish-asr-streamlit/
│
├── app.py                  ← Main Streamlit application (all logic lives here)
├── requirements.txt        ← Python dependencies (streamlit + requests only)
├── README.md               ← This file
├── LICENSE                 ← MIT License
├── .gitignore              ← Python / Streamlit / OS ignores
│
└── .streamlit/
    └── config.toml         ← Theme, upload size limit, usage stats off
```

---

## Quick Start

### Prerequisites

- Python **3.10** or higher
- pip
- Chrome or Edge (for the ESP32 simulator; not needed for the Streamlit app)

### 1. Clone

```bash
git clone https://github.com/kirtivardhansingh29/hinglish-asr-streamlit.git
cd hinglish-asr-streamlit
```

### 2. Virtual environment (recommended)

```bash
# Create
python -m venv venv

# Activate — Windows
venv\Scripts\activate

# Activate — macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run

```bash
streamlit run app.py
```

App opens at **http://localhost:8501**

---

## Usage Guide

### Basic Transcription

1. Open the app at `http://localhost:8501`
2. Click **Browse files** or drag-and-drop an audio file into the upload box
3. The audio player appears — you can preview your file
4. Click **Transcribe →**
5. Wait 3–30 seconds (first call has a Modal cold-start delay)
6. Transcription appears with a typewriter effect
7. Copy from the text area or click **Download .txt**

### Reading the Result Metadata

After a successful transcription, two metadata tags appear below the result:

```
modal · whisper-large-v3-turbo · primary · kirti        3.7s
```

| Field | Meaning |
|---|---|
| `modal` | Inference ran on Modal serverless |
| `whisper-large-v3-turbo` | Model used |
| `primary · kirti` | Kirti's endpoint was used (credits healthy) |
| `fallback · dhruv` | Fell back to Dhruv's endpoint (primary out of credits) |
| `3.7s` | Total round-trip time including model inference |

### Session History

The sidebar tracks every transcription in the session:
- Truncated text preview
- Timestamp, filename, duration, endpoint used
- **Clear history** button to reset

---

## API Reference

### Primary Endpoint

```
POST https://ahamkirtivardhansingh--hinglish-asr-api-fastapi-app-dev.modal.run/transcribe
```

### Fallback Endpoint

```
POST https://dhruv-04--esp32-whisper-hinglish-fastapi-app.modal.run/transcribe
```

### Request

```
Content-Type: multipart/form-data

Field name : file
Type       : binary audio data
Filename   : any (e.g. recording.webm, audio.wav)
MIME type  : audio/webm | audio/wav | audio/mpeg | audio/ogg | audio/flac
```

### Response (200 OK)

```json
{
  "transcription": "bhai ye bahut accha hai, I really loved it yaar"
}
```

### Error Responses

| Status | Meaning | App behaviour |
|---|---|---|
| `200` | Success | Display transcription |
| `422` | Wrong field name or format | Show error — check field is named `file` |
| `429` | Modal credits exhausted | Silent retry with fallback endpoint |
| `503` | Modal cold start / unavailable | Silent retry with fallback endpoint |
| `504` | Gateway timeout | Show error, suggest retry |

### Example — curl

```bash
curl -X POST \
  https://ahamkirtivardhansingh--hinglish-asr-api-fastapi-app-dev.modal.run/transcribe \
  -F "file=@my_recording.wav"
```

### Example — Python

```python
import requests

with open("my_recording.wav", "rb") as f:
    res = requests.post(
        "https://ahamkirtivardhansingh--hinglish-asr-api-fastapi-app-dev.modal.run/transcribe",
        files={"file": ("my_recording.wav", f, "audio/wav")},
        timeout=60,
    )

data = res.json()
print(data["transcription"])
# → "kal office mein presentation hai, nervous hoon thoda"
```

### Example — JavaScript (fetch)

```javascript
const formData = new FormData();
formData.append("file", audioBlob, "recording.webm");

const res = await fetch(
  "https://ahamkirtivardhansingh--hinglish-asr-api-fastapi-app-dev.modal.run/transcribe",
  { method: "POST", body: formData }
);

const data = await res.json();
console.log(data.transcription);
```

---

## Endpoint Fallback Strategy

The app protects against credit exhaustion and cold-start failures using a two-tier automatic fallback:

```python
PRIMARY_API   = "https://ahamkirtivardhansingh--...modal.run/transcribe"  # Kirti's
FALLBACK_API  = "https://dhruv-04--...modal.run/transcribe"               # Dhruv's

FALLBACK_STATUSES = {429, 503, 502}  # codes that trigger a retry
```

**Flow:**

```
Request arrives
      │
      ▼
  Try PRIMARY
      │
  ┌───┴────────────────────────────────────────┐
  │                                            │
200 OK                            429 / 503 / timeout
  │                                            │
  ▼                                            ▼
Return result                           Try FALLBACK
                                              │
                                   ┌──────────┴──────────┐
                                   │                     │
                                 200 OK              any error
                                   │                     │
                                   ▼                     ▼
                             Return result         Show error UI
                             (flagged as fallback)
```

**Why this matters:**
- Kirti's credits are the primary resource and are preserved as long as possible
- Dhruv's endpoint acts as an emergency reserve, not a load-balancer
- The user never sees a failure just because one endpoint is out of credits
- The result metadata always shows which endpoint was actually used

---

## Supported Audio Formats

| Format | Extension | Notes |
|---|---|---|
| WAV | `.wav` | Best quality · lossless · recommended |
| MP3 | `.mp3` | Widely compatible |
| M4A | `.m4a` | Standard iPhone voice memo format |
| OGG Vorbis | `.ogg` | Open format |
| WebM Opus | `.webm` | Browser MediaRecorder output |
| FLAC | `.flac` | Lossless compressed |
| Opus | `.opus` | Efficient for speech |

**For best transcription accuracy:**

```
Sample rate  : 16 kHz   (Whisper's native rate — no resampling needed)
Channels     : Mono      (stereo works but mono is faster)
Bit depth    : 16-bit
Max duration : ~10 min   (keep under 25 MB)
```

---

## Deployment

### Option A — Streamlit Community Cloud (free, recommended)

1. Fork or push this repo to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app**
4. Select: `kirtivardhansingh29/hinglish-asr-streamlit` · branch `main` · file `app.py`
5. Click **Deploy**

Public URL ready in ~2 minutes: `https://hinglish-asr-streamlit.streamlit.app`

### Option B — Local (already covered in Quick Start)

```bash
streamlit run app.py
```

### Option C — Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
```

```bash
docker build -t hinglish-asr .
docker run -p 8501:8501 hinglish-asr
```

---

## Troubleshooting

### "Both endpoints timed out"
Modal serverless functions have a **cold start** of 15–30 seconds when they haven't been called recently. Simply wait a moment and press **Transcribe →** again. The second call is always warm and fast (~3–8s).

### "HTTP 429: workspace billing cycle spend limit"
Both endpoints are out of Modal free credits. Options:
- Add credits at [modal.com/billing](https://modal.com/billing)
- Use the Browser Web Speech API path in the ESP32 simulator (free, no credits needed)

### "HTTP 422: Unprocessable Entity"
The API expects the audio under the field name **`file`** exactly. If calling directly, ensure:
```python
files={"file": ("filename.wav", f, "audio/wav")}  # ✓ correct
files={"audio": ("filename.wav", f, "audio/wav")}  # ✗ wrong field name
```

### App won't start
```bash
pip install --upgrade streamlit requests
streamlit run app.py
```

### Transcription is empty or garbled
- Ensure the audio contains clear speech (not silence or heavy background noise)
- Try recording at 16 kHz mono if possible
- Whisper handles Hinglish best with naturally spoken, continuous sentences

### Port already in use
```bash
streamlit run app.py --server.port 8502
```

---

## Research Context

This project is part of the **ESP32-S3 Edge Hinglish ASR** research initiative at GCET.

**Problem Statement:**  
Code-mixed speech (Hinglish) is the dominant mode of communication among educated urban Indians, yet existing ASR systems are trained on monolingual data and perform poorly on it. Deploying capable ASR on edge microcontrollers (ESP32-S3) further compounds the challenge due to compute and memory constraints.

**Approach:**
- Use OpenAI Whisper `large-v3-turbo` as the core ASR model (strong multilingual baseline)
- Deploy on Modal serverless for cloud-based inference during prototyping
- Build a web simulator to demonstrate the pipeline to academic audiences
- Long-term target: quantized on-device inference on ESP32-S3

**Pipeline:**

```
Microphone (ESP32-S3 / Browser)
        │
        ▼
  Audio capture (16kHz mono WAV)
        │
        ▼
  HTTP POST → Modal FastAPI
        │
        ▼
  Whisper large-v3-turbo inference
        │
        ▼
  JSON response → {"transcription": "..."}
        │
        ▼
  Display in UI / Serial output on device
```

---

## Credits & Team

| Role | Name | Profile |
|---|---|---|
| Project Lead · Frontend · ASR Pipeline | Kirti Vardhan Singh | [GitHub](https://github.com/kirtivardhansingh29) |
| ASR Backend · Modal Deployment | Dhruv Kumar | Chairperson, GFGCB-GCET |
| Faculty Supervisor | Dr. Pallavi Goel | GCET, Greater Noida |
| Institution | Galgotias College of Engineering and Technology | AKTU, Greater Noida |

**Tools & Services:**

| Tool | Purpose |
|---|---|
| [OpenAI Whisper](https://github.com/openai/whisper) | Core ASR model |
| [Modal](https://modal.com) | Serverless GPU inference hosting |
| [Streamlit](https://streamlit.io) | Web UI framework |
| [FastAPI](https://fastapi.tiangolo.com) | Backend API framework |
| [ESP32-S3](https://www.espressif.com/en/products/socs/esp32-s3) | Target edge hardware |

---

## License

```
MIT License

Copyright (c) 2025 Kirti Vardhan Singh

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

<div align="center">
  <sub>
    Built with ❤️ at GCET · Greater Noida · AKTU · 2025<br>
    <a href="https://github.com/kirtivardhansingh29">Kirti Vardhan Singh</a> ·
    GFG Campus Mantri · Technical Coordinator, GFGCB-GCET
  </sub>
</div>
