from __future__ import annotations

import unittest
from unittest.mock import patch

import app
from courtroom.ui.i18n import TRANSLATIONS


class FakeVisionBackend:
    backend_name = "none"

    def analyze_image(self, image_path: str, context_text: str | None = None):
        return {
            "vision_status": "inactive",
            "vision_model": None,
            "vision_summary": None,
            "extracted_text": None,
            "screenshot_type": None,
            "screenshot_risk_clues": [],
            "recommended_text_for_analysis": None,
            "vision_confidence": 0.0,
            "vision_error": None,
        }


class FakeSuccessfulVisionBackend:
    backend_name = "minicpm_v"

    def analyze_image(self, image_path: str, context_text: str | None = None):
        return {
            "vision_status": "analyzed",
            "vision_model": "openbmb/MiniCPM-V-4",
            "vision_summary": "Screenshot analyzed.",
            "extracted_text": "FedEx delivery failed. Update at https://fedex-track.xyz/update",
            "screenshot_type": "sms",
            "screenshot_risk_clues": ["delivery action link"],
            "recommended_text_for_analysis": "FedEx delivery failed. Update at https://fedex-track.xyz/update",
            "vision_confidence": 0.92,
            "vision_error": None,
        }


class ScamCourtUiTests(unittest.TestCase):
    def test_package_link_requires_verification(self):
        report = app.analyze_message(
            "FedEx delivery failed. Update your preferences at https://fedex-track.xyz/update",
            None,
            "en",
        )[1]
        self.assertEqual(report["shield_verdict"], "VERIFY FIRST")
        self.assertGreaterEqual(report["risk_score"], 35)

    def test_otp_request_stops_user(self):
        report = app.analyze_message(
            "Send me the verification code now so I can secure your bank account.",
            None,
            "en",
        )[1]
        self.assertEqual(report["shield_verdict"], "STOP")
        self.assertGreaterEqual(report["risk_score"], 70)

    def test_family_new_number_money_request_stops_user(self):
        report = app.analyze_message(
            "Hi Mom, this is my new number. Please Zelle me $450 right now.",
            None,
            "en",
        )[1]
        self.assertEqual(report["shield_verdict"], "STOP")
        self.assertGreaterEqual(report["risk_score"], 70)

    def test_safe_casual_message_is_low_visible_risk(self):
        report = app.analyze_message(
            "Are we still meeting for coffee at 3?",
            None,
            "en",
        )[1]
        self.assertEqual(report["shield_verdict"], "LOW VISIBLE RISK")
        self.assertLess(report["risk_score"], 35)

    def test_screenshot_failure_never_returns_low_risk(self):
        with patch("app.get_vision_backend", return_value=FakeVisionBackend()):
            report = app.analyze_message("", "unreadable.png", "en")[1]
        self.assertEqual(report["shield_verdict"], "VERIFY FIRST")
        self.assertGreaterEqual(report["risk_score"], 35)
        self.assertFalse(report["analysis_used_vision_text"])

    def test_successful_vision_text_feeds_risk_pipeline(self):
        with patch("app.get_vision_backend", return_value=FakeSuccessfulVisionBackend()):
            report = app.analyze_message("", "fedex.png", "en")[1]
        self.assertEqual(report["vision_status"], "analyzed")
        self.assertTrue(report["analysis_used_vision_text"])
        self.assertIn("vision_extracted_text", report["input_sources"])
        self.assertEqual(report["shield_verdict"], "VERIFY FIRST")

    def test_spanish_dynamic_result_is_localized(self):
        report = app.analyze_message(
            "FedEx delivery failed. Update at https://fedex-track.xyz/update",
            None,
            "es",
        )[1]
        rendered = app.render_shield(report, "es")
        self.assertIn("VERIFICA PRIMERO", rendered)
        self.assertIn("Acción más segura ahora", rendered)

    def test_translation_catalogs_have_matching_keys(self):
        self.assertEqual(set(TRANSLATIONS["en"]), set(TRANSLATIONS["es"]))


if __name__ == "__main__":
    unittest.main()
