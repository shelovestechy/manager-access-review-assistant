from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Employee:
    user_id: str
    display_name: str
    job_title: str
    department: str
    manager_id: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Employee":
        required = ("user_id", "display_name", "job_title", "department", "manager_id")
        _require_fields(value, required, "employee")
        return cls(**{name: str(value[name]) for name in required})


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
class Snapshot:
    employees: tuple[Employee, ...]
    entitlements: tuple[Entitlement, ...]


def _require_fields(value: dict[str, Any], names: tuple[str, ...], label: str) -> None:
    missing = [name for name in names if name not in value]
    if missing:
        raise ValueError(f"{label} is missing required fields: {', '.join(missing)}")
