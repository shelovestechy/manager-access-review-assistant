from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class Employee:
    user_id: str
    display_name: str
    job_title: str
    department: str
    office_location: str
    ad_manager_id: str
    entra_manager_id: str
    ad_account_expires_at: date | None
    contract_end_date: date | None

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Employee":
        required = (
            "user_id",
            "display_name",
            "job_title",
            "department",
            "office_location",
            "ad_manager_id",
            "entra_manager_id",
        )
        _require_fields(value, required, "employee")
        for name in required:
            if not isinstance(value[name], str):
                raise ValueError(f"employee.{name} must be a string")
        return cls(
            **{name: str(value[name]) for name in required},
            ad_account_expires_at=_optional_date(value.get("ad_account_expires_at"), "ad_account_expires_at"),
            contract_end_date=_optional_date(value.get("contract_end_date"), "contract_end_date"),
        )


@dataclass(frozen=True)
class Entitlement:
    user_id: str
    source: str
    resource_type: str
    name: str
    assignment: str
    purpose: str = ""
    expected_departments: tuple[str, ...] = field(default_factory=tuple)
    risk_tags: tuple[str, ...] = field(default_factory=tuple)
    organization_wide: bool = False

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Entitlement":
        required = ("user_id", "source", "resource_type", "name", "assignment")
        _require_fields(value, required, "entitlement")
        assignment = str(value["assignment"])
        if assignment not in {"direct", "transitive"}:
            raise ValueError("entitlement.assignment must be 'direct' or 'transitive'")
        return cls(
            user_id=str(value["user_id"]),
            source=str(value["source"]),
            resource_type=str(value["resource_type"]),
            name=str(value["name"]),
            assignment=assignment,
            purpose=str(value.get("purpose", "")),
            expected_departments=tuple(str(item) for item in value.get("expected_departments", [])),
            risk_tags=tuple(str(item) for item in value.get("risk_tags", [])),
            organization_wide=bool(value.get("organization_wide", False)),
        )


@dataclass(frozen=True)
class AccessSuggestion:
    name: str
    source: str
    resource_type: str
    purpose: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "AccessSuggestion":
        required = ("name", "source", "resource_type", "purpose")
        _require_fields(value, required, "access suggestion")
        return cls(**{name: str(value[name]) for name in required})


@dataclass(frozen=True)
class AccessProfile:
    name: str
    job_titles: tuple[str, ...]
    departments: tuple[str, ...]
    office_locations: tuple[str, ...]
    suggestions: tuple[AccessSuggestion, ...]

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "AccessProfile":
        _require_fields(value, ("name", "suggestions"), "access profile")
        suggestions = value["suggestions"]
        if not isinstance(suggestions, list):
            raise ValueError("access profile suggestions must be an array")
        return cls(
            name=str(value["name"]),
            job_titles=tuple(str(item) for item in value.get("job_titles", [])),
            departments=tuple(str(item) for item in value.get("departments", [])),
            office_locations=tuple(str(item) for item in value.get("office_locations", [])),
            suggestions=tuple(AccessSuggestion.from_dict(item) for item in suggestions),
        )


@dataclass(frozen=True)
class Snapshot:
    employees: tuple[Employee, ...]
    entitlements: tuple[Entitlement, ...]
    access_profiles: tuple[AccessProfile, ...]


def _optional_date(value: Any, field_name: str) -> date | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format") from exc


def _require_fields(value: dict[str, Any], names: tuple[str, ...], label: str) -> None:
    missing = [name for name in names if name not in value]
    if missing:
        raise ValueError(f"{label} is missing required fields: {', '.join(missing)}")

