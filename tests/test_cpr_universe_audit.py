import unittest

from bridge_pipeline.cpr_universe_audit import diagnose


CONFIG = {
    "version": "test-v1", "minimum_source_families": 2,
    "trust_thresholds": {"C": 55},
    "beta_eligibility": {
        "CPR": {"minimum_source_families": 2, "minimum_confidence_score": 55}
    },
}


class CPRUniverseAuditTest(unittest.TestCase):
    def test_finds_eligibility_bottleneck_without_reclassifying_rows(self):
        rows = {
            "as_of_date": "2026-10-25",
            "entities": [{"id": "a"}, {"id": "b"}, {"id": "c"}],
            "collection": [{"diagnostics": {"entity_results": {
                "a": {"status": "success"}, "b": {"status": "success"},
                "c": {"status": "success"},
            }}}],
            "observations": [
                {"entity_id": x, "axis": "B", "status": "measured"} for x in "abc"
            ],
            "scores": [
                {"entity_id": "a", "score": 70, "confidence_score": 60,
                 "publish_status": "published", "diagnostics": {"source_families": 2}},
                {"entity_id": "b", "score": 65, "confidence_score": 50,
                 "publish_status": "shadow", "diagnostics": {"source_families": 2}},
                {"entity_id": "c", "score": 64, "confidence_score": 60,
                 "publish_status": "shadow", "diagnostics": {"source_families": 1}},
            ],
            "rankings": [
                {"entity_id": "a", "published_at": "2026-10-25T00:00:00Z"}
            ],
        }
        report = diagnose(rows, CONFIG)
        self.assertEqual(report["stages"]["score_computed"], 3)
        self.assertEqual(report["stages"]["publication_eligible"], 1)
        self.assertEqual(report["largest_loss"]["to"], "publication_eligible")
        self.assertEqual(
            report["eligibility_exclusion_reasons"]["confidence_below_gate"], 1
        )
        self.assertEqual(
            report["eligibility_exclusion_reasons"]["insufficient_source_families"], 1
        )

    def test_flags_stale_generated_ranking(self):
        rows = {
            "as_of_date": "2026-10-25",
            "entities": [{"id": "a"}, {"id": "b"}],
            "collection": [],
            "observations": [{"entity_id": "a"}, {"entity_id": "b"}],
            "scores": [
                {"entity_id": "a", "score": 70, "confidence_score": 60,
                 "publish_status": "eligible", "diagnostics": {"source_families": 2}},
                {"entity_id": "b", "score": 60, "confidence_score": 40,
                 "publish_status": "shadow", "diagnostics": {"source_families": 2}},
            ],
            "rankings": [
                {"entity_id": "a", "published_at": None},
                {"entity_id": "b", "published_at": None},
            ],
        }
        self.assertEqual(diagnose(rows, CONFIG)["stale_generated_rows"], 1)


if __name__ == "__main__":
    unittest.main()
