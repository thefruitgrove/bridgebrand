"""Guardrail: production freshness must not pass with a two-day grace window.

Read-only offline classifier tests; no live credentials or network.
"""
import datetime as dt
import unittest

from tools.verify_live import classify


class LiveFreshnessGateTests(unittest.TestCase):
    def setUp(self):
        self.today = dt.date(2026, 11, 15)
        self.current = {
            "asOfDate": "2026-11-15",
            "dataStatus": "published",
            "recordCount": 400,
            "rankings": [{}] * 400,
        }

    def test_current_date_is_healthy(self):
        result = classify(self.current, self.current, "2026-11-15 기준", self.today, max_age_days=0)
        self.assertEqual(result["status"], "healthy")

    def test_prior_day_live_snapshot_is_failure(self):
        old = dict(self.current, asOfDate="2026-11-14")
        result = classify(self.current, old, "2026-11-14 기준", self.today, max_age_days=0)
        self.assertEqual(result["status"], "failure")
        self.assertIn("stale_live_snapshot", result["issues"])

    def test_missing_or_inconsistent_today_snapshot_is_failure(self):
        empty = dict(self.current, recordCount=0, rankings=[])
        result = classify(self.current, empty, "2026-11-15 기준", self.today, max_age_days=0)
        self.assertEqual(result["status"], "failure")
        self.assertIn("invalid_live_record_count", result["issues"])
        wrong_page = classify(self.current, self.current, "2026-11-14 기준", self.today, max_age_days=0)
        self.assertIn("this_week_date_mismatch", wrong_page["issues"])


if __name__ == "__main__":
    unittest.main()
