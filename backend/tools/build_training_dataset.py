"""
Build train/eval datasets for BolChaal fine-tuning.

Sources:
- dataset.json at the project root
- training/corrections/*.jsonl

Each correction line must include:
  {"src": "...", "tgt": "...", "src_lang": "...", "tgt_lang": "..."}
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SEED_DATASET = PROJECT_ROOT / "dataset.json"
DEFAULT_CORRECTIONS_DIR = PROJECT_ROOT / "training" / "corrections"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "training" / "generated"


def normalize_text(value: str) -> str:
    return " ".join(value.split())


def normalize_record(record: dict, source_name: str, line_number: int | None = None) -> dict:
    required = ("src", "tgt", "src_lang", "tgt_lang")
    missing = [field for field in required if not record.get(field)]
    if missing:
        line_suffix = f":{line_number}" if line_number is not None else ""
        raise ValueError(f"{source_name}{line_suffix} missing required fields: {', '.join(missing)}")

    normalized = {
        "src": normalize_text(str(record["src"])),
        "tgt": normalize_text(str(record["tgt"])),
        "src_lang": str(record["src_lang"]).strip(),
        "tgt_lang": str(record["tgt_lang"]).strip(),
    }

    if "notes" in record and record["notes"]:
        normalized["notes"] = normalize_text(str(record["notes"]))

    if "source" in record and record["source"]:
        normalized["source"] = normalize_text(str(record["source"]))

    return normalized


def load_json_array(path: Path) -> list[dict]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a top-level JSON array.")
    return [normalize_record(item, str(path)) for item in payload]


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        rows.append(normalize_record(json.loads(line), str(path), line_number))
    return rows


def load_corrections(corrections_dir: Path) -> list[dict]:
    if not corrections_dir.exists():
        return []

    rows: list[dict] = []
    for path in sorted(corrections_dir.glob("*.jsonl")):
        rows.extend(load_jsonl(path))
    return rows


def dedupe_records(records: list[dict]) -> list[dict]:
    unique: dict[tuple[str, str, str, str], dict] = {}
    for record in records:
        key = (
            record["src_lang"],
            record["tgt_lang"],
            record["src"],
            record["tgt"],
        )
        unique[key] = record
    return sorted(
        unique.values(),
        key=lambda item: (item["src_lang"], item["tgt_lang"], item["src"], item["tgt"]),
    )


def choose_eval(record: dict, eval_ratio: int) -> bool:
    key = "||".join(
        [record["src_lang"], record["tgt_lang"], record["src"], record["tgt"]]
    ).encode("utf-8")
    bucket = hashlib.sha1(key).digest()[0]
    return bucket < int(256 * (eval_ratio / 100))


def write_json(path: Path, payload: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build BolChaal fine-tuning datasets.")
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED_DATASET)
    parser.add_argument("--corrections-dir", type=Path, default=DEFAULT_CORRECTIONS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--eval-percent",
        type=int,
        default=20,
        help="Stable holdout percentage from 1 to 99.",
    )
    args = parser.parse_args()

    if not 1 <= args.eval_percent <= 99:
        raise ValueError("--eval-percent must be between 1 and 99.")

    seed_records = load_json_array(args.seed)
    correction_records = load_corrections(args.corrections_dir)
    combined = dedupe_records(seed_records + correction_records)

    train_records = [row for row in combined if not choose_eval(row, args.eval_percent)]
    eval_records = [row for row in combined if choose_eval(row, args.eval_percent)]

    if not train_records:
        raise ValueError("No training records produced. Add more examples or reduce --eval-percent.")
    if not eval_records:
        raise ValueError("No evaluation records produced. Add more examples or increase dataset size.")

    write_json(args.output_dir / "train.json", train_records)
    write_json(args.output_dir / "eval.json", eval_records)

    print(f"Seed records       : {len(seed_records)}")
    print(f"Correction records : {len(correction_records)}")
    print(f"Unique total       : {len(combined)}")
    print(f"Train split        : {len(train_records)}")
    print(f"Eval split         : {len(eval_records)}")
    print(f"Wrote              : {args.output_dir}")


if __name__ == "__main__":
    main()
