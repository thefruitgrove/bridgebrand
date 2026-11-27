"""Safe, portable BRIDGE operations dashboard rendering."""
import html
import unittest

from tools.render_private_ops_dashboard import render_dashboard


def fixture():
    return {
        "checkedAt": "2026-11-28T09:30:05+09:00",
        "observationDate": "2026-11-28",
        "errors": [],
        "checks": {
            "repositoryDate": "2026-11-28",
            "live_ok": True,
            "db_ok": True,
            "live": {"live_date": "2026-11-28", "record_count": 400},
            "errors": [],
        },
        "scorecard": {
            "today": "2026-11-28", "status": "healthy",
            "observed_days": 1, "delivered_days": 1, "clean_days": 1,
            "seven_day_clean": False, "seven_day_delivery": False,
            "days": [{"date": "2026-11-28", "status": "healthy"}],
        },
    }


class OperationsDashboardTests(unittest.TestCase):
    def test_aggregate_status_and_daily_schedule(self):
        doc = render_dashboard(fixture())
        self.assertIn("운영 관리 콘솔", doc)
        self.assertIn("2026-11-28", doc)
        self.assertIn("05:15 KST", doc)
        self.assertIn("09:30 KST", doc)
        self.assertIn("7일 연속 무장애", doc)
        self.assertIn("미충족", doc)
        self.assertIn("기대값 100건", doc)
        self.assertIn("실측 건수가 아닙니다", doc)

    def test_untrusted_values_are_html_escaped(self):
        data = fixture()
        data["checks"]["repositoryDate"] = '<script>alert("XSS")</script>'
        data["scorecard"]["days"][0]["date"] = "<img src=x onerror=alert(1)>"
        doc = render_dashboard(data)
        self.assertNotIn('<script>alert("XSS")</script>', doc)
        self.assertNotIn("<img src=x onerror=alert(1)>", doc)
        self.assertIn("&lt;script&gt;", doc)
        self.assertIn("&lt;img", doc)

    def test_no_internal_errors_or_tokens_are_rendered(self):
        data = fixture()
        data["errors"] = ["API_KEY=do-not-include"]
        data["checks"]["errors"] = ["SUPABASE_SECRET_KEY=also-do-not-include"]
        data["checks"]["database"] = {"private_sql": "sensitive"}
        doc = render_dashboard(data)
        self.assertNotIn("do-not-include", doc)
        self.assertNotIn("also-do-not-include", doc)
        self.assertNotIn("sensitive", doc)
        self.assertIn("2개", doc)

    def test_fail_closed_on_missing_report_fields(self):
        doc = render_dashboard({})
        self.assertIn("기록 없음", doc)
        self.assertIn("미확인 / 실패", doc)

    def test_degraded_is_not_misreported_as_healthy(self):
        data = fixture()
        data["scorecard"]["status"] = "degraded"
        data["scorecard"]["clean_days"] = 0
        data["scorecard"]["days"][0]["status"] = "degraded"
        doc = render_dashboard(data)
        self.assertIn("복구·주의", doc)
        self.assertIn("무장애 정규 운영", doc)
        self.assertIn(">0일</strong>", doc)

    def test_report_does_not_claim_private_auth(self):
        doc = render_dashboard(fixture())
        self.assertNotIn("비공개 인증", doc)
        self.assertNotIn("외부 공개 금지", doc)


if __name__ == "__main__":
    unittest.main()
