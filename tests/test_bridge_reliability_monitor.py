"""Reliability-monitor evidence semantics; no fabricated seven-day success."""
import datetime as dt
import unittest

from tools.bridge_reliability_monitor import (
    DAILY_WORKFLOW, MONITOR_WORKFLOW, RECOVERY_WORKFLOW,
    day_status, run_day, scorecard, successful_run,
)

FIRST = dt.date(2026, 11, 28)


def workflow_run(name, day, conclusion="success", event="schedule",
                 branch="main", status="completed"):
    return {
        "name": name, "event": event, "head_branch": branch, "status": status,
        "conclusion": conclusion,
        "created_at": day.isoformat() + "T00:45:00Z",
    }


class ReliabilityMonitorTests(unittest.TestCase):
    def test_no_future_or_past_claims_before_start(self):
        out = scorecard(dt.date(2026, 11, 27), live_ok=True, db_ok=True,
                        repository_date="2026-11-27", runs=[])
        self.assertEqual(out["status"], "not_started")
        self.assertFalse(out["seven_day_clean"])

    def test_today_requires_current_cloudflare_and_db(self):
        runs = [workflow_run(DAILY_WORKFLOW, FIRST)]
        self.assertEqual(day_status(FIRST, FIRST, live_ok=True, db_ok=True,
                                    repository_date=FIRST.isoformat(),
                                    runs=runs)["status"], "healthy")
        for live_ok, db_ok, source_day in [
            (False, True, FIRST.isoformat()),
            (True, False, FIRST.isoformat()),
            (True, True, "2026-11-27"),
        ]:
            self.assertEqual(day_status(FIRST, FIRST, live_ok=live_ok, db_ok=db_ok,
                                        repository_date=source_day,
                                        runs=runs)["status"], "failure")

    def test_recovery_delivers_but_does_not_count_as_clean(self):
        runs = [workflow_run(DAILY_WORKFLOW, FIRST, "failure"),
                workflow_run(RECOVERY_WORKFLOW, FIRST, "success")]
        value = day_status(FIRST, FIRST, live_ok=True, db_ok=True,
                           repository_date=FIRST.isoformat(), runs=runs)
        self.assertEqual(value["status"], "degraded")
        self.assertTrue(value["recovery_success"])
        self.assertEqual(value["primary_failures"], 1)

    def test_qa_branch_and_push_cannot_prove_production(self):
        rows = [workflow_run(DAILY_WORKFLOW, FIRST, event="push"),
                workflow_run(DAILY_WORKFLOW, FIRST, branch="stability/test"),
                workflow_run(DAILY_WORKFLOW, FIRST, status="in_progress")]
        self.assertFalse(successful_run(rows, FIRST, DAILY_WORKFLOW))
        out = day_status(FIRST, FIRST, live_ok=True, db_ok=True,
                         repository_date=FIRST.isoformat(), runs=rows)
        self.assertEqual(out["status"], "degraded")

    def test_past_live_is_not_inferred_from_current_live(self):
        tomorrow = FIRST + dt.timedelta(days=1)
        runs = [workflow_run(DAILY_WORKFLOW, FIRST)]
        yesterday = day_status(FIRST, tomorrow, live_ok=True, db_ok=True,
                               repository_date=tomorrow.isoformat(), runs=runs)
        self.assertEqual(yesterday["status"], "not_observed")

    def test_seven_consecutive_evidenced_days(self):
        end = FIRST + dt.timedelta(days=6)
        runs = []
        for n in range(7):
            day = FIRST + dt.timedelta(days=n)
            runs.append(workflow_run(DAILY_WORKFLOW, day))
            if n < 6:
                runs.append(workflow_run(MONITOR_WORKFLOW, day))
        result = scorecard(end, live_ok=True, db_ok=True,
                           repository_date=end.isoformat(), runs=runs)
        self.assertTrue(result["seven_day_clean"])
        self.assertTrue(result["seven_day_delivery"])
        self.assertEqual(result["clean_days"], 7)
        self.assertEqual(result["observed_days"], 7)

    def test_missing_one_monitor_day_prevents_7_day_success(self):
        end = FIRST + dt.timedelta(days=6)
        runs = []
        for n in range(7):
            day = FIRST + dt.timedelta(days=n)
            runs.append(workflow_run(DAILY_WORKFLOW, day))
            if n < 6 and n != 2:
                runs.append(workflow_run(MONITOR_WORKFLOW, day))
        result = scorecard(end, live_ok=True, db_ok=True,
                           repository_date=end.isoformat(), runs=runs)
        self.assertFalse(result["seven_day_clean"])
        self.assertEqual(result["observed_days"], 6)
        self.assertEqual(result["days"][2]["status"], "not_observed")

    def test_prior_monitor_failure_not_rebranded_as_success(self):
        tomorrow = FIRST + dt.timedelta(days=1)
        runs = [workflow_run(DAILY_WORKFLOW, FIRST),
                workflow_run(MONITOR_WORKFLOW, FIRST, "failure")]
        prior = day_status(FIRST, tomorrow, live_ok=True, db_ok=True,
                           repository_date=tomorrow.isoformat(), runs=runs)
        self.assertEqual(prior["status"], "failure")

    def test_timestamp_is_asia_seoul(self):
        self.assertEqual(run_day(workflow_run(DAILY_WORKFLOW, FIRST)), FIRST)


if __name__ == "__main__":
    unittest.main()
