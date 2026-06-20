"""
Evaluate BolChaal translation quality on a labeled dataset.

Examples:
  python backend/test/evaluate_model.py
  python backend/test/evaluate_model.py --mode baseline
  python backend/test/evaluate_model.py --dataset training/generated/eval.json --limit 5
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from difflib import SequenceMatcher
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
DEFAULT_DATASET = PROJECT_ROOT / "training" / "generated" / "eval.json"

sys.path.insert(0, str(BACKEND_DIR))

from translator import Translator  # noqa: E402


def normalize_text(value: str) -> str:
    return " ".join(value.split())


def similarity_score(reference: str, prediction: str) -> float:
    return SequenceMatcher(None, normalize_text(reference), normalize_text(prediction)).ratio()


def evaluate_cases(cases: list[dict], use_adapter: bool, limit: int | None) -> dict:
    translator = Translator(use_adapter=use_adapter)
    rows = []

    active_cases = cases[:limit] if limit else cases
    for index, case in enumerate(active_cases, start=1):
        prediction = translator.translate(
            case["src"],
            src_lang=case["src_lang"],
            tgt_lang=case["tgt_lang"],
        )
        reference = case["tgt"]
        score = similarity_score(reference, prediction)
        exact = normalize_text(reference) == normalize_text(prediction)
        rows.append(
            {
                "index": index,
                "src_lang": case["src_lang"],
                "source": case["src"],
                "reference": reference,
                "prediction": prediction,
                "similarity": score,
                "exact_match": exact,
            }
        )

    similarities = [row["similarity"] for row in rows]
    exact_matches = sum(1 for row in rows if row["exact_match"])

    return {
        "rows": rows,
        "count": len(rows),
        "exact_matches": exact_matches,
        "exact_match_rate": (exact_matches / len(rows)) if rows else 0.0,
        "avg_similarity": statistics.mean(similarities) if similarities else 0.0,
    }


def print_report(label: str, report: dict) -> None:
    print("=" * 72)
    print(f"{label}")
    print("=" * 72)
    print(f"Cases            : {report['count']}")
    print(f"Exact matches    : {report['exact_matches']} ({report['exact_match_rate']:.0%})")
    print(f"Avg similarity   : {report['avg_similarity']:.3f}")
    print()

    for row in report["rows"]:
        print(f"[{row['index']:02d}] {row['src_lang']} | sim={row['similarity']:.3f} | exact={row['exact_match']}")
        print(f"  SRC : {row['source']}")
        print(f"  REF : {row['reference']}")
        print(f"  PRED: {row['prediction']}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate base vs adapter translation quality.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument(
        "--mode",
        choices=("compare", "baseline", "adapter"),
        default="compare",
    )
    parser.add_argument("--limit", type=int, default=None, help="Evaluate only the first N rows.")
    args = parser.parse_args()

    if not args.dataset.exists():
        raise FileNotFoundError(
            f"Dataset not found: {args.dataset}. Run backend/tools/build_training_dataset.py first."
        )

    cases = json.loads(args.dataset.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"{args.dataset} must contain a non-empty JSON array.")

    if args.mode in {"compare", "baseline"}:
        baseline_report = evaluate_cases(cases, use_adapter=False, limit=args.limit)
        print_report("Baseline Model", baseline_report)
    else:
        baseline_report = None

    if args.mode in {"compare", "adapter"}:
        adapter_report = evaluate_cases(cases, use_adapter=True, limit=args.limit)
        print_report("Adapter Model", adapter_report)
    else:
        adapter_report = None

    if baseline_report and adapter_report:
        delta = adapter_report["avg_similarity"] - baseline_report["avg_similarity"]
        exact_delta = adapter_report["exact_matches"] - baseline_report["exact_matches"]
        print("=" * 72)
        print("Comparison")
        print("=" * 72)
        print(f"Similarity delta : {delta:+.3f}")
        print(f"Exact delta      : {exact_delta:+d}")


if __name__ == "__main__":
    main()
