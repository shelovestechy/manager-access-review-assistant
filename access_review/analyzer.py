from __future__ import annotations

from typing import Any

from .models import Employee, Entitlement, Snapshot


def analyze_access(snapshot: Snapshot, user_id: str) -> dict[str, Any]:
    employee = _find_employee(snapshot, user_id)
    entitlements = [item for item in snapshot.entitlements if item.user_id == user_id]

    expected: list[dict[str, Any]] = []
    general: list[dict[str, Any]] = []
    review: list[dict[str, Any]] = []

    for entitlement in sorted(entitlements, key=lambda item: (item.source, item.name)):
        evidence = _review_evidence(employee, entitlement)
        item = _as_report_item(entitlement)
        if evidence:
            item["evidence"] = evidence
            review.append(item)
        elif entitlement.organization_wide:
            general.append(item)
        else:
            expected.append(item)

    return {
        "employee": {
            "user_id": employee.user_id,
            "display_name": employee.display_name,
            "job_title": employee.job_title,
            "department": employee.department,
            "manager_id": employee.manager_id,
        },
        "summary": {
            "total": len(entitlements),
            "expected": len(expected),
            "organization_wide": len(general),
            "review": len(review),
        },
        "categories": {
            "expected": expected,
            "organization_wide": general,
            "review": review,
        },
        "decision_boundary": "Human review required. No access change has been made.",
    }


def _find_employee(snapshot: Snapshot, user_id: str) -> Employee:
    matches = [employee for employee in snapshot.employees if employee.user_id == user_id]
    if not matches:
        raise ValueError(f"employee not found: {user_id}")
    if len(matches) > 1:
        raise ValueError(f"duplicate employee id: {user_id}")
    return matches[0]


def _review_evidence(employee: Employee, entitlement: Entitlement) -> list[str]:
    evidence: list[str] = []
    if entitlement.expected_departments and employee.department not in entitlement.expected_departments:
        allowed = ", ".join(entitlement.expected_departments)
        evidence.append(
            f"department mismatch: employee is in {employee.department}; expected: {allowed}"
        )
    if "privileged" in entitlement.risk_tags:
        evidence.append("privileged access")
    if not entitlement.purpose.strip():
        evidence.append("access purpose is missing")
    if "dormant" in entitlement.risk_tags:
        evidence.append("access is marked dormant")
    return evidence


def _as_report_item(entitlement: Entitlement) -> dict[str, Any]:
    return {
        "name": entitlement.name,
        "source": entitlement.source,
        "resource_type": entitlement.resource_type,
        "assignment": entitlement.assignment,
        "purpose": entitlement.purpose or None,
        "risk_tags": list(entitlement.risk_tags),
    }
