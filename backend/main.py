"""
BolChaal - FastAPI Backend Server

Endpoints:
  POST /translate  — Translate text to Maithili
  GET  /languages  — Get list of supported source languages
  GET  /health     — Server health check
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import SUPPORTED_LANGUAGES, TARGET_LANG, HOST, PORT, MAX_TEXT_LENGTH
from translator import Translator
from hinglish import detect_hinglish, transliterate_hinglish_to_hindi

# ─── Logging setup ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("bolchaal")

# ─── Global translator instance ──────────────────────────────────────────────
translator = Translator()


# ─── Lifespan (startup/shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: warm up the model
    logger.info("🚀 BolChaal server starting...")
    logger.info("Loading translation model (this may take 15-30 seconds)...")
    try:
        translator.warmup()
        logger.info("✅ BolChaal is ready! Visit http://localhost:8000/docs")
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")
        logger.warning("Server will start but translations will fail until model is loaded.")
    yield
    # Shutdown
    logger.info("BolChaal server shutting down.")


# ─── FastAPI app ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="BolChaal Translation API",
    description="Any Language → Maithili translation powered by IndicTrans2",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow frontend (HTML file opened in browser) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local dev — fine since this is localhost only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request / Response Models ────────────────────────────────────────────────
class TranslationRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=MAX_TEXT_LENGTH,
        description="The text to translate.",
        json_schema_extra={"example": "How are you doing today?"},
    )
    src_lang: str = Field(
        ...,
        description="Source language code (e.g., 'eng_Latn', 'hin_Deva'). "
                    "For Hindi, both Devanagari and Roman/Hinglish script are auto-detected.",
        json_schema_extra={"example": "eng_Latn"},
    )


class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    src_lang: str
    tgt_lang: str = TARGET_LANG
    detected_as: str | None = None  # Set when Hinglish is detected
    time_taken_ms: int


class LanguageInfo(BaseModel):
    name: str
    code: str


class LanguagesResponse(BaseModel):
    languages: list[LanguageInfo]
    target_language: str = "Maithili"
    target_code: str = TARGET_LANG


# ─── Endpoints ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["Status"])
async def health_check():
    """Check if the server is running."""
    return {
        "status": "online",
        "model_loaded": translator._en_indic_model is not None,
        "app": "BolChaal",
        "version": "1.0.0",
    }


@app.get("/languages", response_model=LanguagesResponse, tags=["Languages"])
async def get_languages():
    """Get all supported source languages."""
    langs = [
        LanguageInfo(name=name, code=code)
        for name, code in SUPPORTED_LANGUAGES.items()
    ]
    return LanguagesResponse(languages=langs)


@app.post("/translate", response_model=TranslationResponse, tags=["Translation"])
async def translate(request: TranslationRequest):
    """
    Translate text from any supported language to Maithili.

    For Hindi (hin_Deva): automatically handles both Devanagari script AND
    Roman/Hinglish script (e.g., 'kaise ho'). No separate Hinglish option needed.
    All other language codes follow FLORES-101 format (e.g., 'eng_Latn').
    """
    start_time = time.time()

    text = request.text.strip()
    src_lang = request.src_lang
    detected_as = None

    if not text:
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    # Validate source language
    valid_codes = set(SUPPORTED_LANGUAGES.values())
    if src_lang not in valid_codes:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported source language: '{src_lang}'. "
                   f"Use GET /languages to see supported options.",
        )

    try:
        # ── Hindi auto-detect: handle Hinglish (Roman-script Hindi) ──────────
        # When the user selects Hindi, they may type in Devanagari OR in Roman
        # script (e.g. "kaise ho"). We detect and auto-transliterate Roman→Devanagari.
        if src_lang == "hin_Deva" and detect_hinglish(text):
            logger.info(f"Hinglish detected in Hindi input: '{text[:50]}'")
            transliterated = transliterate_hinglish_to_hindi(text)
            detected_as = "hinglish"   # tell the frontend what we found
            logger.info(f"Transliterated → '{transliterated[:60]}'")
            text = transliterated      # now treat as proper Devanagari Hindi

        # ── Perform translation ───────────────────────────────────────────────
        logger.info(f"Translating: '{text[:50]}' | {src_lang} → {TARGET_LANG}")
        translated = translator.translate(text, src_lang=src_lang, tgt_lang=TARGET_LANG)

        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Done in {elapsed_ms}ms: '{translated[:60]}'")

        return TranslationResponse(
            original_text=request.text,
            translated_text=translated,
            src_lang=request.src_lang,
            tgt_lang=TARGET_LANG,
            detected_as=detected_as,
            time_taken_ms=elapsed_ms,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Translation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


# ─── Run ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    import sys
    # Force UTF-8 output on Windows console
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("\n" + "=" * 55)
    print("  BolChaal - Maithili Translator")
    print("  Starting server at http://localhost:8000")
    print("  API docs at   http://localhost:8000/docs")
    print("=" * 55 + "\n")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
