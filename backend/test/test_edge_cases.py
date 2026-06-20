"""
BolChaal — Step 3.4: Error & Edge Case Tests

Run with: python backend/test_edge_cases.py
Backend must be running at http://localhost:8000
"""

import requests

API = "http://localhost:8000"
TRANSLATE = f"{API}/translate"

passed = 0
failed = 0


def check(name, payload, expected_status, expected_fragment=None, timeout=30):
    """
    Send a POST /translate request and verify the response.

    expected_fragment: optional string that must appear in the response body.
    timeout: seconds to wait — use 120+ for tests that hit the translation model.
    """
    global passed, failed
    try:
        r = requests.post(TRANSLATE, json=payload, timeout=timeout)
        body = r.text

        status_ok = r.status_code == expected_status
        fragment_ok = (expected_fragment is None) or (expected_fragment.lower() in body.lower())

        if status_ok and fragment_ok:
            print(f"  ✅  {name}")
            print(f"       HTTP {r.status_code}  |  {body[:120]}")
            passed += 1
        else:
            print(f"  ❌  {name}")
            if not status_ok:
                print(f"       Expected HTTP {expected_status}, got {r.status_code}")
            if not fragment_ok:
                print(f"       Expected '{expected_fragment}' in response body")
            print(f"       Body: {body[:200]}")
            failed += 1

    except requests.exceptions.ConnectionError:
        print(f"  💀  {name}")
        print(f"       Cannot connect to {API}. Is the backend running?")
        failed += 1
    except Exception as e:
        print(f"  💀  {name}")
        print(f"       Unexpected error: {e}")
        failed += 1

    print()


# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  BolChaal — Error & Edge Case Tests (Step 3.4)")
print("=" * 60)

# ── Section 1: Missing / empty fields ────────────────────────────────────────
print("\n── 1. Missing & empty fields ───────────────────────────────\n")

check(
    "Empty string text",
    {"text": "", "src_lang": "eng_Latn"},
    expected_status=422,           # Pydantic min_length=1 catches this
)

check(
    "Whitespace-only text",
    {"text": "     ", "src_lang": "eng_Latn"},
    expected_status=400,           # Pydantic passes it, route strips → empty
    expected_fragment="empty",
)

check(
    "Missing 'text' field entirely",
    {"src_lang": "eng_Latn"},
    expected_status=422,
)

check(
    "Missing 'src_lang' field entirely",
    {"text": "Hello"},
    expected_status=422,
)

check(
    "Both fields missing (empty body)",
    {},
    expected_status=422,
)

# ── Section 2: Bad language codes ─────────────────────────────────────────────
print("── 2. Invalid language codes ───────────────────────────────\n")

check(
    "Completely fake lang code",
    {"text": "Hello", "src_lang": "xyz_Fake"},
    expected_status=400,
    expected_fragment="unsupported",
)

check(
    "Empty lang code string",
    {"text": "Hello", "src_lang": ""},
    expected_status=400,
    expected_fragment="unsupported",
)

check(
    "Numeric lang code",
    {"text": "Hello", "src_lang": "12345"},
    expected_status=400,
    expected_fragment="unsupported",
)

check(
    "Lang code with wrong separator",
    {"text": "Hello", "src_lang": "eng-Latn"},   # dash instead of underscore
    expected_status=400,
    expected_fragment="unsupported",
)

# ── Section 3: Text length boundaries ─────────────────────────────────────────
print("── 3. Text length boundaries ───────────────────────────────\n")

# Pydantic-rejection tests first — these never hit the model, always instant
check(
    "1001 characters (over limit) — instant Pydantic rejection",
    {"text": "a" * 1001, "src_lang": "eng_Latn"},
    expected_status=422,
)

check(
    "5000 characters (way over limit) — instant Pydantic rejection",
    {"text": "Hello world. " * 400, "src_lang": "eng_Latn"},
    expected_status=422,
)

# Model-hitting tests after — these need a long timeout
check(
    "Single character — hits model",
    {"text": "a", "src_lang": "eng_Latn"},
    expected_status=200,
    timeout=120,
)

check(
    "Exactly 1000 characters (the limit) — hits model, will be slow",
    {"text": "Hello world, this is a test sentence. " * 27, "src_lang": "eng_Latn"},
    expected_status=200,
    timeout=180,
)

# ── Section 4: Special characters & scripts ───────────────────────────────────
print("── 4. Special characters & non-Latin scripts ───────────────\n")

check(
    "Punctuation and symbols",
    {"text": "Hello! @#$% ^&*() — how are you?", "src_lang": "eng_Latn"},
    expected_status=200,
    timeout=120,
)

check(
    "Numbers only",
    {"text": "42 100 2024", "src_lang": "eng_Latn"},
    expected_status=200,
    timeout=120,
)

check(
    "Emoji in text",
    {"text": "Hello how are you 😊", "src_lang": "eng_Latn"},
    expected_status=200,
    timeout=120,
)

check(
    "Japanese script (unsupported language but valid request body)",
    {"text": "こんにちは", "src_lang": "eng_Latn"},
    expected_status=200,           # Server accepts it; translation quality may vary
    timeout=120,
)

check(
    "Arabic text with Arabic lang code",
    {"text": "كيف حالك", "src_lang": "urd_Arab"},
    expected_status=200,
    timeout=120,
)

# ── Section 5: Hinglish edge cases ────────────────────────────────────────────
print("── 5. Hinglish-specific edge cases ────────────────────────\n")

check(
    "Hinglish code with pure English input (auto-routes to English)",
    {"text": "I am feeling great today", "src_lang": "hinglish"},
    expected_status=200,
    timeout=120,
)

check(
    "Hinglish code with Devanagari input (already Hindi, skip transliteration)",
    {"text": "आप कैसे हैं", "src_lang": "hinglish"},
    expected_status=200,
    timeout=120,
)

check(
    "Single Hinglish word",
    {"text": "namaste", "src_lang": "hinglish"},
    expected_status=200,
    timeout=120,
)

# ── Section 6: Wrong HTTP methods ─────────────────────────────────────────────
print("── 6. Wrong HTTP methods ───────────────────────────────────\n")

try:
    r = requests.get(TRANSLATE, timeout=10)
    ok = r.status_code == 405
    symbol = "✅" if ok else "❌"
    print(f"  {symbol}  GET /translate should be 405 Method Not Allowed")
    print(f"       HTTP {r.status_code}  |  {r.text[:80]}\n")
    if ok: passed += 1
    else:  failed += 1
except Exception as e:
    print(f"  💀  GET /translate check failed: {e}\n")
    failed += 1

# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print(f"  Results: {passed} passed, {failed} failed out of {passed + failed} tests")
print("=" * 60 + "\n")

if failed > 0:
    print("Tip: Tests marked ❌ show unexpected behaviour.")
    print("     Tests marked 💀 couldn't reach the server at all.\n")
