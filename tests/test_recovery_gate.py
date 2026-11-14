"""Pure, offline tests for cost-safe BRIDGE recovery classification."""
import unittest

from tools.recovery_gate import choose


def metrics(n=400):
    return [{"entity_id": str(i)} for i in range(n)]


def observations(n=1900):
    return [{"entity_id": str(i), "axis": "BRIDGE"[i % 6]} for i in range(n)]


COLLECTIONS = [
    {"source_id": "google_news_rss", "status": "success"},
    {"source_id": "opendart", "status": "success"},
]


class RecoveryGateTests(unittest.TestCase):
    def test_complete_day_does_no_work(self):
        result = choose("2026-11-14", source_date="2026-11-14",
                        source_published=True, metric_rows=metrics(),
                        observation_rows=observations(), collection_rows=COLLECTIONS)
        self.assertEqual(result["mode"], "skip")

    def test_publish_only_after_completed_metrics(self):
        result = choose("2026-11-14", source_date="2026-11-13",
                        source_published=True, metric_rows=metrics(),
                        observation_rows=[], collection_rows=[])
        self.assertEqual(result["mode"], "export")

    def test_only_score_from_complete_evidence(self):
        result = choose("2026-11-14", source_date="2026-11-13",
                        source_published=True, metric_rows=metrics(100),
                        observation_rows=observations(), collection_rows=COLLECTIONS)
        self.assertEqual(result["mode"], "score")

    def test_block_partial_collection(self):
        result = choose("2026-11-14", source_date="2026-11-13",
                        source_published=True, metric_rows=metrics(100),
                        observation_rows=observations(1104), collection_rows=COLLECTIONS)
        self.assertEqual(result["mode"], "blocked")

    def test_block_missing_core_source(self):
        result = choose("2026-11-14", source_date="2026-11-13",
                        source_published=True, metric_rows=[], observation_rows=observations(),
                        collection_rows=COLLECTIONS[:1])
        self.assertEqual(result["mode"], "blocked")

    def test_never_roll_back_a_newer_publication(self):
        result = choose("2026-11-13", source_date="2026-11-14",
                        source_published=True, metric_rows=[], observation_rows=[],
                        collection_rows=[])
        self.assertEqual(result["mode"], "skip")


if __name__ == "__main__":
    unittest.main()
