import unittest

from reporting.interpretation import (
    Claim, PUBLICITY_BLOCKS, assert_publishable, audit_page_contract,
    axis_coverage, coverage_change, four_week_label, rank_movement,
    set_change, trust_coverage_review, validate_observation, validate_same_scope,
)


def row(identifier="a", rank=1, score=70, date="2026-10-21", domain="ENT", grade="B"):
    return {
        "external_id": identifier, "rank": rank, "score": score,
        "as_of_date": date, "domain": domain, "ranking_type": "T100",
        "methodology_version": "2026.10-v5-beta1", "trust_grade": grade,
        "axis_scores": {axis: 50 for axis in "BRIDGE"},
        "axis_status": {axis: "observed" for axis in "BRIDGE"},
    }


class InterpretationTests(unittest.TestCase):
    def test_rank_movement_does_not_confuse_rank_and_score(self):
        result = rank_movement(row(rank=3, score=69), row(rank=5, score=70))
        self.assertEqual(result["type"], "rank_rise_despite_score_fall")

    def test_same_scope_blocks_cross_field_and_duplicate(self):
        findings = validate_same_scope([row("a"), row("b", domain="UNI")])
        self.assertTrue(any(f.code == "MIXED_DOMAIN" and f.blocks_publication for f in findings))
        self.assertTrue(any(f.code == "DUPLICATE_TARGET" for f in validate_same_scope([row("a"), row("a")])))

    def test_reference_is_explicit_and_excluded(self):
        value = row()
        value["axis_status"]["R"] = "reference"
        self.assertEqual(axis_coverage([value])["R"], 0)
        self.assertFalse(validate_observation(value))

    def test_missing_state_never_inferred_from_50(self):
        value = row(); value.pop("axis_status")
        findings = validate_observation(value)
        self.assertTrue(any(f.code == "AXIS_STATE_MISSING" and f.blocks_publication for f in findings))

    def test_set_and_coverage_change(self):
        old = [row("a"), row("b")]
        new = [row("b"), row("c")]; new[0]["axis_status"]["E"] = "reference"
        self.assertEqual(set_change(new, old)["entered"], ["c"])
        self.assertEqual(coverage_change(new, old)["E"]["delta"], -1)

    def test_four_week_label_is_honest(self):
        self.assertEqual(four_week_label(2), "AVAILABLE-WEEK AVERAGE · 관측 2주")
        self.assertEqual(four_week_label(4), "4-WEEK AVERAGE")

    def test_trust_coverage_is_review_not_automatic_error(self):
        value = row(grade="A")
        value["axis_status"].update({"D": "reference", "G": "reference", "E": "reference"})
        finding = trust_coverage_review(value)
        self.assertEqual(finding.severity, "review")
        self.assertFalse(finding.blocks_publication)

    def test_general_briefing_minimum_and_density(self):
        claims = [Claim(f"검증된 분석문장 {i}", "fact", ("score",)) for i in range(7)]
        pages = [{"number": n, "claims": claims if n >= 11 else []} for n in range(1, 22)]
        self.assertFalse(audit_page_contract(pages))
        pages[10]["claims"] = claims[:6]
        self.assertTrue(any(f.code == "ANALYSIS_DENSITY" for f in audit_page_contract(pages)))

    def test_publicity_eight_blocks_and_overclaim_lint(self):
        payload = {"title": "검증 제목", "standfirst": "관계 구조", "editorial_blocks": list(PUBLICITY_BLOCKS),
                   "sections": [{"paragraphs": ["활동량은 긍정 방향과 같은 뜻이 아니다."]}]}
        assert_publishable(payload)
        payload["title"] = "압도적 우위"
        with self.assertRaisesRegex(ValueError, "PUBLIC_OVERCLAIM"):
            assert_publishable(payload)


if __name__ == "__main__":
    unittest.main()
