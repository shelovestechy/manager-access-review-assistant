from __future__ import annotations

from typing import Any, Sequence


def build_access_change_draft(
    report: dict[str, Any],
    *,
    additions: Sequence[str] = (),
    removals: Sequence[str] = (),
    business_reason: str = "Not provided; Service Desk should request clarification.",
) -> str:
    """Create a draft only. This function never calls an identity or ticketing system."""
    if not additions and not removals:
        raise ValueError("at least one requested addition or removal is required")

    employee = report["employee"]
    requester_id = report["authorization"]["requester_id"]
    lines = [
        f"Subject: Access change request - {employee['display_name']}",
        "",
        "Hello Service Desk,",
        "",
        f"Please review the following access changes for {employee['display_name']} ({employee['user_id']}).",
        f"Role: {employee['job_title']}",
        f"Department: {employee['department']}",
        f"Location: {employee['office_location']}",
        "",
    ]
    if additions:
        lines.append("Requested additions:")
        lines.extend(f"- {item}" for item in additions)
        lines.append("")
    if removals:
        lines.append("Requested removals:")
        lines.extend(f"- {item}" for item in removals)
        lines.append("")
    lines.extend(
        [
            f"Business reason: {business_reason}",
            f"Requesting manager: {requester_id}",
            "",
            "Please validate eligibility and implement only through the normal approval process.",
            "The assistant created this draft but did not make any access changes.",
        ]
    )
    return "\n".join(lines)
