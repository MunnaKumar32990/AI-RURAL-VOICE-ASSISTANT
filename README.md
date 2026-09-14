<div align="center">

# 🌾 Gram Vaani
### AI Voice Assistant for Rural India

**Gram Vaani is an AI-powered voice assistant designed to bridge the digital and language gap for rural communities in India. It enables farmers and rural users to interact with technology through natural voice conversations in their preferred regional language or dialect — making access to information more accessible, inclusive, and user-friendly.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-blue?logo=react)](https://react.dev/)
[![Azure OpenAI](https://img.shields.io/badge/Azure-OpenAI-0078D4?logo=microsoft-azure)](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb)](https://www.mongodb.com/atlas)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Problem Statement](#problem-statement)
3. [Our Solution](#our-solution)
4. [Why This Matters for Rural India](#why-this-matters-for-rural-india)
5. [Key Features](#key-features)
6. [How It Works](#how-it-works)
7. [System Architecture](#system-architecture)
8. [Technologies Used](#technologies-used)
9. [Regional Language & Dialect Support](#regional-language--dialect-support)
10. [Use Cases for Farmers](#use-cases-for-farmers)
11. [Project Structure](#project-structure)
12. [Installation](#installation)
13. [Environment Variables](#environment-variables)
14. [How to Run](#how-to-run)
15. [Example Voice Interactions](#example-voice-interactions)
16. [API Reference](#api-reference)
17. [Future Improvements](#future-improvements)
18. [Challenges & Limitations](#challenges--limitations)
19. [Contributing](#contributing)
20. [License](#license)

---

## 📖 Project Overview

Gram Vaani (meaning *"Village Voice"* in Hindi) is a full-stack, voice-first AI assistant built for the 700 million rural Indians who face barriers in accessing digital information due to language and literacy constraints.

It allows farmers and rural residents to:
- **Speak naturally** in their regional language or dialect
- **Ask questions** about farming, weather, crop prices, and government schemes
- **Hear responses** spoken back in their language with text-to-speech
- **Access critical agricultural information** without needing to read or type

---

## 🔴 Problem Statement

Rural India faces a critical **digital-language divide**:

- **65%+ of India's population** lives in rural areas with limited English proficiency
- Most digital services — government portals, weather apps, market price tools — are in English or formal Hindi
- Farmers lose income due to **lack of timely information** about weather, crop prices, and schemes
- Low digital literacy means traditional apps are inaccessible
- Regional dialects (Bhojpuri, Marathi, Bengali, Telugu, Tamil, etc.) are rarely supported by existing AI tools

The result: millions of farmers make decisions without access to the information that could protect their livelihoods.

---

## ✅ Our Solution

Gram Vaani eliminates these barriers with a **voice-first AI pipeline**:

1. 🎤 **User speaks** in their regional language (Hindi, Telugu, Marathi, Bengali, Tamil, etc.)
2. 🔤 **Azure Whisper** converts speech to text with regional language support
3. 🌐 **Translation layer** converts regional language input to English for processing
4. 🤖 **Azure GPT-3.5** generates accurate, contextual, farmer-friendly responses
5. 🌐 **Translation back** converts the English response to the user's language
6. 🔊 **Azure Text-to-Speech** speaks the answer back in the user's language
7. 📱 The user **hears and reads** the answer in their preferred language

---

## 🌍 Why This Matters for Rural India

| Challenge | Gram Vaani Solution |
|-----------|-------------------|
| English-only services | Supports 9 Indian languages + dialects |
| Low digital literacy | Voice-first — no typing or reading required |
| Complex government portals | Simple conversational AI explains schemes |
| No real-time weather tools | Live weather data with farming context |
| Market price uncertainty | Indicative crop prices based on MSP |
| Poor connectivity | Lightweight frontend, optimised payloads |

---

## ⭐ Key Features

### 🗣️ Voice-First Interaction
- Press a single large button and speak naturally
- No typing, no complex menus
- Auto-plays the spoken response

### 🌐 Multi-Language Support
- Supports **9 Indian languages**: Hindi, Marathi, Bengali, Tamil, Telugu, Gujarati, Kannada, Punjabi, Odia
- Automatic **translate → respond → translate** pipeline
- Correct native scripts (Devanagari, Bengali, Tamil, Telugu, Gurmukhi, etc.)

### 🌤️ Real-Time Weather
- Live weather data via OpenWeatherMap
- Temperature, humidity, wind speed
- Read out in the user's language

### 💰 Crop Price Information
- Indicative prices for 23+ crops (wheat, rice, cotton, mustard, etc.)
- Based on government MSP data
- Guidance to verify at agmarknet.nic.in

### 🏛️ Government Scheme Information
- AI-generated plain-language explanations of:
  - PM-KISAN
  - Pradhan Mantri Fasal Bima Yojana (crop insurance)
  - Soil Health Card Scheme
  - Kisan Credit Card
  - And any other scheme the user asks about

### 👤 User Accounts & Personalization
- Email-based signup/login with JWT authentication
- Location-aware AI responses (GPS auto-detection)
- Preferred language saved to profile
- Full query history in the Profile dashboard

### 📊 Query History Dashboard
- View all past questions and answers
- Statistics: total queries, this week's queries
- Query type breakdown (voice, text, weather, crop, schemes)

---

## ⚙️ How It Works

### Voice Input Flow

```
User presses Mic → Browser records audio (MediaRecorder API) → WAV blob created
  → POST /process-audio (with JWT token) → Backend saves to temp file
  → Azure Whisper transcribes audio to text (with regional language hint)
  → If non-English: GPT-3.5 translates to English
  → GPT-3.5 generates farming-focused response (with user location context)
  → If non-English: GPT-3.5 translates response back to user's language
  → Azure TTS synthesizes speech from response text → base64 WAV returned
  → Frontend decodes audio → auto-plays response → shows text on screen
```

### Text Input Flow

```
User types question → POST /process-text → same translate/respond/translate pipeline
  → AI response returned with TTS audio
```

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────┐
│                   FRONTEND (React + Vite)            │
│                                                      │
│  Auth    ──────────────┐                             │
│  App (Voice/Text)  ────┼──→  Axios HTTP calls        │
│  Profile Dashboard ────┘                             │
└──────────────────────────┬───────────────────────────┘
                           │ HTTP (JWT Bearer Token)
                           ▼
┌──────────────────────────────────────────────────────┐
│               BACKEND (FastAPI / Python)             │
│                                                      │
│  /api/signup, /api/login  ──→  MongoDB Atlas         │
│  /process-audio           ──→  Azure Whisper (STT)   │
│                           ──→  Azure GPT-3.5 (AI)    │
│                           ──→  Azure TTS             │
│  /process-text            ──→  Azure GPT-3.5 + TTS   │
│  /api/weather             ──→  OpenWeatherMap API     │
│  /api/crop-prices         ──→  MSP data (indicative) │
│  /api/gov-schemes         ──→  Azure GPT-3.5 (AI)    │
│  /api/reverse-geocode     ──→  OpenStreetMap Nominatim│
└──────────────────────────────────────────────────────┘
```

---

## 🛠️ Technologies Used

### Backend
| Technology | Purpose |
|---|---|
| **FastAPI** (Python) | High-performance async REST API |
| **Azure OpenAI GPT-3.5** | AI response generation, translation |
| **Azure Whisper** (via Azure OpenAI) | Multi-language speech-to-text |
| **Azure Cognitive Services Speech** | Text-to-speech (TTS) output |
| **MongoDB Atlas** | Cloud database for users & query logs |
| **Motor** | Async MongoDB driver for Python |
| **PyJWT + passlib[bcrypt]** | JWT auth & secure password hashing |
| **OpenWeatherMap API** | Real-time weather data |
| **OSM Nominatim** | Reverse geocoding (GPS → address) |

### Frontend
| Technology | Purpose |
|---|---|
| **React 18** | Component-based UI |
| **Vite** | Fast dev server & bundler |
| **Axios** | HTTP client |
| **Lucide React** | Icon library |
| **MediaRecorder API** | Browser-native audio recording |
| **Web Audio API** | Playback of TTS responses |

---

## 🌐 Regional Language & Dialect Support

Gram Vaani supports the following Indian languages with correct native scripts:

| Code | Language | Script |
|------|----------|--------|
| `hi` | Hindi | Devanagari (हिंदी) |
| `mr` | Marathi | Devanagari (मराठी) |
| `bn` | Bengali | Bengali (বাংলা) |
| `ta` | Tamil | Tamil (தமிழ்) |
| `te` | Telugu | Telugu (తెలుగు) |
| `gu` | Gujarati | Gujarati (ગુજરાતી) |
| `kn` | Kannada | Kannada (ಕನ್ನಡ) |
| `pa` | Punjabi | Gurmukhi (ਪੰਜਾਬੀ) |
| `or` | Odia | Odia (ଓଡ଼ିଆ) |
| `en` | English | Latin |

**How it works for non-English languages:**
1. Azure Whisper transcribes the speech with a language hint
2. GPT-3.5 translates the transcribed text to English
3. GPT-3.5 generates an English response
4. GPT-3.5 translates the response back to the target language in the correct native script

---

## 🌾 Use Cases for Farmers

### 1. Weather & Farming Advice
> *"Aaj mausam kaisa rahega?" (How will the weather be today?)*

The assistant provides real-time weather and contextual farming advice (e.g., whether to water crops, spray pesticide, or harvest).

### 2. Crop Market Prices
> *"Gehun ka bhav kya hai?" (What is the price of wheat?)*

Returns current indicative prices based on MSP data with guidance to verify at the local mandi.

### 3. Government Schemes
> *"PM Kisan scheme kya hai?" (What is PM Kisan scheme?)*

Explains eligibility, benefits, how to apply, and contact helplines in simple language.

### 4. Farming Advice
> *"Tomato mein kaunsa khad dalna chahiye?" (What fertilizer should I use for tomato?)*

GPT-3.5 provides practical, location-aware farming advice.

### 5. Pest & Disease Queries
> *"Meri fasal ki pattiyan peeli ho rahi hain." (My crop leaves are turning yellow.)*

AI diagnoses likely causes and recommends actions.

---

## 📁 Project Structure

```
GRAM VAANI 3.0/
├── backend/                    # FastAPI backend
│   ├── main.py                 # All API endpoints & business logic
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Environment variables template
│   └── venv/                   # Python virtual environment (not in git)
│
├── frontend/                   # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx             # Main app: voice/text interface
│   │   ├── Auth.jsx            # Login & signup screens
│   │   ├── Profile.jsx         # User profile & query history
│   │   ├── index.css           # All styling
│   │   └── main.jsx            # React entry point
│   ├── index.html              # HTML shell
│   ├── vite.config.js          # Vite configuration
│   ├── package.json            # Node.js dependencies
│   └── .env                    # Frontend env (VITE_API_URL)
│
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

---

## 🚀 Installation

### Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **pip** (Python package manager)
- **npm** (Node package manager)

### Required External Services
You need accounts and API keys for:

| Service | Purpose | Free Tier? |
|---------|---------|-----------|
| [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service) | GPT-3.5 + Whisper STT | Paid |
| [Azure Cognitive Services Speech](https://azure.microsoft.com/en-us/products/ai-services/speech-to-text) | Text-to-Speech | Free tier available |
| [MongoDB Atlas](https://www.mongodb.com/atlas) | Cloud database | Free tier (512MB) |
| [OpenWeatherMap](https://openweathermap.org/api) | Weather data | Free (60 calls/min) |

---

## 🔑 Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in your values:

```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://YOUR_RESOURCE.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_DEPLOYMENT=gpt-35-turbo
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Azure Speech Services
AZURE_SPEECH_KEY=your_speech_key_here
AZURE_SPEECH_REGION=eastus

# MongoDB Atlas
MONGO_URL=mongodb+srv://user:password@cluster.mongodb.net/gramvani?retryWrites=true&w=majority

# OpenWeatherMap
OPENWEATHER_API_KEY=your_openweather_key_here

# JWT Secret (generate with: python -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET_KEY=your_strong_random_secret_here

# CORS (optional)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

> ⚠️ **Never commit your `.env` file to git.** It is already in `.gitignore`.

---

## ▶️ How to Run

### Step 1: Backend Setup

```bash
# Navigate to backend
cd "GRAM VAANI 3.0/backend"

# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
copy .env.example .env
# Edit .env with your actual API keys

# Start the backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at: **http://localhost:8000**  
Interactive API docs: **http://localhost:8000/docs**

### Step 2: Frontend Setup (new terminal)

```bash
# Navigate to frontend
cd "GRAM VAANI 3.0/frontend"

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at: **http://localhost:3000**

### Step 3: Open the App

1. Open **http://localhost:3000** in your browser
2. Click **Sign Up** and create an account
3. Allow microphone permissions when prompted
4. Select your preferred language
5. Click the 🎤 microphone button and ask your question!

---

## 💬 Example Voice Interactions

### 🌤️ Weather Query
**User speaks (Hindi):** *"Aaj Delhi mein mausam kaisa hai?"*  
**Gram Vaani responds (Hindi):** *"Delhi mein aaj ka mausam: Aasaman saaf hai. Taapman 28°C hai, aardrata 65% aur hawa ki gati 3 meter per second hai."*

### 🌾 Crop Price Query
**User speaks (Telugu):** *"Maa vellu gadda dhara enti?"*  
**Gram Vaani responds (Telugu):** *"Onion (Gadda) ki Delhi market lo sanketika dhara prasamgika rupees 800 per quintal ga undi. Actual dhara ki agmarknet.nic.in check cheyyandi."*

### 🏛️ Government Scheme Query
**User speaks (English):** *"Tell me about PM Kisan scheme"*  
**Gram Vaani responds:** *"PM-KISAN (Pradhan Mantri Kisan Samman Nidhi) provides ₹6,000 per year to eligible farmer families in 3 installments of ₹2,000 each. Eligibility: All landholding farmer families. To apply: Visit your nearest Common Service Centre (CSC) or go to pmkisan.gov.in. Helpline: 155261 / 1800-115-526."*

### 🌱 Farming Advice
**User speaks (Hindi):** *"Gehu ki fasal mein paani kitni baar dena chahiye?"*  
**Gram Vaani responds (Hindi):** *"Gehun ki fasal ko aam taur par 4-6 baar sinchai ki zaroorat hoti hai. Pehli sinchai buwai ke 20-25 din baad, doosri tillering ke waqt, teesri jointing par, chauthi flowering par, paanchvi doodh bharne ki awastha mein aur chhattha grain filling ke samay karein."*

---

## 📡 API Reference

The backend API is fully documented at `http://localhost:8000/docs` (Swagger UI).

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/` | GET | No | Health check |
| `/api/signup` | POST | No | Register new user |
| `/api/login` | POST | No | Login and get JWT token |
| `/api/me` | GET | Yes | Get current user profile |
| `/api/profile` | PUT | Yes | Update user profile |
| `/api/user-queries` | GET | Yes | Fetch query history |
| `/api/location` | GET | No | Auto-detect location via IP |
| `/api/reverse-geocode` | POST | No | GPS coords → address |
| `/process-audio` | POST | Yes | Voice → AI response + TTS |
| `/process-text` | POST | Yes | Text → AI response + TTS |
| `/api/weather` | POST | Yes | Get weather for a city |
| `/api/crop-prices` | POST | Yes | Get indicative crop price |
| `/api/gov-schemes` | POST | Yes | AI info on govt schemes |

---

## 🔮 Future Improvements

### Near-Term
- [ ] **WhatsApp integration** — Allow farmers to interact via WhatsApp message/voice note
- [ ] **SMS fallback** — For users without smartphones (feature phone / USSD)
- [ ] **Offline mode** — Cache responses and work without internet
- [ ] **Live mandi prices** — Integrate with Agmarknet API for real-time prices
- [ ] **Voice name selection** — Let users choose male/female voice for TTS

### Medium-Term
- [ ] **Dialect support** — Bhojpuri, Awadhi, Chhattisgarhi, Konkani, Maithili
- [ ] **Crop disease detection** — Upload a photo of the crop for AI diagnosis
- [ ] **Soil health advice** — Integrate soil health card data
- [ ] **Calendar/reminder** — Reminders for sowing seasons and scheme deadlines
- [ ] **Community Q&A** — Farmers sharing and rating helpful answers

### Long-Term
- [ ] **Progressive Web App (PWA)** — Install on phone home screen
- [ ] **Kisan Call Centre integration** — Escalate to human expert if needed
- [ ] **Multi-modal** — Support image and document uploads
- [ ] **Regional AI models** — Fine-tuned models on agriculture-specific data

---

## ⚠️ Challenges & Limitations

| Challenge | Current Status |
|-----------|---------------|
| **Crop prices** | Indicative only (based on MSP). No live mandi API integrated yet. |
| **TTS voice quality** | Azure TTS is used; voice quality for regional languages varies. |
| **Dialect variation** | Whisper handles major languages well; rural dialects (Bhojpuri, etc.) may have lower accuracy. |
| **Azure Speech dependency** | If Azure Speech key is not configured, TTS is disabled (text-only responses). |
| **Translation quality** | GPT-3.5 translation is generally good but may occasionally produce slightly unnatural phrasing. |
| **Internet dependency** | All AI features require active internet. No offline fallback currently. |
| **Rate limits** | Azure OpenAI has token/request limits; high concurrent usage may be throttled. |

---

## 🤝 Contributing

Contributions are welcome! This project aims to help rural India, and community contributions are valuable.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Test thoroughly
5. Commit: `git commit -m "Add: your feature description"`
6. Push: `git push origin feature/your-feature-name`
7. Open a Pull Request

**Areas where contributions are especially welcome:**
- Additional regional language support
- Better farming knowledge in the AI prompts
- Real mandi price API integration
- UI/UX improvements for low-literacy users
- WhatsApp or SMS integration

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Gram Vaani** — *Bridging the digital dialect divide, one voice at a time.* 🌾🤖

*Built with ❤️ for the farmers of India*

</div>