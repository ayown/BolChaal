# Training Data Workflow

This folder is the starting point for the remaining model work.

## Files

- `corrections/*.jsonl`: reviewed translation pairs collected from manual correction.
- `generated/train.json`: fine-tuning split generated from seed data plus corrections.
- `generated/eval.json`: stable holdout split used to compare the base model vs the LoRA adapter.

## Correction format

Each line in a correction file must be valid JSON:

```json
{"src":"मैं ठीक हूँ, तुम बताओ?","tgt":"हम ठीक छी, अहाँ कहू?","src_lang":"hin_Deva","tgt_lang":"mai_Deva"}
```

Use `hin_Deva` for Hinglish-derived examples after you normalize them to Devanagari Hindi.

## Build datasets

From the project root:

```powershell
python backend/tools/build_training_dataset.py
```

That merges:

- `dataset.json`
- every `training/corrections/*.jsonl` file

and writes:

- `training/generated/train.json`
- `training/generated/eval.json`

## Evaluate base vs adapter

After the backend dependencies and models are available:

```powershell
python backend/test/evaluate_model.py
```

To run only the base model:

```powershell
python backend/test/evaluate_model.py --mode baseline
```
