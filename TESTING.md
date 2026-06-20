# BolChaal — Testing & Debugging Handbook

> A complete guide for setting up, running, and testing the BolChaal stack.
> The general pattern in [Part 5](#part-5--general-handbook-any-python--js-project) applies to any Python + JavaScript project.

---

## Table of Contents

1. [Environment Setup](#part-1--environment-setup)
2. [Running the Stack](#part-2--running-the-stack)
3. [Systematic Testing](#part-3--systematic-testing)
4. [Debugging Common Issues](#part-4--debugging-common-issues)
5. [General Handbook (Any Python + JS Project)](#part-5--general-handbook-any-python--js-project)

---

## Part 1 — Environment Setup

### 1.1 Check Prerequisites

Open **PowerShell** in `e:\CODES\AI\Language-Translator`:

```powershell
# Must be 3.10 or higher
python --version

# Check pip
python -m pip --version

# Check if venv already exists
Test-Path venv
```

### 1.2 Create & Activate the Virtual Environment

**If starting fresh (no `venv/` folder yet):**

```powershell
python -m venv venv
```

**Activate it — always do this before any work:**

```powershell
# Windows PowerShell
venv\Scripts\Activate.ps1

# If you get an "execution policy" error, run this first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

You'll see a `(venv)` prefix in your prompt when it's active. Every time you open a new terminal, re-activate before running anything.

### 1.3 Install Dependencies

```powershell
cd backend

# CPU-only PyTorch first (saves ~1GB vs the default CUDA build)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Then the rest
pip install -r requirements.txt
```

**Verify everything installed correctly:**

```powershell
pip list | findstr -i "fastapi torch transformers sentencepiece"
```

---

## Part 2 — Running the Stack

### 2.1 Start the Backend

```powershell
# From project root, with venv active
cd e:\CODES\AI\Language-Translator\backend
python main.py
```

**What you'll see on first run** (takes 15–60 seconds):

```
=======================================================
  BolChaal - Maithili Translator
  Starting server at http://localhost:8000
  API docs at   http://localhost:8000/docs
=======================================================

10:32:11 | bolchaal | INFO | Loading translation model...
10:32:11 | bolchaal | INFO | Loading model 'ai4bharat/indictrans2-en-indic-dist-200M'...
# ← HuggingFace downloads ~400MB here on first run, then caches it
10:32:45 | bolchaal | INFO | ✅ BolChaal is ready!
```

On subsequent runs the model loads from cache (~15–20 seconds, no download).

Leave this terminal open. It is your server.

### 2.2 Open the Frontend

Open `e:\CODES\AI\Language-Translator\frontend\index.html` directly in your browser (double-click it in Explorer, or drag into Chrome).

The status pill should say **"Model ready"** within 10 seconds of the backend being up.

**Alternatively, serve it over HTTP** (avoids any `file://` browser quirks):

```powershell
# New terminal, from project root
python -m http.server 3000 --directory frontend
# Then open http://localhost:3000
```

---

## Part 3 — Systematic Testing

Open a **second terminal** (with venv activated) for API tests. Keep the backend running in the first one.

### 3.1 Smoke Tests — Does the Server Exist?

```bash
curl http://localhost:8000/health
```

Expected:

```json
{"status":"online","model_loaded":true,"app":"BolChaal","version":"1.0.0"}
```

If `model_loaded` is `false`, wait 20 more seconds and retry.

```bash
curl http://localhost:8000/languages
```

Expected: a JSON list of 17 languages including English, Hinglish, Hindi, Bengali, etc.

---

### 3.2 Translation Tests — All Languages

Save this as `backend/test_translations.py` and run it:

```python
import requests

API = "http://localhost:8000"

tests = [
    # (description, src_lang, input_text)
    ("English → Maithili",   "eng_Latn", "How are you? I hope you are doing well."),
    ("Hindi → Maithili",     "hin_Deva", "आप कैसे हैं? मुझे उम्मीद है कि आप ठीक हैं।"),
    ("Bengali → Maithili",   "ben_Beng", "আপনি কেমন আছেন?"),
    ("Tamil → Maithili",     "tam_Taml", "நீங்கள் எப்படி இருக்கிறீர்கள்?"),
    ("Telugu → Maithili",    "tel_Telu", "మీరు ఎలా ఉన్నారు?"),
    ("Marathi → Maithili",   "mar_Deva", "तुम्ही कसे आहात?"),
    ("Gujarati → Maithili",  "guj_Gujr", "તમે કેમ છો?"),
    ("Kannada → Maithili",   "kan_Knda", "ನೀವು ಹೇಗಿದ್ದೀರಿ?"),
    ("Malayalam → Maithili", "mal_Mlym", "നിങ്ങൾ എങ്ങനെ ഉണ്ട്?"),
    ("Punjabi → Maithili",   "pan_Guru", "ਤੁਸੀਂ ਕਿਵੇਂ ਹੋ?"),
    ("Urdu → Maithili",      "urd_Arab", "آپ کیسے ہیں؟"),
    ("Nepali → Maithili",    "npi_Deva", "तपाईं कस्तो हुनुहुन्छ?"),
]

print(f"\n{'='*60}")
print("  BolChaal — Translation Test Suite")
print(f"{'='*60}\n")

passed = 0
failed = 0

for desc, lang, text in tests:
    try:
        r = requests.post(f"{API}/translate",
            json={"text": text, "src_lang": lang},
            timeout=120
        )
        if r.status_code == 200:
            data = r.json()
            print(f"✅ {desc}")
            print(f"   IN:  {text[:60]}")
            print(f"   OUT: {data['translated_text']}")
            print(f"   ⏱  {data['time_taken_ms']}ms\n")
            passed += 1
        else:
            print(f"❌ {desc} — HTTP {r.status_code}: {r.text}\n")
            failed += 1
    except Exception as e:
        print(f"❌ {desc} — ERROR: {e}\n")
        failed += 1

print(f"{'='*60}")
print(f"  Results: {passed} passed, {failed} failed")
print(f"{'='*60}\n")
```

```powershell
python backend/test_translations.py
```

> **Note:** The first call to any Indic-source language (Hindi, Bengali, etc.) will trigger a download of the `indic-indic-dist-320M` model (~500MB). Let it finish — subsequent calls are instant from cache.

---

### 3.3 Hinglish Tests — The Special Feature

Save this as `backend/test_hinglish.py` and run it:

```python
import requests

API = "http://localhost:8000"

# These SHOULD be detected as Hinglish (>=25% signal words)
should_detect = [
    "kaise ho",
    "main theek hu",
    "mujhe bahut accha laga",
    "kal milte hain",
    "aaj kya kiya tumne",
    "yeh bahut accha hai",
    "nahi main nahi jaana chahta",
    "haan bhai sab theek hai",
    "kya hoga kal",
    "bahut zyada ho gaya",
]

# These should NOT be Hinglish — treated as English
should_not_detect = [
    "I am fine today",
    "Hello how are you doing",
    "What is your name",
    "The weather is nice",
    "I went to the market",
]

# Edge cases — tricky mixed inputs
edge_cases = [
    "I am bahut happy aaj",      # 2/5 = 40% → Hinglish
    "main going to market",       # 1/4 = 25% → just barely Hinglish
    "hello kaise ho bhai",        # 2/4 = 50% → Hinglish
    "python is bahut hard",       # 1/4 = 25% → Hinglish (borderline)
]

print("\n" + "="*60)
print("  Hinglish Detection Tests")
print("="*60)

def test(text, expected_hinglish):
    r = requests.post(f"{API}/translate",
        json={"text": text, "src_lang": "hinglish"},
        timeout=60
    )
    data = r.json()
    detected = data.get("detected_as") == "hin_Deva"
    status = "✅" if detected == expected_hinglish else "❌"
    label = "Hinglish→Hindi→Maithili" if detected else "English→Maithili"
    print(f"{status} [{label}]")
    print(f"   IN:  \"{text}\"")
    print(f"   OUT: {data.get('translated_text', data.get('detail', 'ERROR'))}\n")

print("\n── Should detect as Hinglish ──────────────────────────")
for t in should_detect:
    test(t, expected_hinglish=True)

print("\n── Should detect as English ───────────────────────────")
for t in should_not_detect:
    test(t, expected_hinglish=False)

print("\n── Edge cases (inspect manually) ──────────────────────")
for t in edge_cases:
    test(t, expected_hinglish=True)
```

```powershell
python backend/test_hinglish.py
```

**What good Hinglish output looks like:**

```
✅ [Hinglish→Hindi→Maithili]
   IN:  "kaise ho"
   OUT: अहाँ केना छी   ← Maithili Devanagari
```

**What a false-negative looks like** (detected as English when it's Hinglish):

```
❌ [English→Maithili]
   IN:  "kaise ho"
   OUT: कैसे हो   ← This is Hindi, not Maithili — the pipeline broke
```

---

### 3.4 Error & Edge Case Tests

```bash
# Empty text — should get HTTP 422
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "", "src_lang": "eng_Latn"}'

# Invalid language code — should get HTTP 400 with clear message
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "hello", "src_lang": "xyz_Fake"}'

# Text at the character limit
python -c "
import requests
text = 'Hello world. ' * 77
r = requests.post('http://localhost:8000/translate',
    json={'text': text[:1000], 'src_lang': 'eng_Latn'}, timeout=120)
print(r.status_code, r.json().get('translated_text', r.text)[:100])
"
```

---

## Part 4 — Debugging Common Issues

| Symptom | Cause | Fix |
|:---|:---|:---|
| `Connection refused` | Backend not running | `python backend/main.py` in activated venv |
| `model_loaded: false` after 60s | Model download failed | Check internet, check `HF_TOKEN` in `config.py` |
| `OSError` about HF token | Token expired or wrong | Get a new token at huggingface.co/settings/tokens |
| `UnicodeEncodeError` in terminal | Windows console encoding | `main.py` already handles this — restart terminal |
| Status pill stuck on "Connecting..." | Frontend can't reach port 8000 | Check firewall, confirm backend started |
| Hinglish returns garbage output | `ai4bharat-transliteration` not installed | `pip install ai4bharat-transliteration` |
| First Indic request takes 90s+ | `indic-indic` model downloading | Wait — it's 500MB, one-time only |
| `address already in use` on port 8000 | Another process on that port | See command below |

**Check and kill whatever is on port 8000:**

```powershell
netstat -ano | findstr :8000
# Note the PID in the last column, then:
taskkill /PID <PID> /F
```

**Find where HuggingFace caches models** (so you know it's not re-downloading):

```powershell
python -c "from huggingface_hub import constants; print(constants.HF_HUB_CACHE)"
# Usually: C:\Users\USER\.cache\huggingface\hub
```

**List cached models and their sizes:**

```powershell
python -c "
from huggingface_hub import scan_cache_dir
for repo in scan_cache_dir().repos:
    print(repo.repo_id, repo.size_on_disk_str)
"
```

---

## Part 5 — General Handbook (Any Python + JS Project)

This is the repeatable pattern for any project with this stack.

### Step 1 — Isolate the environment

```powershell
# Always one venv per project, never install globally
python -m venv venv
venv\Scripts\Activate.ps1      # Windows
# source venv/bin/activate      # Linux / Mac

# Freeze what you have for reproducibility
pip freeze > requirements.txt
```

### Step 2 — Document one command to start each process

Every project needs one command per process. Write these down and test them on a clean terminal:

```powershell
# Backend
python backend/main.py
# or: uvicorn backend.main:app --reload

# Frontend (static)
python -m http.server 3000 --directory frontend
# or: npx serve frontend
# or: npx vite  (for React/Vue projects)
```

### Step 3 — Health check first, features second

Before testing any feature, confirm the API is alive:

```
GET /health  →  {"status": "ok"}
```

If health fails, fix that before testing anything else. Feature failures are noise until the server itself is confirmed working.

### Step 4 — Test the API layer in isolation (no browser)

```python
# test_api.py — no dependencies besides requests
import requests

BASE = "http://localhost:PORT"

def test(name, method, path, body=None, expected_status=200):
    r = getattr(requests, method)(f"{BASE}{path}", json=body, timeout=30)
    ok = "✅" if r.status_code == expected_status else "❌"
    print(f"{ok} {name}: HTTP {r.status_code}")
    if r.status_code != expected_status:
        print(f"   {r.text[:200]}")
    return r

# Golden path
test("translate English", "post", "/translate",
     {"text": "Hello", "src_lang": "eng_Latn"})

# Error paths — verify these too
test("empty text",    "post", "/translate", {"text": "", "src_lang": "eng_Latn"}, 422)
test("bad lang code", "post", "/translate", {"text": "hi", "src_lang": "fake"},   400)
test("missing field", "post", "/translate", {"text": "hi"},                        422)
```

### Step 5 — Test the frontend in browser dev tools

1. Open `F12` → **Network tab** → watch XHR/Fetch requests when you click Translate
2. If a request fails, click it → see the exact response body
3. **Console tab** → any JS errors will appear here in red
4. For CORS errors you'll see: `Access to fetch... blocked by CORS policy` → fix the `CORSMiddleware` in the backend

### Step 6 — Test on the dimensions that matter

For any translator-type app, cover these systematically:

| Dimension | What to test |
|:---|:---|
| Golden path | Normal input, correct translation output |
| Empty input | Clear error shown, app does not crash |
| Max length | 1000 chars handled gracefully |
| Special characters | `"hello! @#$%"`, `"こんにちは"`, `"مرحبا"` |
| Slow server | Kill backend mid-request — confirm UI shows error, not blank |
| Server down | Start frontend with no backend — confirm error message appears |

### Step 7 — Before claiming it works, verify the full round-trip

```
User types text
  → JS sends fetch()
    → FastAPI receives request
      → Model translates
        → JSON response
          → JS updates DOM
            → User reads output
```

Check each arrow independently. A failure at any link looks identical to the user ("it didn't translate") but has a completely different fix.

---

## Quick Reference — Commands Every Session

```powershell
# Terminal 1 — backend
cd e:\CODES\AI\Language-Translator
venv\Scripts\Activate.ps1
python backend/main.py

# Terminal 2 — tests
cd e:\CODES\AI\Language-Translator
venv\Scripts\Activate.ps1
python backend/test_translations.py
python backend/test_hinglish.py
```

```bash
# One-off API checks (Git Bash)
curl http://localhost:8000/health
curl http://localhost:8000/languages
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "kaise ho", "src_lang": "hinglish"}'
```
