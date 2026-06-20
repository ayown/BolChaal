"""Reviewed exact-match translations for known model failures."""

from __future__ import annotations

import json
import unicodedata
from functools import lru_cache
from pathlib import Path


MEMORY_PATH = Path(__file__).with_name("translation_memory.json")


def normalize_text(text: str) -> str:
    """Normalize Unicode and insignificant whitespace without changing meaning."""
    return " ".join(unicodedata.normalize("NFKC", text).split())


def normalize_source(text: str, src_lang: str) -> str:
    """Normalize source text, including case-insensitive English matching."""
    normalized = normalize_text(text)
    return normalized.casefold() if src_lang == "eng_Latn" else normalized


@lru_cache(maxsize=1)
def _load_memory() -> dict[tuple[str, str, str], str]:
    records = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
    translations: dict[tuple[str, str, str], str] = {}

    for record in records:
        key = (
            record["src_lang"].strip(),
            record["tgt_lang"].strip(),
            normalize_source(record["src"], record["src_lang"].strip()),
        )
        target = normalize_text(record["tgt"])
        previous = translations.get(key)
        if previous is not None and previous != target:
            raise ValueError(f"Conflicting reviewed translations for {key!r}")
        translations[key] = target

    return translations


def lookup_translation(text: str, src_lang: str, tgt_lang: str) -> str | None:
    """Return a reviewed translation when an exact normalized source matches."""
    src_lang = src_lang.strip()
    key = (src_lang, tgt_lang.strip(), normalize_source(text, src_lang))
    return _load_memory().get(key)
