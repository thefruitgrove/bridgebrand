import json
import unittest

from reporting.interpretation import lint_public_text
from reporting.master_briefing import BridgeBriefingEngine


def entity(identifier="a", name="대상 A", domain="ENT", date="2026-10-24", grade="D", activity=0):
    return {
        "external_id": identifier,
        "name": name,
        "domain": domain,
        "as_of_date": date,
        "ranking_type": "T100",
        "methodology_version": "2026.10-v6.5",
        "trust_grade": grade,
        "daily_index": 73.25,
        "rank": 8,
        "activity_points": activity,
        "stability": "N/R",
        "axis_scores": {"B": 82.0, "R": 76.0, "I": 50.0, "D": 64.0, "G": 71.0, "E": 60.0},
        "axis_status": {"B": "observed", "R": "observed", "I": "reference", "D": "observed", "G": "maintained", "E": "observed"},
    }


class MasterBriefingTests(unittest.TestCase):
    def test_actual_trust_grade_is_preserved(self):
        report = BridgeBriefingEngine([entity(grade="D")]).build()
        self.assertEqual(report["metadata"]["trust_grades"]["대상 A"], "D")
        self.assertNotIn("표준 고정", json.dumps(report, ensure_ascii=False))

    def test_real_twenty_one_pages_and_dual_read(self):
        report = BridgeBriefingEngine([entity()]).build()
        self.assertEqual(len(report["pages"]), 21)
        self.assertTrue(all(page["easy_read"] for page in report["pages"]))
        self.assertTrue(all(len(page["professional_read"]) == 7 for page in report["pages"][10:]))
        self.assertTrue(report["publishable"], report["audit"])

    def test_reference_axis_is_not_selected_as_strength_or_weakness(self):
        report = BridgeBriefingEngine([entity()]).build()
        prose = json.dumps(report["pages"][12:17], ensure_ascii=False)
        self.assertNotIn("I·정체성은 상대적으로", prose)
        self.assertIn("참조축은 강약 판정과 종합 해석에서 제외", prose)

    def test_zero_activity_is_not_described_as_no_real_activity(self):
        report = BridgeBriefingEngine([entity(activity=0)]).build()
        prose = json.dumps(report, ensure_ascii=False)
        self.assertIn("실제 활동이 전혀 없었다는 뜻은 아닙니다", prose)
        self.assertNotIn("활동이 없었습니다", prose)

    def test_three_target_comparison_requires_same_scope(self):
        rows = [entity("a", "중심"), entity("b", "비교 A"), entity("c", "비교 B")]
        report = BridgeBriefingEngine(rows).build()
        self.assertEqual(report["metadata"]["mode"], "comparison")
        rows[2]["domain"] = "UNI"
        with self.assertRaisesRegex(ValueError, "MIXED_DOMAIN"):
            BridgeBriefingEngine(rows)

    def test_missing_real_trust_grade_is_rejected(self):
        row = entity(); row.pop("trust_grade")
        with self.assertRaisesRegex(ValueError, "실제 근거 신뢰등급"):
            BridgeBriefingEngine([row])

    def test_claim_certainty_and_no_overclaim(self):
        report = BridgeBriefingEngine([entity()]).build()
        certainties = {claim["certainty"] for page in report["pages"] for claim in page["claims"]}
        self.assertTrue({"confirmed", "bounded", "hypothesis", "recommendation"} <= certainties)
        prose = json.dumps(report, ensure_ascii=False)
        self.assertFalse(lint_public_text(prose))
        for banned in ("유일한 해답", "완벽한 증거", "철옹성", "반등할 것이다", "마음을 측정"):
            self.assertNotIn(banned, prose)


if __name__ == "__main__":
    unittest.main()
