import datetime as dt
import unittest
from bridge_pipeline.core import RawItem, classify_headline
from bridge_pipeline.uni_reputation_v6 import classify_uni_evidence, diagnostics

class UniRelationshipEvidenceTests(unittest.TestCase):
    def test_relationship_identity_and_lifecycle_are_separate(self):
        types={r["type"] for r in classify_uni_evidence("한빛대학교 만족도 상승, 대학 비전 이행과 신뢰 회복")}
        for value in {"uni_relation_satisfaction","uni_relation_trust","uni_identity_institutional_identity","uni_lifecycle_implemented","uni_lifecycle_recovered"}:
            self.assertIn(value,types)
    def test_negative_relationship_and_recurrence_require_review(self):
        rows=classify_uni_evidence("한빛대학교 불만 사태 재발")
        self.assertTrue(all(r["review_status"]=="pending" and r["direction"]<0 for r in rows))
    def test_uni_only_integration_preserves_qualified_visibility(self):
        item=RawItem("google_news_rss","1","한빛대학교 학생 만족도 상승","https://example.test/1","매체",dt.datetime.now(dt.timezone.utc).isoformat(),{},"hash")
        uni=classify_headline(item,"UNI-X","한빛대학교",domain="UNI")
        other=classify_headline(item,"CPR-X","한빛대학교",domain="CPR")
        self.assertIn("uni_relation_satisfaction",{s.signal_type for s in uni})
        self.assertNotIn("uni_relation_satisfaction",{s.signal_type for s in other})
        self.assertIn("qualified_visibility",{s.signal_type for s in uni})
    def test_diagnostics_do_not_expose_terms_or_thresholds(self):
        result=diagnostics([{"signal_type":"uni_relation_trust"},{"signal_type":"qualified_visibility"}])
        self.assertEqual(result["relationship_concepts"],["trust"])
        self.assertEqual(result["enriched_evidence_count"],1)
