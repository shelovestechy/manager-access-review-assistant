from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
DEMO = ROOT / "demo" / "index.html"


class StaticPresentationDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = DEMO.read_text(encoding="utf-8")

    def test_demo_explains_fixed_synthetic_data(self) -> None:
        self.assertIn("fixed, self-made Ankkalinna dataset", self.html)
        self.assertIn("No live or personal data is retrieved", self.html)
        self.assertIn("no backend or API is called", self.html)

    def test_demo_states_future_read_only_boundary(self) -> None:
        self.assertIn("only explicitly allowed data retrieval paths", self.html)
        self.assertIn("would not submit requests or perform unrestricted searches", self.html)

    def test_pages_only_badge_is_removed(self) -> None:
        self.assertNotIn('<span class="source-badge">AD + Entra ID</span>', self.html)
        self.assertIn("Static presentation demo", self.html)

    def test_pages_demo_uses_muted_palette(self) -> None:
        self.assertIn("--brand: #0F6CBD", self.html)
        self.assertIn("--canvas: #F5F5F5", self.html)

    def test_pages_demo_uses_native_fluent_typography(self) -> None:
        self.assertIn('"Segoe UI Variable", "Segoe UI"', self.html)
        self.assertNotIn("@font-face", self.html)
        self.assertNotIn("font-family: Inter", self.html)

    def test_pages_demo_reads_like_an_application(self) -> None:
        self.assertIn("Review employee access", self.html)
        self.assertIn("Access Review Assistant</span>", self.html)
        self.assertNotIn("Access reviews that explain themselves.", self.html)

    def test_finnish_scenario_text_is_utf8(self) -> None:
        self.assertIn("käsin syötettävät tunnukset", self.html)
        self.assertIn("ylläpito-oikeus", self.html)
        self.assertNotIn("Ã¤", self.html)


if __name__ == "__main__":
    unittest.main()
