"""
BolChaal - Hinglish Detection and Transliteration Module

Handles:
1. Detecting if input is Hinglish (Hindi written in English/Latin script)
2. Transliterating Hinglish → Hindi (Devanagari)

Uses 'indic-transliteration' (pure Python, no C++ required).
Tries multiple romanization schemes and picks the best result.
"""

import re
import logging

logger = logging.getLogger("bolchaal.hinglish")

# ─── Hinglish Signal Words ────────────────────────────────────────────────────
# Common Hindi words written in Roman script. If enough of these appear,
# the text is classified as Hinglish.
HINGLISH_SIGNAL_WORDS = {
    # Pronouns
    "main", "mein", "mai", "tu", "tum", "aap", "hum",
    "yeh", "ye", "woh", "wo", "iska", "uska", "mera", "tera", "humara",
    # Verbs
    "hai", "hain", "ho", "tha", "thi", "the", "hoga", "hogi",
    "karna", "kar", "kiya", "karo", "karein",
    "aana", "aa", "aaya", "aao", "jana", "ja", "gaya", "jao",
    "lena", "le", "liya", "dena", "de", "diya",
    "bolna", "bol", "bola", "bolo",
    "dekhna", "dekh", "dekha", "dekho",
    "sunna", "sun", "suno", "suna",
    "rehna", "reh", "raha", "rahi", "rahe",
    # Question words
    "kya", "kyun", "kyu", "kaise", "kaisa", "kaisi",
    "kab", "kahan", "kahaan", "kaun", "kitna", "kitne", "kitni",
    # Negation / Affirmation
    "nahi", "nahin", "nhi", "mat", "haan", "han", "ji",
    # Common adjectives / adverbs
    "bahut", "bohot", "thoda", "zyada", "accha", "acha", "theek",
    "bura", "sahi", "galat", "naya", "purana", "bada", "chota",
    # Conjunctions
    "aur", "ya", "lekin", "par", "magar", "toh", "bhi", "sirf",
    "phir", "fir", "isliye", "kyonki", "agar", "jab", "jab tak",
    # Time words
    "aaj", "kal", "parson", "abhi", "ab", "pehle", "baad",
    "subah", "shaam", "raat", "din",
    # Greetings
    "namaste", "namaskar", "shukriya", "dhanyawad", "alvida",
    "pyaar", "dost", "yaar", "bhai", "behen",
}

# Words to keep in Latin script — transliterating these would produce garbage
ENGLISH_LOANWORDS = {
    "ok", "okay", "please", "sorry", "thanks", "thank", "welcome",
    "yes", "no", "hi", "hello", "bye",
    "app", "phone", "mobile", "internet", "wifi", "data", "online",
    "google", "facebook", "instagram", "whatsapp", "youtube",
    "office", "school", "college", "class", "exam", "job", "work",
    "message", "msg", "call", "video", "photo", "selfie",
    "download", "upload", "update", "install", "password", "email",
    "movie", "show", "party", "birthday", "gift",
    "doctor", "hospital", "bank", "atm", "hotel", "ticket",
}

# ─── Detection ────────────────────────────────────────────────────────────────

def detect_hinglish(text: str) -> bool:
    """
    Detect if text is Hinglish (Hindi written in Latin/Roman script).

    Returns False if:
    - Text already contains Devanagari → it's proper Hindi
    - Text contains Arabic script → it's Urdu
    - Not enough Hinglish signal words found
    """
    # Already in Devanagari — proper Hindi, nothing to do
    if re.search(r'[\u0900-\u097F]', text):
        return False

    # Arabic/Urdu script
    if re.search(r'[\u0600-\u06FF]', text):
        return False

    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    if not words:
        return False

    matches = sum(1 for w in words if w in HINGLISH_SIGNAL_WORDS)
    ratio = matches / len(words)

    logger.debug(f"Hinglish check: {matches}/{len(words)} signal words ({ratio:.0%})")
    return ratio >= 0.20   # 20% threshold — catches even lightly Hinglish text


# ─── Hinglish Direct Map ──────────────────────────────────────────────────────
# Common informal Hinglish spellings mapped to their standard Devanagari form.
# This prevents transliteration issues like "main" -> "मैन्" or "hun" -> "हुन्".
HINGLISH_DIRECT_MAP = {
    "main": "मैं",
    "mein": "में",
    "mai": "मैं",
    "me": "में",
    "tu": "तू",
    "tum": "तुम",
    "aap": "आप",
    "hum": "हम",
    "ham": "हम",
    "yeh": "यह",
    "ye": "ये",
    "woh": "वह",
    "wo": "वो",
    "hai": "है",
    "hain": "हैं",
    "ho": "हो",
    "tha": "था",
    "thi": "थी",
    "the": "थे",
    "hoga": "होगा",
    "hogi": "होगी",
    "hoge": "होगे",
    "hun": "हूँ",
    "hoon": "हूँ",
    "kya": "क्या",
    "kyun": "क्यों",
    "kyu": "क्यों",
    "kaise": "कैसे",
    "kab": "कब",
    "kahan": "कहाँ",
    "kahaan": "कहाँ",
    "kaun": "कौन",
    "kitna": "कितना",
    "kitne": "कितने",
    "kitni": "कितनी",
    "nahi": "नहीं",
    "nahin": "नहीं",
    "nhi": "नहीं",
    "mat": "मत",
    "haan": "हाँ",
    "han": "हाँ",
    "ji": "जी",
    "bahut": "बहुत",
    "bohot": "बहुत",
    "accha": "अच्छा",
    "acha": "अच्छा",
    "theek": "ठीक",
    "thik": "ठीक",
    "aur": "और",
    "ya": "या",
    "lekin": "लेकिन",
    "par": "पर",
    "magar": "मगर",
    "toh": "तो",
    "to": "तो",
    "bhi": "भी",
    "sirf": "सिर्फ",
    "phir": "फिर",
    "fir": "फिर",
    "isliye": "इसलिए",
    "kyonki": "क्योंकि",
    "agar": "अगर",
    "jab": "जब",
    "aaj": "आज",
    "kal": "कल",
    "abhi": "अभी",
    "ab": "अब",
    "pehle": "पहले",
    "baad": "बाद",
    "subah": "सुबह",
    "shaam": "शाम",
    "raat": "रात",
    "din": "दिन",
    "namaste": "नमस्ते",
    "dost": "दोस्त",
    "yaar": "यार",
    "ko": "को",
    "se": "से",
    "ki": "की",
    "ke": "के",
    "ka": "का",
    "kar": "कर",
    "karo": "करो",
    "raha": "रहा",
    "rahi": "रही",
    "rahe": "रहे",
    "ja": "जा",
    "jaa": "जा",
    "jao": "जाओ",
    "aao": "आओ",
    "aa": "आ",
    "ne": "ने",
    "hi": "ही",
}

# ─── Transliteration ─────────────────────────────────────────────────────────

def transliterate_hinglish_to_hindi(text: str) -> str:
    """
    Convert Hinglish (Roman-script Hindi) to Hindi (Devanagari script).
    
    Uses HINGLISH_DIRECT_MAP for standard words to ensure correct spellings,
    and falls back to ITRANS transliteration with trailing halant stripping
    for out-of-vocabulary words.
    
    Preserves English loanwords in their original Latin form.
    """
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate

        words = text.split()
        result_words = []

        for word in words:
            # Strip punctuation for processing, reattach after
            stripped = re.sub(r'^[^a-zA-Z]+|[^a-zA-Z]+$', '', word)
            prefix_len = len(word) - len(word.lstrip(''.join(
                c for c in word if not c.isalpha()
            )))
            prefix = word[:prefix_len]
            suffix = word[len(prefix) + len(stripped):]

            if not stripped:
                result_words.append(word)  # punctuation/numbers only
            elif stripped.lower() in ENGLISH_LOANWORDS:
                result_words.append(word)  # keep loanword as-is
                logger.debug(f"Kept loanword: '{stripped}'")
            else:
                lower_stripped = stripped.lower()
                # Check dictionary first
                if lower_stripped in HINGLISH_DIRECT_MAP:
                    devanagari = HINGLISH_DIRECT_MAP[lower_stripped]
                else:
                    # Fallback to transliterator
                    devanagari = transliterate(stripped, sanscript.ITRANS, sanscript.DEVANAGARI)
                    # Clean trailing halants (common in informal roman typing)
                    if devanagari.endswith("्") and len(devanagari) > 2:
                        devanagari = devanagari[:-1]

                result_words.append(prefix + devanagari + suffix)

        hindi_text = " ".join(result_words)
        logger.info(f"Transliterated: '{text}' → '{hindi_text}'")
        return hindi_text

    except ImportError:
        logger.warning("indic-transliteration not installed. Returning original text.")
        return text
    except Exception as e:
        logger.error(f"Transliteration failed: {e}")
        return text

