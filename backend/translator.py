"""
BolChaal - IndicTrans2 Translation Engine

Manages model loading and translation for:
- English → Maithili (en-indic-dist-200M)
- Indic → Maithili (indic-indic-dist-320M)

**Memory Strategy**: Only ONE model is kept in RAM at a time.
Each model uses ~1.2GB RAM. Swapping takes ~5s (loaded from disk cache).
This keeps peak usage under 3GB comfortably on 16GB RAM.
"""

import gc
import logging
import os
import re
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

try:
    from peft import PeftModel
    _PEFT_AVAILABLE = True
except ImportError:
    _PEFT_AVAILABLE = False

from config import MODELS, ENGLISH_SOURCE_LANGS, INDIC_SOURCE_LANGS, HF_TOKEN
from translation_memory import lookup_translation

logger = logging.getLogger("bolchaal.translator")

_ENGLISH_FUCK_IT_PREFIX = re.compile(
    r"^\s*fuck\s+it\b[\s.!?,;:\-\u2026]*",
    flags=re.IGNORECASE,
)


def split_english_discourse_prefix(text: str) -> tuple[str, str]:
    """Separate an impersonal opening interjection from translatable content."""
    match = _ENGLISH_FUCK_IT_PREFIX.match(text)
    if match is None:
        return "", text.strip()
    return "धुर...", text[match.end():].strip()


def clean_translation_punctuation(text: str) -> str:
    """Remove tokenizer-introduced spaces before terminal punctuation."""
    return re.sub(r"\s+([,.;:!?।])", r"\1", text).strip()


class Translator:
    """
    Wrapper around IndicTrans2 models.
    Loads models lazily and keeps only ONE in RAM at a time.
    """

    def __init__(self, use_adapter: bool = True):
        self.device = "cpu"
        self.ip = None
        self.use_adapter = use_adapter

        self._en_indic_model = None
        self._en_indic_tokenizer = None
        self._indic_indic_model = None
        self._indic_indic_tokenizer = None
        self._active_model_key = None   # track which model is currently loaded

        logger.info(
            "Translator initialized | device=%s | use_adapter=%s",
            self.device,
            self.use_adapter,
        )

    def _load_processor(self):
        """Load IndicProcessor for pre/post-processing."""
        if self.ip is None:
            try:
                from IndicTransToolkit.processor import IndicProcessor
                self.ip = IndicProcessor(inference=True)
                logger.info("IndicProcessor loaded (IndicTransToolkit).")
            except (ImportError, Exception):
                logger.warning(
                    "IndicTransToolkit not available (likely missing C++ Build Tools on Windows). "
                    "Using built-in pure Python processor instead."
                )
                from processor_fallback import IndicProcessor
                self.ip = IndicProcessor(inference=True)
                logger.info("IndicProcessor loaded (pure Python fallback).")

    def _unload_model(self, model_key: str):
        """Unload a model from RAM and free memory."""
        if model_key == "en_indic" and self._en_indic_model is not None:
            logger.info("Unloading en_indic model to free RAM...")
            del self._en_indic_model
            del self._en_indic_tokenizer
            self._en_indic_model = None
            self._en_indic_tokenizer = None
            gc.collect()
            logger.info("en_indic unloaded.")
        elif model_key == "indic_indic" and self._indic_indic_model is not None:
            logger.info("Unloading indic_indic model to free RAM...")
            del self._indic_indic_model
            del self._indic_indic_tokenizer
            self._indic_indic_model = None
            self._indic_indic_tokenizer = None
            gc.collect()
            logger.info("indic_indic unloaded.")

    def _load_model(self, model_key: str):
        """Load a specific IndicTrans2 model and tokenizer from HuggingFace."""
        model_id = MODELS[model_key]
        logger.info(f"Loading model '{model_id}'... (first time downloads, later from cache)")

        token = HF_TOKEN if HF_TOKEN else None

        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=True,
            token=token,
        )
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            torch_dtype=torch.float32,
            token=token,
        )

        if model_key == "indic_indic" and self.use_adapter:
            adapter_path = os.path.join(os.path.dirname(__file__), "models", "bolchaal-lora-adapter")
            if _PEFT_AVAILABLE and os.path.exists(adapter_path):
                logger.info(f"Applying LoRA adapter from '{adapter_path}'...")
                model = PeftModel.from_pretrained(model, adapter_path)
                logger.info("LoRA adapter applied.")
            elif not _PEFT_AVAILABLE:
                logger.warning("peft not installed — skipping LoRA adapter. Run: pip install peft")
            else:
                logger.info("No LoRA adapter found at '%s' — using base model.", adapter_path)

        elif model_key == "indic_indic":
            logger.info("Adapter disabled for this translator instance - using base model.")

        model.eval()
        logger.info(f"Model '{model_key}' loaded successfully.")
        return model, tokenizer

    def _get_en_indic(self):
        """Get the English → Indic model. Unloads indic_indic if needed."""
        if self._en_indic_model is None:
            # Free the other model first to save RAM
            if self._indic_indic_model is not None:
                self._unload_model("indic_indic")
            self._en_indic_model, self._en_indic_tokenizer = self._load_model("en_indic")
            self._active_model_key = "en_indic"
        return self._en_indic_model, self._en_indic_tokenizer

    def _get_indic_indic(self):
        """Get the Indic → Indic model. Unloads en_indic if needed."""
        if self._indic_indic_model is None:
            # Free the other model first to save RAM
            if self._en_indic_model is not None:
                self._unload_model("en_indic")
            self._indic_indic_model, self._indic_indic_tokenizer = self._load_model("indic_indic")
            self._active_model_key = "indic_indic"
        return self._indic_indic_model, self._indic_indic_tokenizer

    def translate(self, text: str, src_lang: str, tgt_lang: str = "mai_Deva") -> str:
        """
        Translate text from src_lang to tgt_lang (default: Maithili).

        Args:
            text: Input text to translate.
            src_lang: Source language FLORES code (e.g., "eng_Latn", "hin_Deva").
            tgt_lang: Target language FLORES code. Default: Maithili.

        Returns:
            Translated text string.
        """
        if not text or not text.strip():
            return ""

        reviewed_translation = lookup_translation(text, src_lang, tgt_lang)
        if reviewed_translation is not None:
            logger.info(
                "Using reviewed translation memory | %s -> %s",
                src_lang,
                tgt_lang,
            )
            return reviewed_translation

        if src_lang == "eng_Latn" and tgt_lang == "mai_Deva":
            prefix, content = split_english_discourse_prefix(text)
            if not content:
                return "धुर।" if prefix else ""

            logger.info("Using English -> Hindi -> Maithili quality route.")
            hindi = self._translate_once(content, "eng_Latn", "hin_Deva")
            maithili = self._translate_once(hindi, "hin_Deva", "mai_Deva")
            return clean_translation_punctuation(f"{prefix} {maithili}")

        return self._translate_once(text, src_lang, tgt_lang)

    def _translate_once(self, text: str, src_lang: str, tgt_lang: str) -> str:
        """Run one model translation step without route selection."""

        self._load_processor()

        # Choose the correct model based on source language
        if src_lang in ENGLISH_SOURCE_LANGS:
            model, tokenizer = self._get_en_indic()
        elif src_lang in INDIC_SOURCE_LANGS:
            model, tokenizer = self._get_indic_indic()
        else:
            raise ValueError(f"Unsupported source language: {src_lang}")

        # Preprocess with IndicProcessor (normalize + add language tags)
        input_sentences = [text.strip()]
        batch = self.ip.preprocess_batch(
            input_sentences,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
        )

        # Tokenize
        inputs = tokenizer(
            batch,
            truncation=True,
            padding="longest",
            return_tensors="pt",
            return_attention_mask=True,
        ).to(self.device)

        # Generate translation
        with torch.no_grad():
            generated_tokens = model.generate(
                **inputs,
                use_cache=True,
                min_length=0,
                max_length=256,
                num_beams=4,
                num_return_sequences=1,
                repetition_penalty=1.3,
                no_repeat_ngram_size=4,
            )

        # Decode tokens
        decoded = tokenizer.batch_decode(
            generated_tokens,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True,
        )

        # Postprocess
        translations = self.ip.postprocess_batch(decoded, lang=tgt_lang)
        return clean_translation_punctuation(translations[0]) if translations else ""

    def warmup(self):
        """
        Pre-load the English → Indic model at startup.
        indic-indic is loaded on demand to save RAM.
        """
        logger.info("Warming up translation engine...")
        try:
            self._load_processor()
            self._get_en_indic()
            logger.info("Warmup complete. Ready to translate!")
        except Exception as e:
            logger.error(f"Warmup failed: {e}")
            raise
