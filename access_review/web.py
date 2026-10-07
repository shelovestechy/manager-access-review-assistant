from __future__ import annotations

import argparse
import json
from datetime import date
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlsplit

from .analyzer import analyze_access
from .repository import load_snapshot
from .summary import OllamaRanker, summarize_report
from .service_desk import build_access_change_draft


ASSET_ROOT = Path(__file__).with_name("web_assets")
DEFAULT_SNAPSHOT = Path(__file__).with_name("demo_data") / "sample_access_snapshot.json"
MAX_REQUEST_BYTES = 64 * 1024


def make_handler(snapshot_path: str | Path, *, summary_ranker=None, scenario_manifest=None):
    snapshot = load_snapshot(snapshot_path)
    manifest_path = Path(scenario_manifest) if scenario_manifest else Path(__file__).parents[1] / "scenarios/cases.json"
    scenarios = {}
    catalogue = []
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for case in manifest["cases"]:
            # Only trusted startup configuration can name files, never HTTP input.
            scenarios[case["id"]] = load_snapshot(manifest_path.parent / case["snapshot"])
            catalogue.append({key: case[key] for key in
                              ("id", "title", "employee", "manager", "review_date")})

    def selected_snapshot(payload):
        scenario_id = payload.get("scenario_id", "")
        if not isinstance(scenario_id, str):
            raise ValueError("scenario_id must be a string")
        if not scenario_id:
            return snapshot
        if scenario_id not in scenarios:
            raise ValueError("Unknown demo scenario")
        return scenarios[scenario_id]

    class AccessReviewHandler(BaseHTTPRequestHandler):
        server_version = "AccessReviewDemo/1.0"

        def version_string(self) -> str:
            return self.server_version

        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            path = urlsplit(self.path).path
            assets = {
                "/": ("index.html", "text/html; charset=utf-8"),
                "/assets/styles.css": ("styles.css", "text/css; charset=utf-8"),
                "/assets/app.js": ("app.js", "text/javascript; charset=utf-8"),
                "/assets/favicon.svg": ("favicon.svg", "image/svg+xml"),
            }
            if path == "/api/demo-scenarios":
                self._send_json(HTTPStatus.OK, {"mode": "synthetic-demo-only", "scenarios": catalogue})
                return
            if path == "/api/health":
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": "ok",
                        "mode": "synthetic-read-only-demo",
                        "write_integrations": False,
                    },
                )
                return
            asset = assets.get(path)
            if asset is None:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            filename, content_type = asset
            self._send_bytes(HTTPStatus.OK, (ASSET_ROOT / filename).read_bytes(), content_type)

        def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            path = urlsplit(self.path).path
            try:
                payload = self._read_json()
                if path == "/api/summary":
                    report = _create_review(selected_snapshot(payload), payload)
                    self._send_json(HTTPStatus.OK, summarize_report(report, summary_ranker))
                    return
                if path == "/api/review":
                    report = _create_review(selected_snapshot(payload), payload)
                    self._send_json(HTTPStatus.OK, report)
                    return
                if path == "/api/service-desk-draft":
                    report = _create_review(selected_snapshot(payload), payload)
                    additions = _string_list(payload.get("additions", []), "additions")
                    removals = _string_list(payload.get("removals", []), "removals")
                    reason = _required_string(payload, "reason", max_length=2000)
                    draft = build_access_change_draft(
                        report,
                        additions=additions,
                        removals=removals,
                        business_reason=reason,
                    )
                    self._send_json(
                        HTTPStatus.OK,
                        {
                            "draft": draft,
                            "submitted": False,
                            "notice": "Draft only. No ticket or access change was submitted.",
                        },
                    )
                    return
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            except PermissionError as exc:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": str(exc)})
            except (ValueError, json.JSONDecodeError) as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

        def _read_json(self) -> dict[str, Any]:
            content_type = self.headers.get("Content-Type", "")
            if "application/json" not in content_type:
                raise ValueError("Content-Type must be application/json")
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise ValueError("invalid Content-Length") from exc
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise ValueError("request body must be between 1 byte and 64 KiB")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("request body must be a JSON object")
            return payload

        def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self._send_bytes(status, body, "application/json; charset=utf-8", no_store=True)

        def _send_bytes(
            self,
            status: HTTPStatus,
            body: bytes,
            content_type: str,
            *,
            no_store: bool = False,
        ) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
                "base-uri 'none'; form-action 'self'",
            )
            if no_store:
                self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    return AccessReviewHandler


def _create_review(snapshot, payload: dict[str, Any]) -> dict[str, Any]:
    user_id = _required_string(payload, "user_id")
    requester_id = _required_string(payload, "requester_id")
    as_of_value = payload.get("as_of")
    try:
        as_of = date.fromisoformat(str(as_of_value)) if as_of_value else None
    except ValueError as exc:
        raise ValueError("as_of must use YYYY-MM-DD format") from exc
    return analyze_access(snapshot, user_id, requester_id, as_of=as_of)


def _required_string(
    payload: dict[str, Any], field_name: str, *, max_length: int = 200
) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    result = value.strip()
    if len(result) > max_length:
        raise ValueError(f"{field_name} may contain at most {max_length} characters")
    return result


def _string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be an array")
    if len(value) > 50:
        raise ValueError(f"{field_name} may contain at most 50 items")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field_name} must contain non-empty strings")
        normalized = item.strip()
        if len(normalized) > 200:
            raise ValueError(f"{field_name} items may contain at most 200 characters")
        result.append(normalized)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local read-only access review demo.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: localhost)")
    parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    parser.add_argument(
        "--snapshot", type=Path, default=DEFAULT_SNAPSHOT, help="Synthetic snapshot path"
    )
    parser.add_argument("--ollama-model", help="Optional locally installed model for evidence ordering")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    ranker = OllamaRanker(args.ollama_model) if args.ollama_model else None
    server = ThreadingHTTPServer((args.host, args.port), make_handler(args.snapshot, summary_ranker=ranker))
    print(f"Read-only demo: http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

