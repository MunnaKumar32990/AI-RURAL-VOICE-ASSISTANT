"""
Gram Vaani – AI Voice Assistant for Rural India
Backend API (FastAPI)

Environment variables required (set in backend/.env):
    MONGO_URL                  – MongoDB Atlas connection string
    AZURE_OPENAI_ENDPOINT      – Azure OpenAI service endpoint
    AZURE_OPENAI_API_KEY       – Azure OpenAI API key
    AZURE_OPENAI_DEPLOYMENT    – Deployment name (e.g. gpt35 or gpt-4o)
    AZURE_OPENAI_API_VERSION   – API version (e.g. 2024-12-01-preview)
    AZURE_SPEECH_KEY           – Azure Cognitive Services Speech key
    AZURE_SPEECH_REGION        – Azure Speech region (e.g. eastus)
    OPENWEATHER_API_KEY        – OpenWeatherMap API key
    JWT_SECRET_KEY             – Strong random secret for JWT signing
    ALLOWED_ORIGINS            – Comma-separated frontend URLs (optional)
"""

import os
import logging
import base64
import random
import tempfile
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from openai import AzureOpenAI
import requests
import azure.cognitiveservices.speech as speechsdk
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import jwt

# -----------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)
logger = logging.getLogger("gram_vaani")

# -----------------------------------------------------------------------
# Load environment variables from .env file
# -----------------------------------------------------------------------
load_dotenv()


def _require_env(name: str) -> str:
    """Read an environment variable; warn if missing."""
    value = os.getenv(name, "")
    if not value:
        logger.warning(
            f"Environment variable '{name}' is not set. "
            "Copy backend/.env.example → backend/.env and fill in your values."
        )
    return value


MONGO_URL           = _require_env("MONGO_URL")
AZURE_ENDPOINT      = _require_env("AZURE_OPENAI_ENDPOINT")
AZURE_API_KEY       = _require_env("AZURE_OPENAI_API_KEY")
AZURE_DEPLOYMENT    = _require_env("AZURE_OPENAI_DEPLOYMENT")
AZURE_API_VERSION   = _require_env("AZURE_OPENAI_API_VERSION")
AZURE_SPEECH_KEY    = _require_env("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = _require_env("AZURE_SPEECH_REGION")
OPENWEATHER_KEY     = _require_env("OPENWEATHER_API_KEY")
JWT_SECRET_KEY      = _require_env("JWT_SECRET_KEY")

if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is not set. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# -----------------------------------------------------------------------
# FastAPI app & CORS
# -----------------------------------------------------------------------
app = FastAPI(
    title="Gram Vaani API",
    description="AI Voice Assistant for Rural India",
    version="1.0.0",
)

_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------
# MongoDB
# -----------------------------------------------------------------------
_mongo_client = AsyncIOMotorClient(MONGO_URL) if MONGO_URL else None
_db = _mongo_client.gramvani if _mongo_client else None
users_collection = _db.user if _db else None
user_queries_collection = _db.user_queries if _db else None
logger.info("MongoDB client initialized.")

# -----------------------------------------------------------------------
# Azure OpenAI
# -----------------------------------------------------------------------
azure_client = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_key=AZURE_API_KEY,
    api_version=AZURE_API_VERSION,
)

# -----------------------------------------------------------------------
# Azure Speech (TTS)
# -----------------------------------------------------------------------
def _make_speech_config():
    if AZURE_SPEECH_KEY and AZURE_SPEECH_REGION:
        return speechsdk.SpeechConfig(
            subscription=AZURE_SPEECH_KEY,
            region=AZURE_SPEECH_REGION,
        )
    logger.warning("Azure Speech credentials not set – TTS responses will be text-only.")
    return None

speech_config = _make_speech_config()

# -----------------------------------------------------------------------
# Security / JWT
# -----------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()



# -----------------------------------------------------------------------
# Language helpers
# -----------------------------------------------------------------------
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi (हिंदी)",
    "mr": "Marathi (मराठी)",
    "bn": "Bengali (বাংলা)",
    "ta": "Tamil (தமிழ்)",
    "te": "Telugu (తెలుగు)",
    "gu": "Gujarati (ગુજરાતી)",
    "kn": "Kannada (ಕನ್ನಡ)",
    "pa": "Punjabi (ਪੰਜਾਬੀ)",
    "or": "Odia (ଓଡ଼ିଆ)",
}

SCRIPT_INSTRUCTIONS = {
    "hi": "Translate to Hindi using Devanagari script only (हिंदी). Do NOT use Arabic/Urdu script.",
    "te": "Translate to Telugu using Telugu script only (తెలుగు).",
    "mr": "Translate to Marathi using Devanagari script only (मराठी).",
    "bn": "Translate to Bengali using Bengali script only (বাংলা).",
    "ta": "Translate to Tamil using Tamil script only (தமிழ்).",
    "gu": "Translate to Gujarati using Gujarati script only (ગુજરાતી).",
    "kn": "Translate to Kannada using Kannada script only (ಕನ್ನಡ).",
    "pa": "Translate to Punjabi using Gurmukhi script only (ਪੰਜਾਬੀ).",
    "or": "Translate to Odia using Odia script only (ଓଡ଼ିଆ).",
}


def get_language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, "English")


def get_translate_instruction(lang_code: str) -> str:
    if lang_code in SCRIPT_INSTRUCTIONS:
        return SCRIPT_INSTRUCTIONS[lang_code] + " Only provide the translation, nothing else."
    name = get_language_name(lang_code)
    return f"Translate to {name} using proper native script. Only provide the translation, nothing else."


# -----------------------------------------------------------------------
# TTS helper
# -----------------------------------------------------------------------
def synthesize_speech(text: str) -> Optional[str]:
    """Convert text to speech using Azure TTS. Returns base64-encoded WAV or None."""
    if not speech_config:
        return None
    try:
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        result = synthesizer.speak_text_async(text).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return base64.b64encode(result.audio_data).decode("utf-8")
        logger.warning(f"TTS synthesis incomplete: reason={result.reason}")
    except Exception as exc:
        logger.error(f"TTS error: {exc}")
    return None


# -----------------------------------------------------------------------
# AI response builder – translate → respond → translate for non-English
# -----------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are Gram Vaani, an AI voice assistant for rural India. "
    "You help farmers and rural residents with farming advice, weather interpretation, "
    "crop information, government agricultural schemes, soil health, pest control, "
    "irrigation tips, and general rural livelihood queries. "
    "The user is located in {location}. "
    "Give concise, practical, easy-to-understand answers. "
    "Avoid technical jargon. Keep responses short and conversational – like a helpful neighbour."
)


def build_ai_response(user_text: str, language: str, user_location: str) -> str:
    """Generate an AI response. Uses translate → respond → translate for non-English languages."""
    system_prompt = SYSTEM_PROMPT.format(location=user_location or "India")

    if language == "en":
        resp = azure_client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            max_tokens=800,
            temperature=0.7,
        )
        return resp.choices[0].message.content

    # Step 1: Translate user input to English
    t1 = azure_client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=[
            {"role": "system", "content": "Translate the following text to English. Only provide the translation, nothing else."},
            {"role": "user", "content": user_text},
        ],
        max_tokens=500,
        temperature=0.2,
    )
    english_input = t1.choices[0].message.content.strip()

    # Step 2: Get English response
    t2 = azure_client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": english_input},
        ],
        max_tokens=800,
        temperature=0.7,
    )
    english_answer = t2.choices[0].message.content

    # Step 3: Translate response to target language
    t3 = azure_client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=[
            {"role": "system", "content": get_translate_instruction(language)},
            {"role": "user", "content": english_answer},
        ],
        max_tokens=800,
        temperature=0.2,
    )
    return t3.choices[0].message.content.strip()


# -----------------------------------------------------------------------
# Query logging
# -----------------------------------------------------------------------
async def log_user_query(
    user_email: str,
    query: str,
    response: str = None,
    query_type: str = "general",
):
    """Silently log a user query to MongoDB. Errors are non-fatal."""
    try:
        await user_queries_collection.insert_one({
            "user_email": user_email,
            "query": query,
            "response": response,
            "type": query_type,
            "timestamp": datetime.utcnow(),
        })
    except Exception as exc:
        logger.warning(f"Query logging failed: {exc}")


# -----------------------------------------------------------------------
# Security helpers
# -----------------------------------------------------------------------
def _normalize_password_for_bcrypt(password: str) -> str:
    """Truncate to 72 UTF-8 bytes to avoid bcrypt overflow."""
    encoded = password.encode("utf-8", errors="ignore")
    if len(encoded) > 72:
        password = encoded[:72].decode("utf-8", errors="ignore")
    return password


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(_normalize_password_for_bcrypt(plain), hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(_normalize_password_for_bcrypt(password))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        user = await users_collection.find_one({"email": email})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found.")
        return user
    except jwt.PyJWTError as exc:
        logger.warning(f"JWT error: {exc}")
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Auth error: {exc}")
        raise HTTPException(status_code=401, detail="Authentication failed.")


# ======================================================================
# PYDANTIC MODELS
# ======================================================================

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    language: str = "en"
    location: str
    coordinates: Optional[dict] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ReverseGeocodeRequest(BaseModel):
    latitude: float
    longitude: float

class ProfileUpdate(BaseModel):
    email: EmailStr
    language: str
    location: str

class QueryLog(BaseModel):
    query: str
    response: Optional[str] = None
    type: str = "general"

class TextRequest(BaseModel):
    text: str
    language: str = "en"

class WeatherRequest(BaseModel):
    city: str
    language: str = "en"

class CropPriceRequest(BaseModel):
    crop: str
    market: str = "Delhi"
    language: str = "en"

class SchemeRequest(BaseModel):
    topic: str
    language: str = "en"


# ======================================================================
# LOCATION ENDPOINTS
# ======================================================================

@app.get("/api/location", summary="Auto-detect location via server IP")
async def get_location():
    """Detect approximate location from IP using ipapi.co (free, no key required)."""
    try:
        resp = requests.get("https://ipapi.co/json/", timeout=8)
        data = resp.json()
        if resp.status_code == 200 and not data.get("error"):
            city = data.get("city") or ""
            region = data.get("region") or ""
            parts = [p for p in [city, region] if p]
            return {
                "city": city,
                "region": region,
                "country": data.get("country_name", ""),
                "location": ", ".join(parts) if parts else None,
            }
    except Exception as exc:
        logger.warning(f"IP location detection failed: {exc}")
    return {"location": None}


@app.post("/api/reverse-geocode", summary="Convert GPS coordinates to address")
async def reverse_geocode(request: ReverseGeocodeRequest):
    """Reverse geocode GPS coordinates using OpenStreetMap Nominatim (free service)."""
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": request.latitude, "lon": request.longitude, "format": "json", "addressdetails": 1},
            headers={"User-Agent": "GramVaani/1.0 (rural-ai-assistant)"},
            timeout=10,
        )
        data = resp.json()
        if resp.status_code == 200 and "address" in data:
            addr = data["address"]
            village  = addr.get("village", "")
            town     = addr.get("town", "")
            city     = addr.get("city", "")
            district = addr.get("state_district", "")
            state    = addr.get("state", "")
            postcode = addr.get("postcode", "")
            locality = village or town or city
            parts = [p for p in [locality, district, state, postcode] if p]
            address_str = ", ".join(parts)
            return {
                "address": address_str,
                "location": address_str,
                "coordinates": {"latitude": request.latitude, "longitude": request.longitude},
                "details": {
                    "village": village, "town": town, "city": city,
                    "district": district, "state": state, "postcode": postcode,
                },
            }
    except Exception as exc:
        logger.warning(f"Reverse geocoding failed: {exc}")
    fallback = f"{request.latitude:.4f}, {request.longitude:.4f}"
    return {"address": fallback, "location": fallback}


# ======================================================================
# AUTH ENDPOINTS
# ======================================================================

@app.post("/api/signup", response_model=Token, summary="Register a new user account")
async def signup(user: UserSignup):
    if len(user.password.encode("utf-8", errors="ignore")) > 512:
        raise HTTPException(status_code=400, detail="Password is too long.")
    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")
    try:
        await users_collection.insert_one({
            "email": user.email,
            "password": hash_password(user.password),
            "language": user.language,
            "location": user.location,
            "coordinates": user.coordinates,
            "created_at": datetime.utcnow(),
        })
        logger.info(f"New user registered: {user.email}")
    except Exception as exc:
        err = str(exc)
        if "duplicate key" in err.lower() or "11000" in err:
            raise HTTPException(status_code=400, detail="Email already registered.")
        logger.error(f"Signup DB error: {exc}")
        raise HTTPException(status_code=500, detail="Registration failed. Please try again.")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/api/login", response_model=Token, summary="Login with email and password")
async def login(user: UserLogin):
    if len(user.password.encode("utf-8", errors="ignore")) > 512:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    try:
        valid = verify_password(user.password, db_user["password"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/me", summary="Get current user's profile")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "email": current_user["email"],
        "language": current_user.get("language", "en"),
        "location": current_user.get("location", ""),
    }


@app.put("/api/profile", summary="Update current user's profile")
async def update_profile(data: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    try:
        await users_collection.update_one(
            {"email": current_user["email"]},
            {"$set": {
                "email": data.email,
                "language": data.language,
                "location": data.location,
                "updated_at": datetime.utcnow(),
            }},
        )
        return {"message": "Profile updated successfully."}
    except Exception as exc:
        logger.error(f"Profile update error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to update profile.")


@app.post("/api/log-query", summary="Manually log a query")
async def log_query(query_data: QueryLog, current_user: dict = Depends(get_current_user)):
    await log_user_query(current_user["email"], query_data.query, query_data.response, query_data.type)
    return {"message": "Query logged."}


@app.get("/api/user-queries", summary="Fetch last 50 queries for current user")
async def get_user_queries(current_user: dict = Depends(get_current_user)):
    try:
        queries = await user_queries_collection.find(
            {"user_email": current_user["email"]}
        ).sort("timestamp", -1).limit(50).to_list(50)
        for q in queries:
            q["_id"] = str(q["_id"])
        return {"queries": queries}
    except Exception as exc:
        logger.error(f"Fetch queries error: {exc}")
        return {"queries": []}


# ======================================================================
# VOICE / AUDIO PROCESSING
# ======================================================================

@app.post("/process-audio", summary="Transcribe voice and return AI response with TTS")
async def process_audio(
    file: UploadFile = File(...),
    language: str = "en",
    current_user: dict = Depends(get_current_user),
):
    """
    Full voice pipeline:
    1. Save uploaded audio to temp file
    2. Transcribe using Azure Whisper
    3. Generate AI response (with translation for non-English)
    4. Synthesize TTS audio
    5. Return transcript + text response + base64 audio
    """
    temp_file_path = None
    try:
        content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(content)
            temp_file_path = tmp.name
        logger.info(f"Audio received: {len(content)} bytes, language={language}")

        # --- Speech-to-Text ---
        transcript = None
        whisper_lang_map = {
            "hi": "hi", "mr": "mr", "bn": "bn", "ta": "ta",
            "te": "te", "gu": "gu", "kn": "kn", "pa": "pa", "or": "or",
        }
        try:
            with open(temp_file_path, "rb") as audio_file:
                stt = azure_client.audio.transcriptions.create(
                    model="whisper",
                    file=audio_file,
                    language=whisper_lang_map.get(language) if language != "en" else None,
                )
            transcript = stt.text.strip()
            logger.info(f"Transcript: {transcript}")
        except Exception as exc:
            logger.warning(f"Whisper STT failed: {exc}")

        if not transcript:
            msg = (
                "I couldn't understand your audio. "
                "Please speak clearly, reduce background noise, and try again."
            )
            await log_user_query(current_user["email"], "[audio – transcription failed]", msg, "voice")
            return JSONResponse({"transcript": "", "response_text": msg, "audio_data": None})

        # --- AI Response ---
        user_location = current_user.get("location", "India")
        try:
            response_text = build_ai_response(transcript, language, user_location)
        except Exception as exc:
            logger.error(f"AI response error: {exc}")
            response_text = (
                "I'm here to help you with farming, weather, and government schemes. "
                "Please try again in a moment."
            )

        await log_user_query(current_user["email"], transcript, response_text, "voice")

        return JSONResponse({
            "transcript": transcript,
            "response_text": response_text,
            "audio_data": synthesize_speech(response_text),
        })

    except Exception as exc:
        logger.error(f"process_audio unexpected error: {exc}")
        return JSONResponse({
            "transcript": "",
            "response_text": "I'm having trouble processing your audio. Please try again later.",
            "audio_data": None,
        })
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


# ======================================================================
# TEXT PROCESSING
# ======================================================================

@app.post("/process-text", summary="Process a text query and return AI response with TTS")
async def process_text(request: TextRequest, current_user: dict = Depends(get_current_user)):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text input cannot be empty.")
    user_location = current_user.get("location", "India")
    try:
        response_text = build_ai_response(request.text, request.language, user_location)
    except Exception as exc:
        logger.error(f"process_text AI error: {exc}")
        raise HTTPException(status_code=500, detail="AI service unavailable. Please try again.")
    await log_user_query(current_user["email"], request.text, response_text, "text")
    return JSONResponse({
        "response_text": response_text,
        "audio_data": synthesize_speech(response_text),
    })


# ======================================================================
# WEATHER
# ======================================================================

@app.post("/api/weather", summary="Get current weather for a city with TTS")
async def get_weather(request: WeatherRequest, current_user: dict = Depends(get_current_user)):
    if not OPENWEATHER_KEY:
        raise HTTPException(status_code=503, detail="Weather service is not configured. Set OPENWEATHER_API_KEY.")
    try:
        res = requests.get(
            "http://api.openweathermap.org/data/2.5/weather",
            params={"q": request.city, "appid": OPENWEATHER_KEY, "units": "metric", "lang": request.language},
            timeout=8,
        )
        data = res.json()
        if res.status_code != 200:
            raise HTTPException(status_code=400, detail=data.get("message", "City not found."))
        desc     = data["weather"][0]["description"].capitalize()
        temp     = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind     = data["wind"]["speed"]
        response_text = (
            f"Current weather in {request.city}: {desc}. "
            f"Temperature: {temp}°C. Humidity: {humidity}%. Wind speed: {wind} m/s."
        )
        await log_user_query(current_user["email"], f"Weather: {request.city}", response_text, "weather")
        return JSONResponse({"text": response_text, "audio_data": synthesize_speech(response_text)})
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Weather API error: {exc}")
        raise HTTPException(status_code=500, detail="Unable to fetch weather data right now.")


# ======================================================================
# CROP PRICES  (indicative prices – not a live mandi API)
# ======================================================================

# MSP / approximate prices (₹ per quintal) — update periodically
CROP_BASE_PRICES = {
    "wheat": 2275, "rice": 2183, "paddy": 2183, "maize": 1962,
    "cotton": 6620, "sugarcane": 315, "soybean": 4600, "groundnut": 5850,
    "onion": 800, "potato": 750, "tomato": 1200, "mustard": 5650,
    "gram": 5440, "dal": 6200, "bajra": 2350, "jowar": 3371,
    "sunflower": 6760, "sesame": 8635, "moong": 8558, "urad": 7400,
    "arhar": 7000, "lentil": 6425, "barley": 1735,
}


@app.post("/api/crop-prices", summary="Get indicative crop price for a crop")
async def get_crop_prices(request: CropPriceRequest, current_user: dict = Depends(get_current_user)):
    crop_lower = request.crop.strip().lower()
    base = CROP_BASE_PRICES.get(crop_lower, 2000 + abs(hash(crop_lower)) % 1000)
    # Add ±5% variation to simulate market fluctuation
    price = int(base * (0.95 + random.random() * 0.10))
    response_text = (
        f"Indicative price for {request.crop.title()} at {request.market} market: "
        f"approximately ₹{price} per quintal. "
        f"Note: These are indicative prices based on MSP. "
        f"Please verify actual prices at agmarknet.nic.in or your local mandi before selling."
    )
    await log_user_query(current_user["email"], f"Crop price: {request.crop}", response_text, "crop")
    return JSONResponse({"text": response_text, "audio_data": synthesize_speech(response_text)})


# ======================================================================
# GOVERNMENT SCHEMES
# ======================================================================

@app.post("/api/gov-schemes", summary="Get AI-generated information about government schemes")
async def get_gov_schemes(request: SchemeRequest, current_user: dict = Depends(get_current_user)):
    lang_name = get_language_name(request.language)
    script_note = SCRIPT_INSTRUCTIONS.get(request.language, f"Respond in {lang_name}.")
    try:
        resp = azure_client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Gram Vaani, an AI assistant for rural India. "
                        "Provide clear, accurate, and simple information about Indian government agricultural schemes. "
                        "Include: scheme name, eligibility criteria, benefits, how to apply, and helpline if available. "
                        "Keep the response concise and easy to understand for rural farmers. "
                        f"IMPORTANT: {script_note} Do not mix languages."
                    ),
                },
                {"role": "user", "content": f"Tell me about government schemes related to: {request.topic}"},
            ],
            max_tokens=1024,
            temperature=0.6,
        )
        summary = resp.choices[0].message.content
    except Exception as exc:
        logger.error(f"Gov schemes AI error: {exc}")
        raise HTTPException(status_code=500, detail="Unable to fetch scheme information right now.")
    await log_user_query(current_user["email"], f"Schemes: {request.topic}", summary, "schemes")
    return JSONResponse({"text": summary, "audio_data": synthesize_speech(summary)})


# ======================================================================
# HEALTH CHECK
# ======================================================================

@app.get("/", summary="Health check")
async def health_check():
    return {"status": "ok", "service": "Gram Vaani API", "version": "1.0.0"}

