import datetime as dt
import unittest

from bridge_pipeline.core import RawItem, SupabaseRest, attention_continuity_score, canonical_url, classify_headline, robust_rank, trust_grade, weighted_score
from bridge_pipeline.run import merge_official_and_flow
from bridge_pipeline.events import build_event_record, diagnosis_tags
from bridge_pipeline.targets import target_quota_report


CFG = {
    "minimum_publishable_axes": 3,
    "axis_weights": {"B": .15, "R": .25, "I": .15, "D": .10, "G": .20, "E": .15},
    "trust_thresholds": {"A": 85, "B": 70, "C": 55, "D": 0},
    "attention_continuity": {
        "no_mention_score": 45, "mention_base_score": 55,
        "volume_bonus_max": 20, "source_diversity_bonus_max": 5,
        "tone_adjustment_max": 20, "minimum_diverse_sources": 3,
        "half_life_days": {"STAR": 7, "CPR": 14}
    }
}


class PipelineTest(unittest.TestCase):
    def test_signal_ledger_separates_issue_from_final_e_score(self):
        item = RawItem("google_news_rss", "x", "가수A 음주운전 논란", "https://example.com/x", "언론사", "2026-10-11T00:00:00Z", {}, "hash")
        signals = classify_headline(item, "ENT-A", "가수A")
        event = build_event_record({"id": "entity", "domain": "STAR"}, item, "raw", signals)
        self.assertEqual(event["event_type"], "issue")
        self.assertEqual(event["review_status"], "pending")
        self.assertIn("E", event["axes"])

    def test_outcome_event_can_be_auto_recorded_for_g(self):
        item = RawItem("google_news_rss", "x", "가수A 월드투어 완판 신기록", "https://example.com/x", "언론사", "2026-10-11T00:00:00Z", {}, "hash2")
        signals = classify_headline(item, "ENT-A", "가수A")
        event = build_event_record({"id": "entity", "domain": "STAR"}, item, "raw", signals)
        self.assertEqual(event["event_type"], "outcome")
        self.assertEqual(event["review_status"], "auto")
        self.assertEqual(event["axes"], ["G"])

    def test_public_diagnosis_uses_metrics_not_internal_formula(self):
        tags = diagnosis_tags({"weekly_index": 74, "last_week_index": 70, "four_week_average": 68,
                               "activity_points": 12, "stability": 85})
        self.assertEqual(tags, ["상승 흐름", "중기 평균 상회", "활동 신호 활발"])

    def test_supabase_select_exhausts_default_row_cap(self):
        db = object.__new__(SupabaseRest)
        calls = []

        def fake_request(method, table, data=None, query="", prefer="return=representation"):
            calls.append(query)
            return [{"n": len(calls)}] * (1000 if len(calls) == 1 else 7)

        db.request = fake_request
        rows = db.select("x", "select=id")
        self.assertEqual(len(rows), 1007)
        self.assertIn("offset=1000", calls[1])

    def test_supabase_upsert_batches_historical_payloads(self):
        db = object.__new__(SupabaseRest)
        sizes = []

        def fake_request(method, table, data=None, query="", prefer="return=representation"):
            sizes.append(len(data))
            return data

        db.request = fake_request
        rows = [{"id": i} for i in range(1201)]
        result = db.upsert("x", rows, "id")
        self.assertEqual(sizes, [500, 500, 201])
        self.assertEqual(len(result), 1201)

    def test_tracking_params_are_removed(self):
        self.assertEqual(canonical_url("https://A.com/x/?utm_source=z&a=1#x"), "https://a.com/x?a=1")

    def test_adverse_signal_requires_review(self):
        item = RawItem("google_news_rss", "1", "삼성전자 과징금 논란", "https://x", "신문", None, {}, "h")
        signals = classify_headline(item, "CPR-001", "삼성전자")
        adverse = [s for s in signals if s.axis == "R"]
        self.assertEqual(adverse[0].review_status, "pending")

    def test_ent_commercial_and_response_signals_are_separate(self):
        item = RawItem("google_news_rss", "2", "아이유 브랜드 광고 캠페인 화제", "https://x", "신문", None, {}, "h2")
        signals = classify_headline(item, "STAR-001", "아이유")
        self.assertIn("I", {s.axis for s in signals})
        positive_r = [s for s in signals if s.axis == "R" and s.direction > 0]
        self.assertEqual(positive_r[0].signal_type, "positive_public_response")

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

    def test_no_mention_is_slightly_below_neutral(self):
        score, diag = attention_continuity_score([], 10, dt.date(2026, 10, 11), "STAR", CFG)
        self.assertEqual(score, 45)
        self.assertTrue(diag["no_mention_observed"])

    def test_mention_presence_and_tone_are_separate(self):
        base = {"id": "1", "raw_item_id": "a", "source_id": "news", "occurred_at": "2026-10-11T00:00:00Z"}
        neutral = [{**base, "axis": "B", "signal_type": "qualified_visibility", "direction": 1, "magnitude": 1, "confidence": .7}]
        negative = neutral + [{**base, "id": "2", "axis": "R", "signal_type": "adverse_mention", "direction": -1, "magnitude": 30, "confidence": 1}]
        neutral_score, neutral_diag = attention_continuity_score(neutral, 10, dt.date(2026, 10, 11), "STAR", CFG)
        negative_score, negative_diag = attention_continuity_score(negative, 10, dt.date(2026, 10, 11), "STAR", CFG)
        self.assertGreater(neutral_score, 45)
        self.assertEqual(neutral_diag["unique_mentions"], 1)
        self.assertLess(negative_score, neutral_score)
        self.assertEqual(negative_diag["unique_mentions"], 1)


if __name__ == "__main__":
    unittest.main()
