import datetime as dt
import unittest
from bridge_pipeline.core import RawItem,classify_headline
from bridge_pipeline.gov_reputation_v6 import classify_gov_evidence,diagnostics

class GovRelationshipEvidenceTests(unittest.TestCase):
 def test_concepts(self):
  types={r["type"] for r in classify_gov_evidence("한빛시 공청회 의견 반영 후 개선 조치, 민관협력 민원 처리")}
  for value in {"gov_procedure_consultation","gov_participation_input_reflected","gov_lifecycle_implemented","gov_collaboration_joint_governance","gov_experience_complaint_service"}: self.assertIn(value,types)
 def test_agreement_is_weaker(self):
  rows={r["type"]:r for r in classify_gov_evidence("한빛시 업무협약 뒤 공동사업")}
  self.assertLess(rows["gov_collaboration_agreement_only"]["magnitude"],rows["gov_collaboration_joint_delivery"]["magnitude"])
 def test_recurrence_requires_review(self):
  row=next(r for r in classify_gov_evidence("한빛시 감사 지적 재발") if r["type"]=="gov_lifecycle_recurred")
  self.assertEqual(row["review_status"],"pending"); self.assertLess(row["direction"],0)
 def test_gov_only(self):
  item=RawItem("google_news_rss","1","한빛시 공청회 의견수렴","https://example.test/1","매체",dt.datetime.now(dt.timezone.utc).isoformat(),{},"hash")
  self.assertIn("gov_procedure_consultation",{s.signal_type for s in classify_headline(item,"GOV-X","한빛시",domain="GOV")})
  self.assertNotIn("gov_procedure_consultation",{s.signal_type for s in classify_headline(item,"UNI-X","한빛시",domain="UNI")})
 def test_public_safe_diagnostics(self):
  result=diagnostics([{"signal_type":"gov_procedure_transparency"},{"signal_type":"qualified_visibility"}])
  self.assertEqual(result["procedure_concepts"],["transparency"]); self.assertEqual(result["enriched_evidence_count"],1)
