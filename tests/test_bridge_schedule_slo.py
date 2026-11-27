"""GitHub Actions scheduled-run punctuality regression contracts."""
import datetime as dt
import unittest

from tools.bridge_schedule_slo import punctuality
from tools.render_private_ops_dashboard import render_dashboard
KST=dt.timezone(dt.timedelta(hours=9))

def run(day,hour,minute,name="BRIDGE Daily Pipeline",event="schedule",branch="main"):
    t=dt.datetime.combine(day,dt.time(hour,minute),tzinfo=KST)
    return {"name":name,"created_at":t.astimezone(dt.timezone.utc).isoformat(),
            "event":event,"head_branch":branch,
            "status":"completed","conclusion":"success"}

class ScheduleSLOTest(unittest.TestCase):
    def test_missing_0515_is_overdue_at_0620(self):
        now=dt.datetime(2026,11,28,6,20,tzinfo=KST)
        result=punctuality([],now)
        self.assertEqual(result["jobs"][0]["status"],"overdue")
        self.assertEqual(result["jobs"][1]["status"],"pending")
        self.assertEqual(result["overdueCount"],1)
        self.assertTrue(result["scheduleRisk"])

    def test_real_delayed_schedule_is_recorded_not_repaired(self):
        day=dt.date(2026,11,27)
        result=punctuality([run(day,11,51)],dt.datetime(2026,11,27,13,0,tzinfo=KST))
        self.assertEqual(result["jobs"][0]["delayMinutes"],396)
        self.assertEqual(result["jobs"][0]["status"],"late")
        self.assertEqual(result["jobs"][0]["historicalMaxDelayMinutes"],396)

    def test_manual_and_qa_runs_do_not_prove_schedule_punctuality(self):
        day=dt.date(2026,11,28)
        runs=[run(day,5,15,event="workflow_dispatch"),
              run(day,5,15,branch="stability/test")]
        result=punctuality(runs,dt.datetime(2026,11,28,6,20,tzinfo=KST))
        self.assertEqual(result["jobs"][0]["status"],"overdue")

    def test_before_0515_no_failure(self):
        result=punctuality([],dt.datetime(2026,11,28,5,0,tzinfo=KST))
        self.assertEqual(result["jobs"][0]["status"],"pending")
        self.assertFalse(result["scheduleRisk"])

    def test_observed_early_is_ok_and_lateness_does_not_change_publication(self):
        day=dt.date(2026,11,28)
        result=punctuality([run(day,5,22)],dt.datetime(2026,11,28,9,30,tzinfo=KST))
        self.assertEqual(result["jobs"][0]["status"],"observed")
        self.assertEqual(result["jobs"][0]["delayMinutes"],7)

    def test_dashboard_renders_no_raw_run_metadata(self):
        report={"scorecard":{"today":"2026-11-28","status":"failure","days":[]},
                "scheduleAudit":{"scheduleRisk":True,"jobs":[
                    {"label":"정규 수집","status":"late","expectedKst":"05:15",
                     "delayMinutes":396,"secrets":"PRIVATE_TOKEN"},
                    {"label":"<script>exfil</script>","status":"overdue",
                     "expectedKst":"06:45"}]}}
        rendered=render_dashboard(report)
        self.assertIn("예약 실행 준수 현황",rendered)
        self.assertIn("396분 지연",rendered)
        self.assertNotIn("PRIVATE_TOKEN",rendered)
        self.assertNotIn("<script>exfil</script>",rendered)

if __name__=="__main__":unittest.main()
