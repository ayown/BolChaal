# 🧠 How to Train & Fine-Tune BolChaal on Google Colab

If direct translations for low-resource pairs (like **Bengali → Maithili** or informal **Hinglish → Maithili**) are suboptimal, the best way to fix it is **fine-tuning** the pre-trained `IndicTrans2` model using a custom dataset of correct translation pairs. 

This guide shows you how to use **Google Colab (Free T4 GPU)** and **LoRA (Low-Rank Adaptation)** to fine-tune the model, and then load the adapter weights locally on your CPU.

---

## 📅 Step 1: Prepare Your Training Dataset

Prepare a dataset of correct translation pairs. Create a file called `dataset.json` with the following structure:

```json
[
  {
    "src": "আপনি কেমন আছেন?",
    "tgt": "अहाँ कोना छी?",
    "src_lang": "ben_Beng",
    "tgt_lang": "mai_Deva"
  },
  {
    "src": "আমি তোমাকে ভালোবাসি।",
    "tgt": "हम अहाँ सँ प्रेम करैत छी ।",
    "src_lang": "ben_Beng",
    "tgt_lang": "mai_Deva"
  },
  {
    "src": "main thik hun, tum batao?",
    "tgt": "हम ठीक छी, अहाँ कहू?",
    "src_lang": "hin_Deva",
    "tgt_lang": "mai_Deva"
  }
]
```

> [!TIP]
> **Hinglish Tip**: Since Hinglish inputs are automatically transliterated to standard Devanagari Hindi in the pipeline before hitting the model, you should write Hinglish source sentences in their **transliterated Devanagari form** (e.g., `"मैं ठीक हूँ, तुम बताओ?"`) as the `src` and map them to Maithili. This allows the model to learn the correct mappings directly.

---

## 🚀 Step 2: Google Colab Training Notebook

1. Go to [Google Colab](https://colab.research.google.com).
2. Create a new notebook and set the runtime to **T4 GPU** (`Runtime > Change runtime type > T4 GPU`).
3. Copy and run the following blocks in Colab cells:

### Cell 1: Environment Setup (run once, then RESTART the runtime)

> [!IMPORTANT]
> **After this cell finishes, go to `Runtime → Restart session` before running any other cell.** This forces Python to pick up the pinned `transformers` version. The `!rm` line also wipes any cached model modules from a previous session that were built against a newer, incompatible API.

```python
# Wipe stale cached model code (tokenizer / config files built against newer transformers)
!rm -rf ~/.cache/huggingface/modules/

# Pin to 4.37.2 — the last stable release before two breaking API changes:
#   1. transformers.onnx was removed (≥ 4.40) — breaks IndicTrans2 config
#   2. _special_tokens_map no longer pre-exists at __setattr__ time (≥ 4.44) — breaks IndicTrans2 tokenizer
!pip install -q "transformers==4.37.2" "accelerate==0.25.0" "peft==0.9.0" datasets sentencepiece sacremoses
```

### Cell 2: Import Packages & Log in to Hugging Face
```python
import json
import torch
import gc
from datasets import Dataset
from transformers import (
    AutoModelForSeq2SeqLM, 
    AutoTokenizer, 
    DataCollatorForSeq2Seq, 
    Seq2SeqTrainingArguments, 
    Seq2SeqTrainer
)
from peft import LoraConfig, get_peft_model, TaskType

# Paste your HuggingFace read token here — get it from .env or huggingface.co/settings/tokens
HF_TOKEN = "hf_YOUR_TOKEN_HERE"   # ← replace with your own token
```

### Cell 3: Load Dataset
*Upload your `dataset.json` to Colab files pane, then run:*
```python
with open("dataset.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

# Convert to HF Dataset
dataset = Dataset.from_list(raw_data)
print(f"Loaded {len(dataset)} translation pairs.")
```

### Cell 4: Verify Environment

> [!IMPORTANT]
> **If this prints a version other than `4.37.x`, stop.** Re-run Cell 1, then go to `Runtime → Restart session`, then start again from Cell 2. Running a wrong version causes two cascading errors: `ModuleNotFoundError: transformers.onnx` and `AttributeError: IndicTransTokenizer has no attribute _special_tokens_map`.

```python
import transformers
print(f"transformers version: {transformers.__version__}")
assert transformers.__version__.startswith("4.37"), \
    f"Wrong version! Got {transformers.__version__} — re-run Cell 1 and restart runtime."
print("Environment OK — safe to proceed.")
```

### Cell 5: Load Base Model and Tokenizer
```python
model_id = "ai4bharat/indictrans2-indic-indic-dist-320M"

tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True, token=HF_TOKEN)
model = AutoModelForSeq2SeqLM.from_pretrained(
    model_id, 
    trust_remote_code=True, 
    torch_dtype=torch.float32,  # FP32 required for stable LoRA training — 320M model fits in T4's 15GB VRAM
    device_map="auto",
    token=HF_TOKEN
)
```

### Cell 6: Preprocess Data with Language Tags
```python
def preprocess_function(examples):
    # Prepend tags formatting required by IndicTrans2
    # Format: "{src_lang} {tgt_lang} {text}"
    inputs = [
        f"{src_l} {tgt_l} {text}" 
        for text, src_l, tgt_l in zip(examples["src"], examples["src_lang"], examples["tgt_lang"])
    ]
    targets = examples["tgt"]
    
    model_inputs = tokenizer(inputs, max_length=256, truncation=True)
    labels = tokenizer(text_target=targets, max_length=256, truncation=True)
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

tokenized_dataset = dataset.map(preprocess_function, batched=True, remove_columns=dataset.column_names)
```

### Cell 7: Configure LoRA (Adapter Tuning)
```python
# LoRA config targeting attention weights
peft_config = LoraConfig(
    task_type=TaskType.SEQ_2_SEQ_LM,
    inference_mode=False,
    r=16,          # rank
    lora_alpha=32,
    lora_dropout=0.1,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"]
)

model = get_peft_model(model, peft_config)
model.print_trainable_parameters()
# Expected: ~1-2% of model parameters are trainable, meaning training will be extremely fast!
```

### Cell 8: Run Training
```python
training_args = Seq2SeqTrainingArguments(
    output_dir="./bolchaal-lora-adapter",
    per_device_train_batch_size=8,
    gradient_accumulation_steps=2,
    learning_rate=3e-4,
    num_train_epochs=5,  # Adjust based on dataset size (5-10 is usually good)
    predict_with_generate=True,
    fp16=False,  # Must be False when model is in FP32 — mixing FP16 AMP with FP32 LoRA adapters causes GradScaler crash
    logging_steps=10,
    save_strategy="epoch",
    report_to="none"
)

trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=DataCollatorForSeq2Seq(tokenizer, model=model)
)

trainer.train()

# Save the adapter weights
model.save_pretrained("./bolchaal-lora-adapter")
tokenizer.save_pretrained("./bolchaal-lora-adapter")
print("🎉 Training complete and adapter saved!")
```

### Cell 9: Download Adapter
Zip and download the adapter folder:
```python
!zip -r bolchaal-lora-adapter.zip ./bolchaal-lora-adapter
from google.colab import files
files.download("bolchaal-lora-adapter.zip")
```

---

## 🔌 Step 3: Load the Adapter in Your Local App

Once downloaded, you can load your LoRA adapter on your local CPU setup.

1. Unzip the file and place the `bolchaal-lora-adapter` directory inside your `backend/models/` folder.
2. Install `peft` in your local Python virtual environment:
   ```bash
   e:\CODES\AI\Language-Translator\venv\Scripts\pip.exe install peft
   ```
3. Update `backend/translator.py` to wrap the loaded model with `PeftModel`:

```python
from peft import PeftModel

# Inside your _load_model function in translator.py:
model = AutoModelForSeq2SeqLM.from_pretrained(...)

# Add adapter path checking
adapter_path = "models/bolchaal-lora-adapter"
if os.path.exists(adapter_path):
    logger.info(f"Applying fine-tuned LoRA adapter from {adapter_path}...")
    model = PeftModel.from_pretrained(model, adapter_path)
```

This ensures that the base model stays unmodified, but uses your custom-trained weights to translate Bengali and Hinglish perfectly!
