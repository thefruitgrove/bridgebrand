import datetime as dt
import unittest

from bridge_pipeline.core import RawItem, classify_headline
from bridge_pipeline.ent_reputation_v6 import classify_ent_evidence, diagnostics


class EntRelationshipEvidenceTests(unittest.TestCase):
    def test_relationship_identity_action_and_lifecycle(self):
        types = {r["type"] for r in classify_ent_evidence(
            "새 그룹 공식 콘셉트와 응원봉 공개, 팬미팅 직접 소통 뒤 앨범 구매·투표 확산"
        )}
        for value in {
            "ent_identity_official_concept", "ent_identity_fandom_symbol",
            "ent_relation_fan_contact", "ent_relation_direct_communication",
            "ent_action_purchase", "ent_action_voting",
        }:
            self.assertIn(value, types)

    def test_job_contexts_are_separate(self):
        types = {r["type"] for r in classify_ent_evidence(
            "배우 연기 호평, 가수 라이브 호평, 선수 경기력 호평, 크리에이터 콘텐츠 전문성"
        )}
        self.assertIn("ent_craft_actor_performance", types)
        self.assertIn("ent_craft_music_performance", types)
        self.assertIn("ent_craft_sports_performance", types)
        self.assertIn("ent_craft_creator_expertise", types)

    def test_recurrence_requires_review(self):
        row = next(r for r in classify_ent_evidence("사과 뒤 동일 논란 재발") if r["type"] == "ent_lifecycle_recurred")
        self.assertEqual(row["review_status"], "pending")
        self.assertLess(row["direction"], 0)

    def test_ent_only(self):
        item = RawItem("google_news_rss", "1", "A2O 팬미팅 직접 소통",
                       "https://example.test/1", "매체",
                       dt.datetime.now(dt.timezone.utc).isoformat(), {}, "hash")
        ent_types = {s.signal_type for s in classify_headline(item, "STAR-X", "A2O", domain="STAR")}
        gov_types = {s.signal_type for s in classify_headline(item, "GOV-X", "A2O", domain="GOV")}
        self.assertIn("ent_relation_fan_contact", ent_types)
        self.assertNotIn("ent_relation_fan_contact", gov_types)

    def test_public_safe_diagnostics(self):
        result = diagnostics([
            {"signal_type": "ent_action_ticketing"},
            {"signal_type": "ent_discovery_organic_discovery"},
            {"signal_type": "qualified_visibility"},
        ])
        self.assertEqual(result["action_paths"], ["ticketing"])
        self.assertEqual(result["discovery_contexts"], ["organic_discovery"])
        self.assertEqual(result["enriched_evidence_count"], 2)
        self.assertNotIn("threshold", result)
