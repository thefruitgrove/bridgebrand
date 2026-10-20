import datetime as dt
import unittest

from bridge_pipeline.core import RawItem, classify_headline
from bridge_pipeline.cpr_reputation_v6 import classify_cpr_evidence, diagnostics


class CprRelationshipEvidenceTests(unittest.TestCase):
    def test_relationship_identity_action_and_capability(self):
        types = {r["type"] for r in classify_cpr_evidence(
            "고객 중심 핵심가치, 고객 의견 반영해 서비스 개선…재구매와 추천 확산"
        )}
        for value in {
            "cpr_identity_customer_orientation", "cpr_identity_official_promise",
            "cpr_relation_responsiveness", "cpr_capability_service_delivery",
            "cpr_action_repurchase", "cpr_action_recommendation",
        }:
            self.assertIn(value, types)

    def test_esg_claim_is_not_automatic_positive_reputation(self):
        rows = classify_cpr_evidence("기업 ESG 선언과 윤리경영 계획 발표")
        ethics = next(r for r in rows if r["type"] == "cpr_responsibility_ethics")
        self.assertEqual(ethics["direction"], 0)

    def test_recurrence_and_exit_require_review(self):
        rows = classify_cpr_evidence("보상안 발표 뒤 같은 결함 재발, 고객 불매")
        recurrence = next(r for r in rows if r["type"] == "cpr_lifecycle_recurred")
        boycott = next(r for r in rows if r["type"] == "cpr_action_boycott")
        self.assertEqual(recurrence["review_status"], "pending")
        self.assertEqual(boycott["review_status"], "pending")
        self.assertLess(recurrence["direction"], 0)

    def test_cpr_only(self):
        item = RawItem("google_news_rss", "1", "예시기업 고객 의견 반영해 품질 개선",
                       "https://example.test/1", "매체",
                       dt.datetime.now(dt.timezone.utc).isoformat(), {}, "hash")
        cpr_types = {s.signal_type for s in classify_headline(item, "CPR-X", "예시기업", domain="CPR")}
        ent_types = {s.signal_type for s in classify_headline(item, "STAR-X", "예시기업", domain="STAR")}
        self.assertIn("cpr_relation_responsiveness", cpr_types)
        self.assertIn("cpr_capability_quality_delivery", cpr_types)
        self.assertNotIn("cpr_relation_responsiveness", ent_types)

    def test_public_safe_diagnostics(self):
        result = diagnostics([
            {"signal_type": "cpr_action_repurchase"},
            {"signal_type": "cpr_lifecycle_implemented"},
            {"signal_type": "qualified_visibility"},
        ])
        self.assertEqual(result["action_paths"], ["repurchase"])
        self.assertEqual(result["lifecycle_stages"], ["implemented"])
        self.assertEqual(result["enriched_evidence_count"], 2)
        self.assertNotIn("threshold", result)


if __name__ == "__main__":
    unittest.main()
