"""Regression tests for reviewed translations that bypass known model failures."""

import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from translation_memory import lookup_translation  # noqa: E402
from translator import Translator  # noqa: E402


class TranslationMemoryTests(unittest.TestCase):
    def test_bengali_paternal_aunt_translation(self):
        result = lookup_translation(
            "আমার পিসি কোথায়?",
            "ben_Beng",
            "mai_Deva",
        )

        self.assertEqual(result, "हमर फुआ कतय छथि?")

    def test_whitespace_is_normalized(self):
        result = lookup_translation(
            "  আমার   পিসি কোথায়?  ",
            "ben_Beng",
            "mai_Deva",
        )

        self.assertEqual(result, "हमर फुआ कतय छथि?")

    def test_english_tone_correction_is_case_insensitive(self):
        expected = "भाड़मे जाए... हम तोरा सँ बहुत प्रेम करैत छी।"

        lowercase = lookup_translation(
            "fuck it.. i love you so much",
            "eng_Latn",
            "mai_Deva",
        )
        capitalized = lookup_translation(
            "Fuck it.. I love you so much",
            "eng_Latn",
            "mai_Deva",
        )

        self.assertEqual(lowercase, expected)
        self.assertEqual(capitalized, expected)
        self.assertNotIn("जाओ", expected)

    def test_english_hindi_leakage_correction(self):
        result = lookup_translation(
            "fuck it... i don't care anymore",
            "eng_Latn",
            "mai_Deva",
        )

        self.assertEqual(result, "धुर... आब हमरा कोनो परवाह नहि अछि।")
        self.assertNotIn("मुझे", result)
        self.assertNotIn("नहीं है", result)

    def test_reviewed_translation_does_not_load_a_model(self):
        translator = Translator()

        result = translator.translate(
            "আমার পিসি কোথায়?",
            "ben_Beng",
            "mai_Deva",
        )

        self.assertEqual(result, "हमर फुआ कतय छथि?")
        self.assertIsNone(translator._active_model_key)


if __name__ == "__main__":
    unittest.main()
