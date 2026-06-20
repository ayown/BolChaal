"""Unit tests for multi-stage translation routing and tone handling."""

import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from translator import (  # noqa: E402
    Translator,
    clean_translation_punctuation,
    split_english_discourse_prefix,
)


class StubTranslator(Translator):
    def __init__(self):
        super().__init__(use_adapter=False)
        self.calls = []

    def _translate_once(self, text, src_lang, tgt_lang):
        self.calls.append((text, src_lang, tgt_lang))
        if (src_lang, tgt_lang) == ("eng_Latn", "hin_Deva"):
            return "हमें अब निकलना चाहिए"
        if (src_lang, tgt_lang) == ("hin_Deva", "mai_Deva"):
            return "आब हमरा सभकेँ निकलबाक चाही"
        return "direct"


class TranslationRoutingTests(unittest.TestCase):
    def test_tokenizer_spacing_before_punctuation_is_removed(self):
        self.assertEqual(
            clean_translation_punctuation("हमरा आब परवाह नहि अछि ."),
            "हमरा आब परवाह नहि अछि.",
        )

    def test_fuck_it_is_an_impersonal_prefix(self):
        prefix, content = split_english_discourse_prefix(
            "Fuck it... we should leave now"
        )

        self.assertEqual(prefix, "धुर...")
        self.assertEqual(content, "we should leave now")

    def test_english_to_maithili_uses_hindi_pivot(self):
        translator = StubTranslator()

        result = translator.translate(
            "Fuck it... we should leave now",
            "eng_Latn",
            "mai_Deva",
        )

        self.assertEqual(result, "धुर... आब हमरा सभकेँ निकलबाक चाही")
        self.assertEqual(
            translator.calls,
            [
                ("we should leave now", "eng_Latn", "hin_Deva"),
                ("हमें अब निकलना चाहिए", "hin_Deva", "mai_Deva"),
            ],
        )

    def test_non_maithili_target_uses_direct_route(self):
        translator = StubTranslator()

        result = translator.translate("Hello", "eng_Latn", "hin_Deva")

        self.assertEqual(result, "हमें अब निकलना चाहिए")
        self.assertEqual(
            translator.calls,
            [("Hello", "eng_Latn", "hin_Deva")],
        )


if __name__ == "__main__":
    unittest.main()
