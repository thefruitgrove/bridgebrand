"""RSS resilience: no false success, preserve partial evidence, fail closed."""
import datetime as dt
import urllib.error
import unittest
from unittest.mock import patch

from bridge_pipeline.news_resilience import collect_targets, NewsCollectionIncomplete, resumable_successes, search_names
from bridge_pipeline.run import collect_news


def entities(n=4):
    return [
        {"id": f"id-{i}", "external_id": f"ENT-{i:03}", "domain": "STAR",
         "name": f"대상{i}", "aliases": []}
        for i in range(n)
    ]


def http_error(code):
    return urllib.error.HTTPError("https://news.google.com/rss", code,
                                  "provider unavailable", {}, None)


class NewsResilienceTests(unittest.TestCase):
    def test_transient_errors_isolated_and_circuit_opens(self):
        calls = []
        def fetch(entity, query):
            calls.append(entity["id"])
            if entity["id"] in {"id-1", "id-2"}:
                raise http_error(503)
            return []
        successes, status, failures = collect_targets(entities(), fetch)
        self.assertEqual(calls, ["id-0", "id-1", "id-2"])
        self.assertEqual([e["id"] for e, _ in successes], ["id-0"])
        self.assertEqual(status["id-0"]["status"], "success")
        self.assertEqual(status["id-0"]["fetched_count"], 0)
        self.assertEqual(status["id-1"]["status"], "failed")
        self.assertIsNone(status["id-1"]["fetched_count"])
        self.assertEqual(status["id-3"]["status"], "not_attempted")
        self.assertEqual(status["id-3"]["error_code"], "PROVIDER_CIRCUIT_OPEN")
        self.assertEqual(failures, ["id-1", "id-2", "id-3"])

    def test_single_transient_failure_does_not_abort_remaining_targets(self):
        def fetch(entity, query):
            if entity["id"] == "id-1":
                raise http_error(429)
            return []
        successes, status, failures = collect_targets(entities(), fetch)
        self.assertEqual(len(successes), 3)
        self.assertEqual(failures, ["id-1"])
        self.assertEqual(status["id-3"]["status"], "success")

    def test_nontransient_http_error_is_not_swallowed(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            collect_targets(entities(1), lambda entity, query: (_ for _ in ()).throw(http_error(403)))
        self.assertEqual(caught.exception.code, 403)

    def test_invalid_circuit_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            collect_targets(entities(1), lambda entity, query: [], max_consecutive_failures=0)

    def test_complete_success_still_includes_empty_observations(self):
        successes, statuses, failures = collect_targets(entities(), lambda entity, query: [])
        self.assertEqual(len(successes), 4)
        self.assertEqual(failures, [])
        self.assertTrue(all(result["status"] == "success" for result in statuses.values()))

    def test_partial_collection_keeps_saved_records_but_marks_required_run_failed(self):
        class FakeDB:
            def __init__(self):
                self.patches = []
                self.inserts = []
                self.upserts = []
            def select(self, table, query):
                return entities()
            def insert(self, table, rows):
                self.inserts.append((table, rows))
                return [{"id": "run-001"}] if table == "bridge_collection_runs" else []
            def upsert(self, table, rows, conflict):
                self.upserts.append((table, rows))
                return []
            def patch(self, table, values, query):
                self.patches.append((table, values))
        db = FakeDB()
        def fetch(query, *args):
            if '"대상1"' in query or '"대상2"' in query:
                raise http_error(503)
            return []
        with patch("bridge_pipeline.run.fetch_google_news", side_effect=fetch):
            with self.assertRaises(NewsCollectionIncomplete):
                collect_news(db, dt.date(2026, 11, 27))
        self.assertIn("bridge_raw_items", [t for t, _ in db.upserts])
        self.assertIn("bridge_signals", [t for t, _ in db.upserts])
        self.assertIn("bridge_event_ledger", [t for t, _ in db.upserts])
        self.assertFalse(any(v["status"] == "success" for t, v in db.patches))
        failures = [v for t, v in db.patches if v.get("status") == "failed"]
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["diagnostics"]["entity_results"]["id-0"]["status"], "success")
        self.assertEqual(failures[0]["diagnostics"]["entity_results"]["id-3"]["status"], "not_attempted")
        self.assertEqual(len(failures[0]["diagnostics"]["failed_entity_ids"]), 3)
        self.assertTrue(any(table == "bridge_pipeline_alerts" for table, _ in db.inserts))

    def test_resume_only_matching_persisted_partial_run(self):
        from zoneinfo import ZoneInfo
        as_of = dt.date(2026, 11, 27)
        end = dt.datetime(2026, 11, 27, 5, 15, tzinfo=ZoneInfo("Asia/Seoul"))
        start = end - dt.timedelta(days=1)
        statuses = {
            e["id"]: {
                "status": "success" if e["id"] == "id-0" else "failed",
                "query_names": search_names(e),
                "fetched_count": 0 if e["id"] == "id-0" else None,
                "matched_count": 0,
            }
            for e in entities()
        }
        past = {
            "status": "failed", "window_start": start.astimezone(dt.timezone.utc).isoformat(),
            "window_end": end.astimezone(dt.timezone.utc).isoformat(),
            "diagnostics": {
                "partial_evidence_saved": True,
                "observation_as_of": as_of.isoformat(),
                "methodology_version": "test-v1",
                "entity_results": statuses,
            },
        }
        reusable = resumable_successes([past], entities(), as_of, start, end, "test-v1")
        self.assertEqual(set(reusable), {"id-0"})
        calls = []
        def fetch(entity, query):
            calls.append(entity["id"])
            return []
        success, result, failed = collect_targets(entities(), fetch, prior_results=reusable)
        self.assertEqual(calls, ["id-1", "id-2", "id-3"])
        self.assertEqual(failed, [])
        self.assertTrue(result["id-0"]["reused_from_prior_run"])
        self.assertEqual(len(success), 3)
        self.assertEqual(set(result), {e["id"] for e in entities()})
        self.assertTrue(all(v["status"] == "success" for v in result.values()))

        changed = [{**e, "aliases": ["추가 명칭"]} if e["id"] == "id-0" else e for e in entities()]
        self.assertEqual(resumable_successes([past], changed, as_of, start, end, "test-v1"), {})
        self.assertEqual(resumable_successes([past], entities(), as_of, start, end, "test-v2"), {})
        self.assertEqual(resumable_successes([past], entities(), as_of + dt.timedelta(days=1), start, end, "test-v1"), {})
        later = end + dt.timedelta(hours=1)
        self.assertEqual(resumable_successes([past], entities(), as_of, start, later, "test-v1"), {})
        unpersisted = {**past, "diagnostics": {**past["diagnostics"], "partial_evidence_saved": False}}
        self.assertEqual(resumable_successes([unpersisted], entities(), as_of, start, end, "test-v1"), {})
        incorrect_roster = {**past, "diagnostics": {**past["diagnostics"], "entity_results": {"id-0": statuses["id-0"]}}}
        self.assertEqual(resumable_successes([incorrect_roster], entities(), as_of, start, end, "test-v1"), {})


if __name__ == "__main__":
    unittest.main()
