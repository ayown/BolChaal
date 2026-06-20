# BolChaal - Configuration
# Language codes and model settings for IndicTrans2

import os
from dotenv import load_dotenv

load_dotenv()

# ─── HuggingFace Token ────────────────────────────────────────────────────────
# Required to download gated IndicTrans2 models.
# Steps:
#   1. Create free account at https://huggingface.co
#   2. Go to https://huggingface.co/ai4bharat/indictrans2-en-indic-dist-200M
#      and click "Agree and access repository"
#   3. Go to https://huggingface.co/settings/tokens → New token (Read)
#   4. Paste your token in the .env file as HF_TOKEN=your_token
HF_TOKEN = os.environ.get("HF_TOKEN")  # ← Loaded from .env

# Model IDs from HuggingFace
MODELS = {
    "en_indic": "ai4bharat/indictrans2-en-indic-dist-200M",       # English → Indic
    "indic_indic": "ai4bharat/indictrans2-indic-indic-dist-320M",  # Indic → Indic
    "indic_en": "ai4bharat/indictrans2-indic-en-dist-200M",        # Indic → English (fallback)
}

# Always translate TO Maithili
TARGET_LANG = "mai_Deva"

# Supported source languages
# Format: { "display_name": "flores_code" }
SUPPORTED_LANGUAGES = {
    "English":    "eng_Latn",
    "Hindi":      "hin_Deva",    # Also auto-detects Hinglish (Roman-script Hindi)
    "Bengali":    "ben_Beng",
    "Tamil":      "tam_Taml",
    "Telugu":     "tel_Telu",
    "Marathi":    "mar_Deva",
    "Gujarati":   "guj_Gujr",
    "Kannada":    "kan_Knda",
    "Malayalam":  "mal_Mlym",
    "Punjabi":    "pan_Guru",
    "Odia":       "ory_Orya",
    "Assamese":   "asm_Beng",
    "Sanskrit":   "san_Deva",
    "Urdu":       "urd_Arab",
    "Nepali":     "npi_Deva",
    "Maithili":   "mai_Deva",
}

# Languages that need the en-indic model (source = English)
ENGLISH_SOURCE_LANGS = {"eng_Latn"}

# Languages that need indic-indic model (source = any Indic)
INDIC_SOURCE_LANGS = {
    "hin_Deva", "ben_Beng", "tam_Taml", "tel_Telu",
    "mar_Deva", "guj_Gujr", "kan_Knda", "mal_Mlym",
    "pan_Guru", "ory_Orya", "asm_Beng", "san_Deva",
    "urd_Arab", "npi_Deva", "mai_Deva",
}

# Server settings
HOST = "127.0.0.1"
PORT = 8000
MAX_TEXT_LENGTH = 1000  # characters
