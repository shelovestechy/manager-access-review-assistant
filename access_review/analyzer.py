from __future__ import annotations

from datetime import date
from typing import Any

from .models import AccessProfile, Employee, Entitlement, Snapshot


EXPIRY_WARNING_DAYS = 90


def analyze_access(
    snapshot: Snapshot,
    user_id: str,
    requester_id: str,
    *,
    as_of: date | None = None,
) -> dict[str, Any]:
    employee = _find_employee(snapshot, user_id)
    _authorize_direct_manager(employee, requester_id)
    review_date = as_of or date.today()
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

    account_status = _account_status(employee, review_date)
    suggestions = _access_suggestions(employee, entitlements, snapshot.access_profiles)
    return {
        "authorization": {
            "requester_id": requester_id,
            "authorized": True,
            "basis": "Requester is the direct manager in both AD and Entra ID.",
        },
        "employee": {
            "user_id": employee.user_id,
            "display_name": employee.display_name,
            "job_title": employee.job_title,
            "department": employee.department,
            "office_location": employee.office_location,
        },
        "account_status": account_status,
        "summary": {
            "total": len(entitlements),
            "expected": len(expected),
            "organization_wide": len(general),
            "review": len(review),
            "suggestions": len(suggestions),
        },
        "categories": {
            "expected": expected,
            "organization_wide": general,
            "review": review,
        },
        "access_suggestions": suggestions,
        "service_desk_next_step": (
            "Ask ICT or Service Desk to validate and implement any requested change through the normal approval process."
        ),
        "decision_boundary": (
            "Decision support only. The assistant cannot grant, remove, approve, or deny access."
        ),
    }


def _find_employee(snapshot: Snapshot, user_id: str) -> Employee:
    matches = [employee for employee in snapshot.employees if employee.user_id == user_id]
    if not matches:
        raise ValueError(f"employee not found: {user_id}")
    if len(matches) > 1:
        raise ValueError(f"duplicate employee id: {user_id}")
    return matches[0]


def _authorize_direct_manager(employee: Employee, requester_id: str) -> None:
    ad_match = employee.ad_manager_id == requester_id
    entra_match = employee.entra_manager_id == requester_id
    if not (ad_match and entra_match):
        raise PermissionError(
            "access denied: requester must be the employee's direct manager in both AD and Entra ID"
        )


def _account_status(employee: Employee, as_of: date) -> dict[str, Any]:
    expiry = employee.ad_account_expires_at
    if expiry is None:
        return {
            "status": "no_expiry_configured",
            "ad_account_expires_at": None,
            "days_remaining": None,
            "requires_service_desk_notice": False,
            "messages": ["AD does not contain an account expiry date."],
        }

    days_remaining = (expiry - as_of).days
    messages: list[str] = []
    if days_remaining < 0:
        status = "expired"
        messages.append(f"AD account expired {abs(days_remaining)} days ago.")
    elif days_remaining <= EXPIRY_WARNING_DAYS:
        status = "expiring_soon"
        messages.append(f"AD account expires in {days_remaining} days.")
    else:
        status = "active"

    contract_mismatch = bool(employee.contract_end_date and employee.contract_end_date > expiry)
    if contract_mismatch:
        messages.append(
            "AD account expiry is earlier than the recorded contract end date; Service Desk should verify the account date."
        )

    requires_notice = status in {"expired", "expiring_soon"} or contract_mismatch
    result: dict[str, Any] = {
        "status": status,
        "ad_account_expires_at": expiry.isoformat(),
        "days_remaining": days_remaining,
        "contract_end_date": (
            employee.contract_end_date.isoformat() if employee.contract_end_date else None
        ),
        "contract_date_mismatch": contract_mismatch,
        "requires_service_desk_notice": requires_notice,
        "messages": messages,
    }
    if requires_notice:
        result["service_desk_notice_draft"] = _expiry_notice_draft(employee, result)
    return result


def _expiry_notice_draft(employee: Employee, account_status: dict[str, Any]) -> str:
    contract_line = (
        f"Recorded contract end date: {account_status['contract_end_date']}\n"
        if account_status.get("contract_end_date")
        else ""
    )
    return (
        f"Subject: Please verify AD account expiry - {employee.display_name}\n\n"
        "Hello Service Desk,\n\n"
        f"Please verify the AD account expiry for {employee.display_name} ({employee.user_id}).\n"
        f"Current AD account expiry: {account_status['ad_account_expires_at']}\n"
        f"{contract_line}"
        "The assistant has not changed the account. Please validate the dates and follow the normal approval process.\n\n"
        f"Manager: {employee.ad_manager_id}"
    )


def _access_suggestions(
    employee: Employee,
    current_entitlements: list[Entitlement],
    profiles: tuple[AccessProfile, ...],
) -> list[dict[str, Any]]:
    current_names = {item.name.casefold() for item in current_entitlements}
    suggestions: dict[str, dict[str, Any]] = {}
    for profile in profiles:
        matched_attributes = _matched_profile_attributes(employee, profile)
        if matched_attributes is None:
            continue
        for suggestion in profile.suggestions:
            key = suggestion.name.casefold()
            if key in current_names:
                continue
            suggestions[key] = {
                "name": suggestion.name,
                "source": suggestion.source,
                "resource_type": suggestion.resource_type,
                "purpose": suggestion.purpose,
                "profile": profile.name,
                "matched_attributes": matched_attributes,
                "notice": "Suggestion only; ICT or Service Desk must validate the need and eligibility.",
            }
    return sorted(suggestions.values(), key=lambda item: (item["source"], item["name"]))


def _matched_profile_attributes(
    employee: Employee, profile: AccessProfile
) -> list[str] | None:
    checks = (
        ("job_title", employee.job_title, profile.job_titles),
        ("department", employee.department, profile.departments),
        ("office_location", employee.office_location, profile.office_locations),
    )
    matched: list[str] = []
    for label, employee_value, allowed_values in checks:
        if not allowed_values:
            continue
        if employee_value not in allowed_values:
            return None
        matched.append(f"{label}={employee_value}")
    return matched or None


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
