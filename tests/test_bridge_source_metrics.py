"""Source metrics test: actual attempt counts, date windows and missing data."""
import datetime as dt
import unittest
from tools.bridge_source_metrics import summarize_sources,collect_source_summary
from tools.render_private_ops_dashboard import render_dashboard

TODAY=dt.date(2026,11,28)

def sample(source,status,start="2026-11-27T09:00:00+09:00",end="2026-11-27T09:04:00+09:00"):
    return {"source_id":source,"status":status,"started_at":start,"finished_at":end}

class SourceMetricsTests(unittest.TestCase):
    def test_successful_retry_does_not_hide_initial_failure(self):
        rows=[sample("google_news_rss","failed",end="2026-11-27T09:01:00+09:00"),
              sample("google_news_rss","success",start="2026-11-27T10:00:00+09:00",end="2026-11-27T10:06:00+09:00")]
        m=summarize_sources(rows,TODAY)
        item=next(r for r in m["sources"] if r["sourceId"]=="google_news_rss")
        self.assertEqual(item["runs"],2)
        self.assertEqual(item["successfulRuns"],1)
        self.assertEqual(item["failedRuns"],1)
        self.assertEqual(item["observedDays"],1)
        self.assertEqual(item["successfulDays"],1)
        self.assertEqual(item["successRatePct"],50.0)
        self.assertEqual(item["averageDurationMinutes"],3.5)
        self.assertEqual(item["lastRunStatus"],"success")

    def test_missing_record_cannot_be_success(self):
        data=summarize_sources([],TODAY)
        item=next(r for r in data["sources"] if r["sourceId"]=="opendart")
        self.assertEqual(item["runs"],0)
        self.assertIsNone(item["successRatePct"])
        self.assertIsNone(item["averageDurationMinutes"])
        self.assertEqual(item["lastRunStatus"],"not_observed")
        self.assertFalse(data["metricsAvailable"])

    def test_incomplete_success_not_counted(self):
        row=sample("opendart","success",end=None)
        item=next(r for r in summarize_sources([row],TODAY)["sources"] if r["sourceId"]=="opendart")
        self.assertEqual(item["successfulRuns"],0)
        self.assertEqual(item["incompleteRuns"],1)
        self.assertEqual(item["lastRunStatus"],"unknown")

    def test_outside_window_future_and_unlisted_sources_are_ignored(self):
        rows=[sample("google_news_rss","failed","2026-10-01T00:00:00+09:00","2026-10-01T00:01:00+09:00"),
              sample("google_news_rss","success","2026-11-29T00:00:00+09:00","2026-11-29T00:01:00+09:00"),
              sample("secret-internal-db","failed")]
        self.assertEqual(summarize_sources(rows,TODAY)["totalRuns"],0)

    def test_readonly_query_has_strict_kst_date_limits_and_projection(self):
        class Stub:
            def select(self,table,query):
                self.table,self.query=table,query
                return []
        db=Stub()
        result=collect_source_summary(db,TODAY)
        self.assertEqual(db.table,"bridge_collection_runs")
        self.assertIn("select=source_id,status,started_at,finished_at",db.query)
        self.assertNotIn("error_detail",db.query)
        self.assertIn("started_at=gte.2026-10-30T00:00:00+09:00",db.query)
        self.assertIn("started_at=lt.2026-11-29T00:00:00+09:00",db.query)
        self.assertEqual(result["windowDays"],30)

    def test_dashboard_source_table_no_secrets(self):
        report={
            "scorecard":{"today":"2026-11-28","status":"not_observed","days":[]},
            "sourceMetrics":{
                "windowStart":"2026-10-30","windowEnd":"2026-11-28",
                "sources":[{
                    "sourceId":"google_news_rss","runs":2,
                    "observedDays":1,"successfulDays":1,"failedRuns":1,
                    "successRatePct":50.0,"averageDurationMinutes":3.5,
                    "lastRunStatus":"success",
                    "error_detail":"SOME_KEY_SHOULD_NEVER_APPEAR"
                }]}
        }
        rendered=render_dashboard(report)
        self.assertIn("자료원별 수집 안정성",rendered)
        self.assertIn("뉴스 RSS",rendered)
        self.assertIn("50.0%",rendered)
        self.assertNotIn("SOME_KEY_SHOULD_NEVER_APPEAR",rendered)

if __name__=="__main__":
    unittest.main()
