"""
BolChaal - Translation Pipeline Tests
Run from: e:\CODES\AI\Language-Translator\backend\
Usage: ..\venv\Scripts\python.exe test\test_translations.py
"""
import sys
import json
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://localhost:8000"


def translate(text: str, lang: str) -> dict:
    data = json.dumps({"text": text, "src_lang": lang}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/translate",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req, timeout=120)
    return json.loads(resp.read().decode("utf-8"))


def health_check() -> dict:
    resp = urllib.request.urlopen(f"{BASE_URL}/health", timeout=10)
    return json.loads(resp.read().decode("utf-8"))


# ─── Test Cases ───────────────────────────────────────────────────────────────
TEST_CASES = [
    # (label, input_text, src_lang, expected_note)
    ("English → Maithili",          "How are you?",             "eng_Latn", "अहाँ कोना छी?"),
    ("English (long) → Maithili",   "I am going to the market to buy some vegetables.", "eng_Latn", "market sentence"),
    ("Hindi Devanagari → Maithili", "आप कैसे हैं?",              "hin_Deva", "अहाँ कोना छी?"),
    ("Hindi → Maithili (sentence)", "मुझे बहुत अच्छा लगा।",     "hin_Deva", "मोरा / हमरा"),
    ("Hinglish → Maithili",         "kaise ho aaj",             "hin_Deva", "auto-detected hinglish"),
    ("Hinglish → Maithili (long)",  "main theek hun, aur tum?", "hin_Deva", "auto-detected hinglish"),
    ("Bengali → Maithili",          "আপনি কেমন আছেন?",          "ben_Beng", "formal greeting"),
    ("Maithili passthrough",        "अहाँ कोना छी?",             "mai_Deva", "identity / near-identity"),
]


def run_tests():
    print("=" * 60)
    print("  BolChaal Translation Tests")
    print("=" * 60)

    # Health check first
    try:
        h = health_check()
        print(f"\n  Server: {h['status']} | Model loaded: {h['model_loaded']}\n")
    except Exception as e:
        print(f"\n  ❌ Server not reachable: {e}")
        print("  Start the server first: python main.py\n")
        return

    passed = failed = 0

    for label, text, lang, note in TEST_CASES:
        print(f"▶  {label}")
        print(f"   Input  : {text}")
        try:
            r = translate(text, lang)
            output = r["translated_text"]
            elapsed = r["time_taken_ms"]
            detected = r.get("detected_as")

            print(f"   Output : {output}")
            if detected:
                print(f"   Detect : {detected}")
            print(f"   Time   : {elapsed}ms")
            print(f"   Note   : {note}")
            passed += 1
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
