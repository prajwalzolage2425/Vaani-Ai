# 🕉️ VaaniAI (वाणीAI)
### AI-Powered Sanskrit Pronunciation & Phonetic Correction System
**Grounded in Indian Knowledge Systems (Pāṇinīya Śikṣā — Vedāṅga of Phonetics)**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask 3.0](https://img.shields.io/badge/Flask-3.0%2B-green.svg)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-pymongo-brightgreen.svg)](https://www.mongodb.com/)
[![Google Gemini API](https://img.shields.io/badge/Google_Gemini-google--genai-orange.svg)](https://aistudio.google.com/)
[![IKS Vedāṅga](https://img.shields.io/badge/IKS-Pāṇinīya_Śikṣā-red.svg)](#)

---

## 📌 Problem & IKS Innovation
Learners of Sanskrit and Indian languages frequently struggle to produce correct classical pronunciations—notably confusing:
- **Dental (त) vs Retroflex (ट)**
- **Dental Voiced (द) vs Retroflex Voiced (ड)**
- **Unaspirated (ग / क / प) vs Aspirated (घ / ख / फ)**
- **Palatal (श) vs Retroflex (ष) vs Dental (स)**

Classical Indian phonetics (**Śikṣā**, the first of the six Vedāṅgas) systematically codifies articulation through:
1. **Sthāna (स्थान - Place of Articulation)**: The exact anatomical point in the vocal tract where the breath is obstructed or shaped:
   - *Kaṇṭha* (कण्ठ - Throat/Velum)
   - *Tālu* (तालु - Hard Palate)
   - *Mūrdhā* (मूर्धा - Palate Roof/Retroflex)
   - *Danta* (दन्त - Upper Front Teeth)
   - *Oṣṭha* (ओष्ठ - Lips)
   - *Nāsikā* (नासिका - Nasal cavity)
2. **Prayatna (प्रयत्न - Articulatory Effort / Manner)**:
   - *Alpaprāṇa* (अल्पप्राण - gentle breath) vs *Mahāprāṇa* (महाप्राण - aspirated burst)
   - *Aghoṣa* (अघोष - unvoiced) vs *Ghoṣa* (घोष - vocal cord vibration)

### 💡 Core Innovation (Deterministic IKS Engine)
Most generic speech-to-text models auto-correct the speaker's mispronunciations, assuming what the speaker intended.
**VaaniAI does NOT let the LLM guess or hallucinate phonetic rules.**
1. **Acoustic Transcription**: Google Gemini analyzes the raw audio and transcribes the exact sounds articulated.
2. **Deterministic Pāṇinian Comparative Engine**: Our backend compares the target sound against the heard sound in MongoDB and computes the precise delta in Sthāna, Aspiration, and Voicing.
3. **Anatomical Sthāna Feedback**: The user sees an interactive SVG mouth cross-section highlighting where their tongue went wrong and where it must move according to Pāṇini’s classical sutras (e.g. *ऌतुलसानां दन्ताः* vs *ऋटुरषाणां मूर्धा*).

---

## 🏗️ System Architecture & Tech Stack

- **Frontend**: Plain HTML5, Vanilla CSS3 (custom saffron/cream/deep-brown palette, Noto Sans Devanagari typography), Vanilla JavaScript (No frameworks, No build step).
- **Interactive Vocal Tract**: Dynamic SVG with sagittal mouth cross-section, dynamic tongue curvature, and animated corrective arrows.
- **Backend**: Python Flask with `flask-cors`.
- **Database**: MongoDB via `pymongo` (with automatic, zero-crash in-memory/JSON fallback if MongoDB is not running locally).
- **AI Engine**: Google Gemini API via the official `google-genai` Python SDK (`Config.GEMINI_MODEL`).
- **Resilience**: Built-in `DEMO_MODE` flag that ensures zero presentation failures during live exhibition demos.

---

## 🚀 Setup & Execution Guide

### Prerequisites
- Python 3.10+ (or Python 3.11/3.12)
- (Optional) MongoDB running at `mongodb://localhost:27017` (If MongoDB is absent, the app operates automatically with its built-in in-memory fallback!)
- (Optional) Free Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/)

### Step 1: Clone or Navigate to Project
```bash
cd vaani
```

### Step 2: Create and Activate Virtual Environment
```bash
# On Windows (PowerShell):
python -m venv .venv
.venv\Scripts\Activate.ps1

# On Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment (`.env`)
The file `.env` is pre-configured with `DEMO_MODE=true` so you can test immediately without any API keys.
To use live Google Gemini AI speech transcription, open `.env` and set your key:
```ini
PORT=5000
FLASK_DEBUG=True
MONGO_URI=mongodb://localhost:27017
DB_NAME=vaaniai
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
DEMO_MODE=false
```

### Step 5: Seed the Database
Populate the 25 sparsha consonants, semivowels, sibilants, vowels, and practice items:
```bash
python seed/seed.py
```
*(If MongoDB is running, documents are inserted into collections. If MongoDB is offline, it safely reports the status while continuing with fallback data).*

### Step 6: Start the Flask Application
```bash
python app.py
```

Open your browser and navigate to:
👉 **`http://localhost:5000`**

---

## 🎭 2-Minute Exhibition Demo Script for Judges

Use this step-by-step walkthrough to wow the judges:

1. **Introduction (0:00 - 0:25)**:
   - *"Respected judges, classical Sanskrit is a phonetic language governed by Shiksha, a Vedanga codified by Maharshi Panini. Modern learners struggle because standard speech AI auto-corrects mistakes rather than explaining vocal articulation."*
   - Show the **Home Page**: Select language (*संस्कृतम्*), level (*प्रारम्भिक*), and click **Start Practicing**.

2. **The Classic Trap: Dental त vs Retroflex ट (0:25 - 1:00)**:
   - Choose the first minimal pair: **त vs ट** (*ta vs ṭa*).
   - Point out the **Sthāna Panel**: Show the SVG mouth diagram. Highlight that **त** is *दन्त्य (Dantya)* governed by Panini's sutra *'ऌतुलसानां दन्ताः'* (tongue tip on upper teeth).
   - Click **Listen Reference** to hear clean pronunciation via speech synthesis.
   - Click **Record**, speak into the mic, and click **Stop**.
   - Click **Analyze Pronunciation**.

3. **Demonstrating the IKS Diagnostic (1:00 - 1:35)**:
   - Show the **Result Screen**:
     - Point to the **Character Breakdown**: The target character **त** shows an error state.
     - Look at the **Sthāna Mouth Cross-Section**: The diagram dynamically highlights the expected Dantya in green, the heard Mūrdhanya in red, and draws a green directional arrow indicating where the tongue must shift!
     - Read the **Pāṇinian Articulatory Remedy**: *"You articulated at Mūrdhā (retroflex dome) producing 'ट'; however 'त' is Dantya. Panini's rule: 'ऌतुलसानां दन्ताः'. Touch the flat tip of your tongue against the back of your upper front teeth—do NOT curl backward."*
     - Point out: *"The LLM identifies what was spoken, but our deterministic Shiksha engine computes the exact anatomical advice."*

4. **Analytics & Progress Dashboard (1:35 - 2:00)**:
   - Click **Dashboard** in the top navigation.
   - Show the **Accuracy Curve** generated with Chart.js.
   - Point out **Phonetic Error Clusters Grouped by Varga**: The system automatically groups the student's mistakes by varga (*त-वर्ग, ट-वर्ग, क-वर्ग*), proving longitudinal pedagogical value.

---

## 🛠️ API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System health, MongoDB status, Gemini config, Demo Mode state |
| `GET` | `/api/items?level=&language=` | Returns filtered practice items (pairs, words, shlokas) |
| `GET` | `/api/sounds/<symbol>` | Retrieves Pāṇinian phonetic metadata (Sthāna, Prayatna, Sutra) |
| `GET` | `/api/sounds` | Returns all 40+ seeded sounds in catalog |
| `POST` | `/api/analyze` | Multipart form (audio, `item_id`, `user_id`) -> Returns score, character breakdown, and Shiksha tips |
| `GET` | `/api/progress/<user_id>` | Returns session attempts and weak sounds grouped by varga |

---

## 📂 Project Directory Structure

```
vaaniai/
├── app.py                      # Main Flask application & API routes
├── config.py                   # Central settings, constants & DEMO_MODE toggle
├── requirements.txt            # Python dependencies
├── .env.example                # Configuration template
├── .env                        # Active environment configuration
├── .gitignore                  # Git ignore rules
├── services/
│   ├── __init__.py             # Services export package
│   ├── db_service.py           # MongoDB driver with memory fallback
│   ├── gemini_service.py       # Google Gemini SDK caller with retry & demo mode
│   ├── phonetics_service.py    # Deterministic Paninian Shiksha comparator
│   └── scoring.py              # Composite Shiksha articulatory scoring
├── seed/
│   ├── seed.py                 # Database population script
│   ├── sounds.json             # 40+ Sanskrit sounds with Sthana, Prayatna & Sutras
│   └── practice_items.json     # 18 curated minimal pairs, words, and shlokas
├── static/
│   ├── css/
│   │   └── style.css           # Saffron/cream palette, Devanagari styling
│   └── js/
│       ├── api.js              # REST client
│       ├── audio.js            # MediaRecorder & SpeechSynthesis engine
│       ├── sthana_diagram.js   # Interactive SVG vocal tract diagram & animations
│       ├── practice.js         # Practice controller
│       └── dashboard.js        # Chart.js analytics controller
├── templates/
│   ├── base.html               # Shared layout & navbar
│   ├── index.html              # Home page & session setup
│   ├── practice.html           # Main practice console & results
│   └── dashboard.html          # Student learning curve & analytics
└── README.md                   # Full documentation & 2-minute demo script
```

---

## 🏛️ Grounded in Pāṇinīya Śikṣā

> **अकुहविसर्जनीयानां कण्ठः** — Kaṇṭha (Throat / Velum)  
> **इचुयशानां तालु** — Tālu (Hard Palate)  
> **ऋटुरषाणां मूर्धा** — Mūrdhā (Roof / Retroflex)  
> **ऌतुलसानां दन्ताः** — Danta (Upper Teeth / Dental)  
> **उपूपध्मानीयानामोष्ठौ** — Oṣṭha (Lips / Labial)  
> **ञमङणननां नासिका च** — Nāsikā (Nasal Cavity)  
