from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
CONFIG = ROOT / "config"


class UiStaticTests(unittest.TestCase):
    def test_login_gate_uses_hermes_slicer_branding(self) -> None:
        html = (WEB / "index.html").read_text(encoding="utf-8")
        self.assertIn('aria-label="Hermes Slicer login"', html)
        self.assertIn('<h1 class="sr-only">Hermes Slicer</h1>', html)
        self.assertIn("/assets/hermes-slicer-login.png", html)
        self.assertTrue((WEB / "assets" / "hermes-slicer-login.png").exists())
        self.assertIn("/assets/hermes-orca-minimal.svg", html)
        self.assertIn("/assets/hermes-slicer-icon-32.png", html)
        self.assertIn("/assets/hermes-slicer-icon-256.png", html)
        self.assertIn('id="authForm"', html)
        self.assertIn("Email or Username", html)
        self.assertIn("Password", html)
        self.assertIn("Sign In", html)
        self.assertIn("Sign Up / Create Account", html)
        self.assertNotIn("Continue to Hermes Tools", html)
        self.assertIn("Tool ID or request", html)

    def test_login_form_is_real_local_session_ui(self) -> None:
        html = (WEB / "index.html").read_text(encoding="utf-8")
        script = (WEB / "app.js").read_text(encoding="utf-8")
        self.assertIn('autocomplete="username"', html)
        self.assertIn('autocomplete="current-password"', html)
        self.assertIn('aria-label="Show password"', html)
        self.assertIn("submitAuth", script)
        self.assertIn("Email or username and password are required", script)
        self.assertIn("sessionStorage.setItem(\"hermesLocalSession\", \"connected\")", script)

    def test_brand_assets_are_present(self) -> None:
        for asset in (
            "hermes-slicer-login.png",
            "readme-hero.png",
            "hermes-orca-primary.svg",
            "hermes-orca-minimal.svg",
            "hermes-slicer-icon-32.png",
            "hermes-slicer-icon-256.png",
        ):
            path = WEB / "assets" / asset
            self.assertTrue(path.exists(), asset)
            self.assertGreater(path.stat().st_size, 0, asset)

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("web/assets/readme-hero.png", readme)

    def test_css_uses_brand_tokens(self) -> None:
        tokens = json.loads((CONFIG / "brand_tokens.json").read_text(encoding="utf-8"))
        css = (WEB / "styles.css").read_text(encoding="utf-8")
        self.assertIn(f"--bg: {tokens['background_primary']};", css)
        self.assertIn(f"--accent: {tokens['accent_cyan']};", css)
        self.assertIn(f"--warning: {tokens['accent_gold']};", css)

    def test_web_surface_does_not_ship_jusprin_branding(self) -> None:
        for path in [*WEB.glob("*"), *WEB.glob("assets/*.svg")]:
            if path.suffix not in {".html", ".js", ".css", ".svg"}:
                continue
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("JusPrin", content)
            self.assertNotIn("JusBot", content)
            self.assertNotIn("Obico", content)


if __name__ == "__main__":
    unittest.main()
