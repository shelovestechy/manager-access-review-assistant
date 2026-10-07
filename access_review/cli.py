from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .analyzer import analyze_access
from .repository import load_snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create an explainable access review from a synthetic snapshot."
    )
    parser.add_argument("snapshot", type=Path, help="Path to the JSON snapshot")
    parser.add_argument("--user", required=True, help="Employee user ID")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = analyze_access(load_snapshot(args.snapshot), args.user)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text_report(report))
    return 0


def format_text_report(report: dict[str, Any]) -> str:
    employee = report["employee"]
    summary = report["summary"]
    lines = [
        f"Access review: {employee['display_name']}",
        f"Role: {employee['job_title']} | Department: {employee['department']}",
        "",
        f"{summary['total']} access items found",
        f"- {summary['expected']} appear role-aligned",
        f"- {summary['organization_wide']} are organization-wide",
        f"- {summary['review']} require review",
    ]

    review_items = report["categories"]["review"]
    if review_items:
        lines.extend(["", "Review findings"])
        for item in review_items:
            lines.append(f"- {item['name']}: {', '.join(item['evidence'])}")

    lines.extend(["", report["decision_boundary"]])
    return "\n".join(lines)
