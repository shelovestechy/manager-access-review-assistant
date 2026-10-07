from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Sequence

from .analyzer import analyze_access
from .repository import load_snapshot
from .service_desk import build_access_change_draft


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create an explainable access review from a synthetic snapshot."
    )
    parser.add_argument("snapshot", type=Path, help="Path to the JSON snapshot")
    parser.add_argument("--user", required=True, help="Employee user ID")
    parser.add_argument(
        "--manager", required=True, help="Requester ID; must match direct manager in AD and Entra ID"
    )
    parser.add_argument("--as-of", type=date.fromisoformat, help="Review date in YYYY-MM-DD format")
    parser.add_argument(
        "--draft-add", action="append", default=[], metavar="ACCESS", help="Add to Service Desk draft"
    )
    parser.add_argument(
        "--draft-remove", action="append", default=[], metavar="ACCESS", help="Remove in Service Desk draft"
    )
    parser.add_argument("--reason", help="Business reason for the Service Desk draft")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = analyze_access(
            load_snapshot(args.snapshot), args.user, args.manager, as_of=args.as_of
        )
        if args.draft_add or args.draft_remove:
            report["access_change_draft"] = build_access_change_draft(
                report,
                additions=args.draft_add,
                removals=args.draft_remove,
                business_reason=args.reason or "Not provided; Service Desk should request clarification.",
            )
    except (PermissionError, ValueError) as exc:
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
    account = report["account_status"]
    lines = [
        f"Access review: {employee['display_name']}",
        (
            f"Role: {employee['job_title']} | Department: {employee['department']} | "
            f"Location: {employee['office_location']}"
        ),
        f"Authorized manager: {report['authorization']['requester_id']} (AD + Entra ID)",
        "",
        "AD account",
        f"- Status: {account['status']}",
        f"- Expires: {account['ad_account_expires_at'] or 'not configured'}",
    ]
    for message in account["messages"]:
        lines.append(f"- {message}")

    lines.extend(
        [
            "",
            f"{summary['total']} access items found",
            f"- {summary['expected']} appear role-aligned",
            f"- {summary['organization_wide']} are organization-wide",
            f"- {summary['review']} require review",
            f"- {summary['suggestions']} possible missing access items",
        ]
    )

    review_items = report["categories"]["review"]
    if review_items:
        lines.extend(["", "Review findings"])
        for item in review_items:
            lines.append(f"- {item['name']}: {', '.join(item['evidence'])}")

    suggestions = report["access_suggestions"]
    if suggestions:
        lines.extend(["", "Access suggestions (ICT / Service Desk validation required)"])
        for item in suggestions:
            reason = ", ".join(item["matched_attributes"])
            lines.append(f"- {item['name']}: {item['purpose']} ({reason})")

    if account.get("service_desk_notice_draft"):
        lines.extend(["", "Service Desk account-expiry draft", account["service_desk_notice_draft"]])
    if report.get("access_change_draft"):
        lines.extend(["", "Service Desk access-change draft", report["access_change_draft"]])

    lines.extend(["", report["service_desk_next_step"], report["decision_boundary"]])
    return "\n".join(lines)
