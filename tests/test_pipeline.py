import unittest

from bridge_pipeline.core import RawItem, canonical_url, classify_headline, robust_rank, trust_grade, weighted_score
from bridge_pipeline.run import merge_official_and_flow
from bridge_pipeline.targets import target_quota_report


CFG = {
    "minimum_publishable_axes": 3,
    "axis_weights": {"B": .15, "R": .25, "I": .15, "D": .10, "G": .20, "E": .15},
    "trust_thresholds": {"A": 85, "B": 70, "C": 55, "D": 0}
}


class PipelineTest(unittest.TestCase):
    def test_tracking_params_are_removed(self):
        self.assertEqual(canonical_url("https://A.com/x/?utm_source=z&a=1#x"), "https://a.com/x?a=1")

    def test_adverse_signal_requires_review(self):
        item = RawItem("google_news_rss", "1", "삼성전자 과징금 논란", "https://x", "신문", None, {}, "h")
        signals = classify_headline(item, "CPR-001", "삼성전자")
        adverse = [s for s in signals if s.axis == "R"]
        self.assertEqual(adverse[0].review_status, "pending")

    def test_missing_axes_are_not_zero(self):
        score, confidence, axes = weighted_score({"B": 80, "R": 70, "I": None, "D": None, "G": None, "E": None}, {"B": .8, "R": .8}, CFG)
        self.assertIsNone(score)
        self.assertEqual(confidence, 0)
        self.assertEqual(axes, ["B", "R"])

    def test_rank_is_deterministic(self):
        rows = [{"external_id": "B", "score": 80, "confidence_score": 90}, {"external_id": "A", "score": 80, "confidence_score": 90}]
        ranked = robust_rank(rows)
        self.assertEqual([r["external_id"] for r in ranked], ["A", "B"])
        self.assertEqual([r["rank"] for r in ranked], [1, 1])

    def test_trust_grade(self):
        self.assertEqual(trust_grade(72, CFG), "B")

    def test_target_quota_mismatch_is_visible(self):
        rows = [
            {"domain": "CPR", "subcategory": "BC70", "active": True},
            {"domain": "CPR", "subcategory": "BB30", "active": True},
        ]
        report = target_quota_report(rows)
        cpr = {row["cohort_code"]: row for row in report if row["domain"] == "CPR"}
        self.assertEqual(cpr["BC70"]["actual_count"], 1)
        self.assertFalse(cpr["BC70"]["exact_match"])

    def test_official_baseline_is_not_overwritten_by_news_flow(self):
        official = {"score": 80, "confidence": .95, "coverage": 1, "evidence_count": 2,
                    "freshness_days": 1, "diagnostics": {"source_id": "opendart_financials"}}
        flow = {"score": 20, "confidence": .4, "coverage": .2, "evidence_count": 3,
                "freshness_days": 0, "diagnostics": {"source_ids": ["google_news_rss"]}}
        merged = merge_official_and_flow(official, flow, "CPR")
        self.assertEqual(merged["score"], 53.0)
        self.assertEqual(merged["source_families"], 2)
        self.assertEqual(merged["evidence_count"], 5)


if __name__ == "__main__":
    unittest.main()
