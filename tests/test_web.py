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
