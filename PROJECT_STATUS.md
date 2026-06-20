# BolChaal — Project Status Report

This document provides a comprehensive overview of what has been implemented so far in **BolChaal** (formerly MithilaTranslate), a CPU-friendly, local-first language translator targeting translation from English, Hindi, Hinglish, and other Indic languages into **Maithili**.

---

## 🛠️ Implemented Architecture

```
                                  ┌───────────────────────────┐
                                  │   Frontend (Web Browser)  │
                                  │   - Premium Dark Glass UI │
                                  │   - Real-time interaction │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼ fetch() to localhost:8000
                                  ┌───────────────────────────┐
                                  │      FastAPI Backend      │
                                  └─────────────┬─────────────┘
                                                │
                          ┌─────────────────────┴─────────────────────┐
                          ▼ (If Hindi selected & input in Latin)     ▼ (All other inputs)
            ┌──────────────────────────┐                ┌──────────────────────────┐
            │ Hinglish Pipeline        │                │ Translation Engine       │
            │ 1. Match signal words    │                │ - Lazily loads models    │
            │ 2. Keep English loanwords│                │ - Enforces single model  │
            │ 3. Transliterate Roman   │                │   in RAM (~1.2GB limit)  │
            │    Hindi to Devanagari   │                │ - CPU optimized execution│
            └─────────────┬────────────┘                └─────────────┬────────────┘
                          │                                           │
                          └─────────────────────┬─────────────────────┘
                                                ▼
                                  ┌───────────────────────────┐
                                  │      Maithili Output      │
                                  └───────────────────────────┘
```

---

## 🧠 Translation Engine & Memory Optimizations

To run smoothly on CPU-only machines with limited RAM (keeping usage under the 3GB limit), the backend features a robust memory management strategy:

1. **Lazy Loading**: Translation models are only loaded into memory when required by a request.
2. **Strict Single-Model RAM Residency**: 
   - Translating **English → Maithili** uses `indictrans2-en-indic-dist-200M` (~1.2GB).
   - Translating **Hindi/Bengali/other Indic → Maithili** uses `indictrans2-indic-indic-dist-320M` (~1.3GB).
   - When a switch occurs (e.g. from English to Hindi translation), the engine unloads the active model, performs Garbage Collection (`gc.collect()`), and then loads the requested model. This prevents Out-Of-Memory (OOM) crashes.
3. **Pure Python Fallback Processor**: Built a fallback implementation of `IndicProcessor` (`backend/processor_fallback.py`) that bypasses compiler dependencies like C++ Build Tools or Cython on Windows, allowing it to run out of the box.

---

## 🗣️ Hinglish Detection & Transliteration Pipeline

Hinglish is handled seamlessly under the **Hindi** language selection without requiring a separate dropdown:

- **Detection**: Analyzes the script of the input text. If it is Roman script and contains at least 20% of common Hindi phonetics/signal words (e.g., *kaise*, *ho*, *main*, *aaj*, *theek*), it is classified as Hinglish.
- **Transliteration**: Uses a local transliterator to convert the Roman Hindi characters into Devanagari script.
- **Loanword Protection**: Common English loanwords (e.g., *phone*, *laptop*, *online*, *doctor*) are identified and protected so they are not transliterated into phonetic nonsense, keeping translation accuracy high.

---

## 🎨 Frontend UI

A single-page web app is implemented in the `frontend/` directory with:
- **`index.html`**: Structured semantic layout containing the translator card, input textareas, language selectors, and status indicators.
- **`styles/main.css`**: Styling built with modern CSS variables, vibrant indigo-to-violet dark gradient backgrounds, glassmorphism card panels (`backdrop-filter`), smooth hover/focus transitions, and a loading skeleton screen.
- **`scripts/app.js`**: Drives client-side logic:
  - Fetches the active language list from the backend.
  - Translates text via async `fetch()` requests.
  - Detects if the backend automatically identified Hinglish text, and shows a premium "Hinglish Detected" badge to the user.
  - Features character counting, copy-to-clipboard buttons, and error recovery.

---

## 🧪 Comprehensive Test Suite

Per the project requirements, all tests have been placed in the `backend/test/` folder. They cover unit and integration scopes:

1. **`backend/test/test_translations.py`**:
   - Tests end-to-end translation requests for English, Hindi (Devanagari), Hinglish, Bengali, and Maithili passthroughs.
2. **`backend/test/test_hinglish.py`**:
   - Performs unit tests for Hinglish detection ratio thresholds and transliteration mappings.
3. **`backend/test/test_edge_cases.py`**:
   - Validates server boundaries (e.g., whitespace-only inputs, empty fields, invalid language codes, text over the 1000-character limit, and wrong HTTP methods).

---

## 🚦 Next Steps

- Refine translation quality for low-resource pairs like Bengali/Hinglish → Maithili (which can be accomplished via future fine-tuning on Google Colab/Hugging Face).
- Migrate the frontend to React/Vite (if desired) once model performance is fully tuned.
