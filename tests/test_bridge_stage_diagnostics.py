"""BRIDGE step diagnostics must never infer success or expose secrets."""
import datetime as dt
import unittest
from tools.bridge_stage_diagnostics import summarize_runs, failed_stage
from tools.render_private_ops_dashboard import render_dashboard

DAY=dt.date(2026,11,28)

def run(name="BRIDGE Daily Pipeline", conclusion="failure", event="schedule", branch="main", ident=15):
    return {"name":name,"conclusion":conclusion,"event":event,
            "head_branch":branch,"id":ident,"status":"completed",
            "created_at":"2026-11-28T01:00:00Z"}

class StageDiagnosticsTests(unittest.TestCase):
    def test_latest_main_scheduled_failure_only(self):
        rows=[run(),run(conclusion="success",event="push",ident=88),
              run(conclusion="success",branch="stability/test",ident=89)]
        steps=summarize_runs(rows,DAY)
        self.assertEqual(steps[0]["label"],"정규 수집")
        self.assertEqual(steps[0]["status"],"failure")
        self.assertEqual(steps[0]["runId"],15)
        self.assertEqual(steps[0]["failureCount"],1)
        self.assertEqual(steps[1]["status"],"not_observed")

    def test_failed_stage_uses_only_allowlisted_labels(self):
        jobs=[{"steps":[{"name":"Unknown step SECRET_TOKEN=xxx","conclusion":"failure"},
                        {"name":"Compute shadow scores and rankings","conclusion":"failure"}]}]
        self.assertEqual(failed_stage(jobs),"점수·순위")
        self.assertIsNone(failed_stage([{"steps":[{"name":"SECRET=123","conclusion":"failure"}]}]))

    def test_no_success_from_no_runs(self):
        report=summarize_runs([],DAY)
        self.assertEqual(len(report),4)
        self.assertTrue(all(v["status"]=="not_observed" and v["runId"] is None for v in report))

    def test_dashboard_stage_info_is_sanitized(self):
        report={"scorecard":{"today":"2026-11-28","status":"failure","days":[]},
                "checks":{},"stages":[
                  {"label":"정규 수집","status":"failure","runId":44,"failureCount":1,
                   "failedStage":"점수·순위"},
                  {"label":"<script>bad</script>","status":"failure","runId":45,"failureCount":0,
                   "failedStage":"SUPABASE_SECRET=xxx"},
                  {"label":"근거 복구","status":"failure","runId":46,"failureCount":2,
                   "failedStage":"SUPABASE_SECRET=xxx"}]}
        rendered=render_dashboard(report)
        self.assertIn("작업별 진단·실패 단계",rendered)
        self.assertIn("실패 단계: 점수·순위",rendered)
        self.assertIn("단계 확인 불가",rendered)
        self.assertIn("/actions/runs/44",rendered)
        self.assertNotIn("SUPABASE_SECRET",rendered)
        self.assertNotIn("<script>bad</script>",rendered)

if __name__=="__main__":
    unittest.main()
