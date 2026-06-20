# BolChaal 🗣️ — Maithili Language Translator

> Translate any language → Maithili, with special support for **Hinglish** (Hindi written in English letters).

---

## Tech Stack

- **Backend**: Python 3.12 + FastAPI + IndicTrans2 (AI4Bharat)
- **Frontend**: Vanilla HTML/CSS/JS (Phase 1), React.js (Phase 2)
- **Models**: `indictrans2-en-indic-dist-200M` + `indictrans2-indic-indic-dist-320M`

---

## Setup Instructions

### Step 1: Activate Virtual Environment

```powershell
# From project root
.\venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies

```powershell
cd backend

# Install main packages (CPU-only PyTorch — smaller download)
pip install -r requirements.txt

# Install IndicTransToolkit (required for preprocessing)
pip install git+https://github.com/VarunGumma/IndicTransToolkit.git

# Install Hinglish transliteration (optional but recommended)
pip install ai4bharat-transliteration
```

### Step 3: Run the Server

```powershell
python main.py
```

Server starts at: `http://localhost:8000`  
API docs at: `http://localhost:8000/docs`

---

## API Reference

### POST `/translate`

Translate text to Maithili.

**Request:**
```json
{
  "text": "How are you?",
  "src_lang": "eng_Latn"
}
```

**Response:**
```json
{
  "original_text": "How are you?",
  "translated_text": "अहाँ कोना छी?",
  "src_lang": "eng_Latn",
  "tgt_lang": "mai_Deva",
  "detected_as": null,
  "time_taken_ms": 2341
}
```

### Hinglish Example

```json
{
  "text": "kaise ho aap",
  "src_lang": "hinglish"
}
```

Response will include `"detected_as": "hin_Deva"`.

### GET `/languages`

Returns all supported source languages.

### GET `/health`

Returns server status.

---

## Supported Languages

| Language | Code |
|:---|:---|
| English | `eng_Latn` |
| **Hinglish** | `hinglish` |
| Hindi | `hin_Deva` |
| Bengali | `ben_Beng` |
| Tamil | `tam_Taml` |
| Telugu | `tel_Telu` |
| Marathi | `mar_Deva` |
| Gujarati | `guj_Gujr` |
| Kannada | `kan_Knda` |
| Malayalam | `mal_Mlym` |
| Punjabi | `pan_Guru` |
| Odia | `ory_Orya` |
| Assamese | `asm_Beng` |

---

## Project Structure

```
Language-Translator/
├── venv/                      # Python virtual environment
├── backend/
│   ├── main.py                # FastAPI server
│   ├── translator.py          # IndicTrans2 wrapper
│   ├── hinglish.py            # Hinglish detection + transliteration
│   ├── config.py              # Language codes & settings
│   └── requirements.txt       # Python dependencies
├── frontend/                  # (Phase 2)
│   ├── index.html
│   ├── styles/main.css
│   └── scripts/app.js
└── README.md
```

---

## Notes

- **First launch** will download models from HuggingFace (~900 MB total). This is a one-time download.
- Models are cached in `~/.cache/huggingface/` automatically.
- Translation takes **2–5 seconds** on CPU (AMD Ryzen 7 7730U). This is normal.
- Keep at least **3 GB RAM free** when running the server.
