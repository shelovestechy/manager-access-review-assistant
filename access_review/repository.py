from __future__ import annotations

import json
from pathlib import Path

from .models import AccessProfile, Employee, Entitlement, Snapshot


def load_snapshot(path: str | Path) -> Snapshot:
    source = Path(path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"snapshot file not found: {source}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"snapshot is not valid JSON: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise ValueError("snapshot root must be a JSON object")

    employees = payload.get("employees")
    entitlements = payload.get("entitlements")
    access_profiles = payload.get("access_profiles", [])
    if not isinstance(employees, list) or not isinstance(entitlements, list):
        raise ValueError("snapshot must contain employees and entitlements arrays")
    if not isinstance(access_profiles, list):
        raise ValueError("snapshot access_profiles must be an array")

    return Snapshot(
        employees=tuple(Employee.from_dict(item) for item in employees),
        entitlements=tuple(Entitlement.from_dict(item) for item in entitlements),
        access_profiles=tuple(AccessProfile.from_dict(item) for item in access_profiles),
    )
