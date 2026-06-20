"""
BolChaal - Hinglish Detection Unit Tests
Run from: e:\CODES\AI\Language-Translator\backend\
Usage: ..\venv\Scripts\python.exe test\test_hinglish.py
"""
import sys
sys.path.insert(0, ".")  # so it can find hinglish.py
sys.stdout.reconfigure(encoding="utf-8")

from hinglish import detect_hinglish, transliterate_hinglish_to_hindi

DETECT_CASES = [
    # (input, expected_is_hinglish, note)
    ("kaise ho",                True,  "pure Hinglish"),
    ("main theek hun",          True,  "common Hinglish phrase"),
    ("aaj bahut accha din hai", True,  "multi-word Hinglish"),
    ("How are you?",            False, "pure English"),
    ("aap kaise hain?",         False, "Devanagari — not Hinglish"),
    ("hello how are you",       False, "English with no signal words"),
    ("ok thanks bye",           False, "English loanwords only"),
    ("main okay hun",           True,  "mixed English/Hinglish"),
]

TRANSLIT_CASES = [
    ("kaise ho",       "कैसे हो"),
    ("aaj kal",        "आज कल"),
    ("namaste dost",   "नमस्ते दोस्त"),
]


def run_tests():
    print("=" * 55)
    print("  Hinglish Detection Tests")
    print("=" * 55)

    passed = failed = 0
    for text, expected, note in DETECT_CASES:
        result = detect_hinglish(text)
        status = "PASS" if result == expected else "FAIL"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"  [{status}] {note}")
        print(f"     Input    : {text!r}")
        print(f"     Expected : {expected} | Got: {result}")
        print()

    print("=" * 55)
    print("  Transliteration Tests")
    print("=" * 55)

    for text, expected in TRANSLIT_CASES:
        result = transliterate_hinglish_to_hindi(text)
        print(f"  {text!r}  ->  {result}")
    print()

    print("=" * 55)
    print(f"  Detection: {passed} passed, {failed} failed")
    print("=" * 55)


if __name__ == "__main__":
    run_tests()
