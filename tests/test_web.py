from __future__ import annotations

import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from access_review.web import make_handler


FIXTURE = Path(__file__).parents[1] / "access_review" / "demo_data" / "sample_access_snapshot.json"


class WebDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(FIXTURE))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        host, port = cls.server.server_address
        cls.base_url = f"http://{host}:{port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_health_endpoint_declares_read_only_mode(self) -> None:
        with urlopen(f"{self.base_url}/api/health") as response:
            body = json.loads(response.read())
            self.assertEqual(body["mode"], "synthetic-read-only-demo")
            self.assertFalse(body["write_integrations"])
            self.assertEqual(response.headers["X-Frame-Options"], "DENY")
            self.assertEqual(response.headers["Server"], "AccessReviewDemo/1.0")
            self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])

    def test_index_is_served_without_external_assets(self) -> None:
        with urlopen(f"{self.base_url}/") as response:
            html = response.read().decode("utf-8")
            self.assertIn("Access reviews that explain themselves", html)
            self.assertIn("No write access. Ever.", html)
            self.assertNotIn("https://", html)

    def test_authorized_manager_can_open_review(self) -> None:
        status, report = self.post(
            "/api/review",
            {
                "user_id": "aku.ankka",
                "requester_id": "roope.ankka",
                "as_of": "2026-10-07",
            },
        )
        self.assertEqual(status, 200)
        self.assertTrue(report["authorization"]["authorized"])
        self.assertEqual(report["account_status"]["status"], "expiring_soon")

    def test_unverified_manager_receives_forbidden_response(self) -> None:
        status, body = self.post(
            "/api/review",
            {
                "user_id": "aku.ankka",
                "requester_id": "other.manager",
                "as_of": "2026-10-07",
            },
        )
        self.assertEqual(status, 403)
        self.assertIn("access denied", body["error"])

    def test_service_desk_endpoint_returns_draft_without_submission(self) -> None:
        status, body = self.post(
            "/api/service-desk-draft",
            {
                "user_id": "aku.ankka",
                "requester_id": "roope.ankka",
                "as_of": "2026-10-07",
                "additions": ["HR-Case-Management-Users"],
                "removals": ["Rahasailio-Admin"],
                "reason": "Align access with current HR duties.",
            },
        )
        self.assertEqual(status, 200)
        self.assertFalse(body["submitted"])
        self.assertIn("did not make any access changes", body["draft"])

    def test_oversized_identity_input_is_rejected(self) -> None:
        status, body = self.post(
            "/api/review",
            {
                "user_id": "x" * 201,
                "requester_id": "roope.ankka",
                "as_of": "2026-10-07",
            },
        )
        self.assertEqual(status, 400)
        self.assertIn("at most 200 characters", body["error"])

    def test_summary_reauthorizes_instead_of_trusting_browser_report(self):
        status, body = self.post("/api/summary", {
            "user_id": "aku.ankka", "requester_id": "other.manager",
            "authorization": {"authorized": True},
        })
        self.assertEqual(status, 403)
        self.assertNotIn("evidence", body)

    def test_authorized_summary_is_cited_and_offline_by_default(self):
        status, body = self.post("/api/summary", {
            "user_id": "aku.ankka", "requester_id": "roope.ankka",
            "as_of": "2026-10-07",
        })
        self.assertEqual(status, 200)
        self.assertEqual(body["mode"], "deterministic")
        self.assertEqual(len(body["evidence"]), 6)

    def test_scenario_catalogue_contains_cases_without_file_paths(self):
        with urlopen(f"{self.base_url}/api/demo-scenarios") as response:
            body = json.loads(response.read())
        self.assertEqual(len(body["scenarios"]), 22)
        hansu = next(x for x in body["scenarios"] if x["id"] == "hansu-seasonal")
        self.assertEqual(hansu["manager"], "mummo.ankka")
        self.assertNotIn("snapshot", hansu)
        self.assertNotIn("expected", hansu)

    def test_scenario_selection_applies_to_review_briefing_and_draft(self):
        payload = {"scenario_id": "hannu-legacy-finance", "user_id": "hannu.hanhi",
                   "requester_id": "roope.ankka", "as_of": "2026-10-07"}
        status, report = self.post("/api/review", payload)
        self.assertEqual(status, 200)
        self.assertEqual(report["employee"]["display_name"], "Hannu Hanhi")
        status, brief = self.post("/api/summary", payload)
        self.assertEqual(status, 200)
        self.assertEqual(brief["metrics"]["evidence_count"], 2)
        status, draft = self.post("/api/service-desk-draft", dict(payload, additions=["Ankkalinna-Sales-CRM"], reason="Changed role"))
        self.assertEqual(status, 200)
        self.assertIn("Hannu Hanhi", draft["draft"])

    def test_scenario_cannot_bypass_authorization_or_name_arbitrary_files(self):
        payload = {"scenario_id": "hansu-wrong-manager", "user_id": "hansu.hanhi", "requester_id": "roope.ankka"}
        for endpoint in ("/api/review", "/api/summary", "/api/service-desk-draft"):
            status, body = self.post(endpoint, payload)
            self.assertEqual(status, 403)
            self.assertNotIn("employee", body)
        for scenario in ("../../etc/passwd", "missing-case", ["hansu-seasonal"]):
            status, body = self.post("/api/review", dict(payload, scenario_id=scenario))
            self.assertEqual(status, 400)
            self.assertNotIn("employee", body)

    def post(self, path: str, payload: dict) -> tuple[int, dict]:
        request = Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request) as response:
                return response.status, json.loads(response.read())
        except HTTPError as exc:
            return exc.code, json.loads(exc.read())


if __name__ == "__main__":
    unittest.main()

