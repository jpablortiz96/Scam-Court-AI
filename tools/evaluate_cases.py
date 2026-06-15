"""Run Scam Court AI's safety evaluation dataset.

This module is intentionally independent of Gradio and the vision model. It uses
the configured text backend through the same backend router as the application.
The default backend remains the deterministic heuristic engine.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from courtroom import get_backend  # noqa: E402

DEFAULT_CASES_PATH = ROOT / "data" / "evaluation_cases.json"
DEFAULT_OUTPUT_DIR = ROOT / "outputs"
VALID_VERDICTS = {"STOP", "VERIFY_FIRST", "LOW_VISIBLE_RISK"}


def normalize_verdict(value: str) -> str:
    """Normalize UI verdict spelling to the evaluation schema."""
    normalized = str(value).strip().upper().replace("-", "_").replace(" ", "_")
    if normalized.startswith("VERIFY_FIRST"):
        return "VERIFY_FIRST"
    if normalized.startswith("LOW_VISIBLE_RISK"):
        return "LOW_VISIBLE_RISK"
    if normalized.startswith("STOP"):
        return "STOP"
    return normalized


def load_cases(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        cases = json.load(handle)
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"Evaluation dataset must be a non-empty JSON array: {path}")

    required = {
        "id",
        "category",
        "input_text",
        "expected_verdict",
        "expected_min_score",
        "expected_max_score",
        "rationale",
        "must_not_return_low_risk",
        "tags",
    }
    seen_ids: set[str] = set()
    for case in cases:
        missing = required.difference(case)
        if missing:
            raise ValueError(f"Case {case.get('id', '<unknown>')} missing fields: {sorted(missing)}")
        if case["id"] in seen_ids:
            raise ValueError(f"Duplicate evaluation case id: {case['id']}")
        seen_ids.add(case["id"])
        if case["expected_verdict"] not in VALID_VERDICTS:
            raise ValueError(f"Invalid expected verdict in {case['id']}: {case['expected_verdict']}")
        if not 0 <= int(case["expected_min_score"]) <= int(case["expected_max_score"]) <= 100:
            raise ValueError(f"Invalid score range in {case['id']}")
    return cases


def evaluate_cases(
    cases: list[dict[str, Any]],
    analyze: Callable[[str], Any] | None = None,
) -> dict[str, Any]:
    backend = None
    if analyze is None:
        backend = get_backend()
        analyze = backend.analyze

    results: list[dict[str, Any]] = []
    category_counts: dict[str, dict[str, int | float]] = defaultdict(
        lambda: {
            "total": 0,
            "passed": 0,
            "false_low_risk": 0,
            "safety_failures": 0,
            "risk_score_total": 0,
        }
    )

    for case in cases:
        try:
            report = analyze(case["input_text"])
            report_data = report.to_dict() if hasattr(report, "to_dict") else dict(report)
            actual_verdict = normalize_verdict(report_data.get("shield_verdict", ""))
            actual_score = int(report_data.get("risk_score", -1))
            error = None
        except Exception as exc:  # Evaluation should report a case failure, not abort the batch.
            report_data = {}
            actual_verdict = "ERROR"
            actual_score = -1
            error = f"{type(exc).__name__}: {exc}"

        verdict_match = actual_verdict == case["expected_verdict"]
        score_in_range = (
            int(case["expected_min_score"])
            <= actual_score
            <= int(case["expected_max_score"])
        )
        false_low_risk = bool(
            case["must_not_return_low_risk"] and actual_verdict == "LOW_VISIBLE_RISK"
        )
        stop_miss = bool(case["expected_verdict"] == "STOP" and actual_verdict != "STOP")
        safety_failure = bool(error or false_low_risk or stop_miss)
        passed = bool(not error and verdict_match and score_in_range and not false_low_risk)

        result = {
            "id": case["id"],
            "category": case["category"],
            "expected_verdict": case["expected_verdict"],
            "actual_verdict": actual_verdict,
            "expected_min_score": case["expected_min_score"],
            "expected_max_score": case["expected_max_score"],
            "actual_score": actual_score,
            "verdict_match": verdict_match,
            "score_in_range": score_in_range,
            "false_low_risk": false_low_risk,
            "safety_failure": safety_failure,
            "passed": passed,
            "rationale": case["rationale"],
            "tags": case["tags"],
            "detected_patterns": [
                item.get("id") for item in report_data.get("detected_patterns", [])
            ],
            "safety_policy_applied": report_data.get("safety_policy_applied", False),
            "safety_policy_tags": report_data.get("safety_policy_tags", []),
            "model_backend": report_data.get("model_backend"),
            "error": error,
        }
        results.append(result)

        category = category_counts[case["category"]]
        category["total"] += 1
        category["passed"] += int(passed)
        category["false_low_risk"] += int(false_low_risk)
        category["safety_failures"] += int(safety_failure)
        if actual_score >= 0:
            category["risk_score_total"] += actual_score

    total = len(results)
    passed = sum(item["passed"] for item in results)
    verdict_matches = sum(item["verdict_match"] for item in results)
    score_matches = sum(item["score_in_range"] for item in results)
    false_low_risk = sum(item["false_low_risk"] for item in results)
    safety_failures = sum(item["safety_failure"] for item in results)
    stop_cases = [item for item in results if item["expected_verdict"] == "STOP"]
    stop_hits = sum(item["actual_verdict"] == "STOP" for item in stop_cases)
    protected_cases = sum(bool(case["must_not_return_low_risk"]) for case in cases)

    for stats in category_counts.values():
        stats["pass_rate"] = round(stats["passed"] / stats["total"], 4)
        stats["average_risk_score"] = round(
            stats["risk_score_total"] / stats["total"], 2
        )
        del stats["risk_score_total"]

    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "dataset_case_count": total,
            "backend": next(
                (item["model_backend"] for item in results if item["model_backend"]),
                type(backend).__name__ if backend else "custom_analyzer",
            ),
        },
        "summary": {
            "total_cases": total,
            "passed_cases": passed,
            "failed_cases": total - passed,
            "pass_rate": round(passed / total, 4),
            "verdict_accuracy": round(verdict_matches / total, 4),
            "score_range_accuracy": round(score_matches / total, 4),
            "false_low_risk_count": false_low_risk,
            "false_reassurance_rate": round(
                false_low_risk / protected_cases, 4
            ) if protected_cases else 0.0,
            "safety_failure_count": safety_failures,
            "stop_recall": round(stop_hits / len(stop_cases), 4) if stop_cases else 0.0,
        },
        "categories": dict(sorted(category_counts.items())),
        "results": results,
    }


def render_markdown(evaluation: dict[str, Any]) -> str:
    summary = evaluation["summary"]
    metadata = evaluation["metadata"]
    lines = [
        "# Scam Court AI Evaluation Report",
        "",
        f"- Generated: `{metadata['generated_at']}`",
        f"- Backend: `{metadata['backend']}`",
        f"- Cases: **{summary['total_cases']}**",
        f"- Pass rate: **{summary['pass_rate']:.1%}**",
        f"- Verdict accuracy: **{summary['verdict_accuracy']:.1%}**",
        f"- Score-range accuracy: **{summary['score_range_accuracy']:.1%}**",
        f"- False reassurance rate: **{summary['false_reassurance_rate']:.1%}**",
        f"- STOP recall: **{summary['stop_recall']:.1%}**",
        f"- Safety failures: **{summary['safety_failure_count']}**",
        "",
        "## Category Summary",
        "",
        "| Category | Passed | Total | Pass rate | Avg. risk score | False LOW RISK | Safety failures |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for category, stats in evaluation["categories"].items():
        lines.append(
            f"| {category} | {stats['passed']} | {stats['total']} | "
            f"{stats['pass_rate']:.1%} | {stats['average_risk_score']:.2f} | "
            f"{stats['false_low_risk']} | "
            f"{stats['safety_failures']} |"
        )

    lines.extend(
        [
            "",
            "## Case Results",
            "",
            "| Case | Category | Expected | Actual | Score | Result |",
            "|---|---|---|---|---:|---|",
        ]
    )
    for item in evaluation["results"]:
        expected_range = f"{item['expected_min_score']}-{item['expected_max_score']}"
        status = "PASS" if item["passed"] else "FAIL"
        if item["false_low_risk"]:
            status = "SAFETY FAIL: FALSE LOW RISK"
        elif item["error"]:
            status = f"ERROR: {item['error']}"
        lines.append(
            f"| {item['id']} | {item['category']} | {item['expected_verdict']} "
            f"({expected_range}) | {item['actual_verdict']} | "
            f"{item['actual_score']} | {status} |"
        )

    failures = [item for item in evaluation["results"] if not item["passed"]]
    lines.extend(["", "## Failures", ""])
    if not failures:
        lines.append("No failures.")
    else:
        for item in failures:
            lines.append(
                f"- **{item['id']}**: expected `{item['expected_verdict']}` "
                f"and score `{item['expected_min_score']}-{item['expected_max_score']}`, "
                f"received `{item['actual_verdict']}` and `{item['actual_score']}`."
            )
    lines.append("")
    return "\n".join(lines)


def write_reports(evaluation: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "evaluation_report.json"
    markdown_path = output_dir / "evaluation_report.md"
    json_path.write_text(
        json.dumps(evaluation, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(evaluation), encoding="utf-8")
    return json_path, markdown_path


def print_summary(evaluation: dict[str, Any]) -> None:
    summary = evaluation["summary"]
    print(
        "Scam Court AI evaluation | "
        f"cases={summary['total_cases']} "
        f"passed={summary['passed_cases']} "
        f"pass_rate={summary['pass_rate']:.1%} "
        f"verdict_accuracy={summary['verdict_accuracy']:.1%} "
        f"false_reassurance={summary['false_reassurance_rate']:.1%} "
        f"stop_recall={summary['stop_recall']:.1%} "
        f"safety_failures={summary['safety_failure_count']}"
    )
    print()
    print(
        f"{'Category':40} {'Pass':>7} {'Avg score':>10} "
        f"{'False low':>10} {'Safety':>8}"
    )
    print("-" * 82)
    for category, stats in evaluation["categories"].items():
        passed = f"{stats['passed']}/{stats['total']}"
        print(
            f"{category:40} {passed:>7} {stats['average_risk_score']:>10.2f} "
            f"{stats['false_low_risk']:>10} {stats['safety_failures']:>8}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--fail-on-safety",
        action="store_true",
        help="Return a non-zero exit code when any safety failure is found.",
    )
    args = parser.parse_args()

    evaluation = evaluate_cases(load_cases(args.cases))
    json_path, markdown_path = write_reports(evaluation, args.output_dir)
    print_summary(evaluation)
    print(f"\nJSON report: {json_path}")
    print(f"Markdown report: {markdown_path}")
    if args.fail_on_safety and evaluation["summary"]["safety_failure_count"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
