"""
BolChaal - Pure Python IndicProcessor Fallback

This replaces the IndicTransToolkit's IndicProcessor (which requires
Microsoft C++ Build Tools to compile Cython on Windows).

Implements the same interface:
  - preprocess_batch(sentences, src_lang, tgt_lang)
  - postprocess_batch(sentences, lang)

The IndicTrans2 HuggingFace models handle language routing via
the tokenizer's src_lang + forced_bos_token_id mechanism,
so we just need basic text normalization here.
"""

import re
import unicodedata


# Punctuation normalization map (common across Indian scripts)
_PUNCT_MAP = {
    "\u0964": ".",   # Devanagari danda → period
    "\u0965": ".",   # Devanagari double danda → period
    "\u200b": "",    # Zero-width space
    "\u200c": "",    # Zero-width non-joiner
    "\u200d": "",    # Zero-width joiner
    "\ufeff": "",    # BOM
    "\u00a0": " ",   # Non-breaking space → regular space
}


def _normalize_text(text: str) -> str:
    """Basic text normalization for translation input."""
    # Apply punctuation map
    for src, tgt in _PUNCT_MAP.items():
        text = text.replace(src, tgt)

    # Normalize unicode (NFC form — important for Devanagari)
    text = unicodedata.normalize("NFC", text)

    # Collapse multiple whitespace
    text = re.sub(r"\s+", " ", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


class IndicProcessor:
    """
    Pure Python drop-in replacement for IndicTransToolkit.IndicProcessor.
    Works without Microsoft C++ Build Tools or Cython.
    """

    def __init__(self, inference: bool = True):
        self.inference = inference

    def preprocess_batch(
        self,
        sentences: list[str],
        src_lang: str,
        tgt_lang: str,
        show_progress_bar: bool = False,
    ) -> list[str]:
        """
        Normalize and prepare sentences for IndicTrans2 input.

        The IndicTrans2 tokenizer expects the input string to start with
        the source and target language tags separated by spaces:
        "{src_lang} {tgt_lang} {text}"
        """
        processed = []
        for sent in sentences:
            sent = _normalize_text(sent)
            if sent:
                # Add the language tags required by IndicTransTokenizer._src_tokenize
                processed.append(f"{src_lang} {tgt_lang} {sent}")
            else:
                processed.append("")
        return processed

    def postprocess_batch(
        self,
        sentences: list[str],
        lang: str,
        show_progress_bar: bool = False,
    ) -> list[str]:
        """
        Normalize translation output.
        Strips any stray whitespace and normalizes unicode.
        """
        processed = []
        for sent in sentences:
            sent = _normalize_text(sent)
            processed.append(sent)
        return processed
