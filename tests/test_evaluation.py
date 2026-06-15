from __future__ import annotations

import unittest

from courtroom import CourtroomEngine
from tools.evaluate_cases import DEFAULT_CASES_PATH, evaluate_cases, load_cases


class EvaluationSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = load_cases(DEFAULT_CASES_PATH)
        cls.evaluation = evaluate_cases(cls.cases, CourtroomEngine().analyze)

    def test_dataset_has_required_size_and_categories(self):
        categories = {case["category"] for case in self.cases}
        self.assertGreaterEqual(len(self.cases), 50)
        self.assertEqual(
            categories,
            {
                "family_impersonation",
                "otp_code_theft",
                "fake_bank_alert",
                "package_delivery_scam",
                "marketplace_deposit_scam",
                "fake_invoice",
                "government_refund_stimulus_scam",
                "romance_emergency_money_scam",
                "safe_benign",
                "ambiguous_action_required",
            },
        )

    def test_no_false_low_risk_on_protected_cases(self):
        self.assertEqual(self.evaluation["summary"]["false_low_risk_count"], 0)

    def test_required_guardrail_cases_pass(self):
        required_ids = {
            "package-001",
            "otp-001",
            "family-001",
            "bank-001",
            "safe-001",
        }
        results = {
            result["id"]: result
            for result in self.evaluation["results"]
            if result["id"] in required_ids
        }
        self.assertEqual(set(results), required_ids)
        self.assertTrue(all(result["passed"] for result in results.values()))

    def test_full_baseline_has_no_safety_failures(self):
        self.assertEqual(self.evaluation["summary"]["safety_failure_count"], 0)

    def test_category_metrics_include_average_risk_score(self):
        for stats in self.evaluation["categories"].values():
            self.assertIn("average_risk_score", stats)
            self.assertGreaterEqual(stats["average_risk_score"], 0)
            self.assertLessEqual(stats["average_risk_score"], 100)

if __name__ == "__main__":
    unittest.main()
