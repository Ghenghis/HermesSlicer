from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


class UiStaticTests(unittest.TestCase):
    def test_login_gate_uses_hermes_slicer_branding(self) -> None:
        html = (WEB / "index.html").read_text(encoding="utf-8")
        self.assertIn('aria-label="Hermes Slicer login"', html)
        self.assertIn('<h1 class="sr-only">Hermes Slicer</h1>', html)
        self.assertIn("/assets/hermes-slicer-login.png", html)
        self.assertTrue((WEB / "assets" / "hermes-slicer-login.png").exists())
        self.assertIn("Continue to Hermes Tools", html)
        self.assertIn("Tool ID or request", html)

    def test_web_surface_does_not_ship_jusprin_branding(self) -> None:
        for path in WEB.glob("*"):
            if path.suffix not in {".html", ".js", ".css"}:
                continue
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("JusPrin", content)
            self.assertNotIn("JusBot", content)
            self.assertNotIn("Obico", content)


if __name__ == "__main__":
    unittest.main()
