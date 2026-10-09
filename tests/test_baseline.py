import unittest

from bridge_pipeline.baseline import grade, normalize_gov, normalize_uni, percentile
from bridge_pipeline.cpr_financials import extract_metrics, normalize as normalize_cpr
from bridge_pipeline.gov_source import convert
from bridge_pipeline.targets import load_targets, target_quota_report


class OfficialBaselineTest(unittest.TestCase):
    def test_cpr_financial_metrics_and_cohort_percentiles(self):
        rows = [
            {"fs_div": "CFS", "account_nm": "매출액", "thstrm_amount": "1200", "frmtrm_amount": "1000"},
            {"fs_div": "CFS", "account_nm": "영업이익", "thstrm_amount": "120", "frmtrm_amount": "80"},
            {"fs_div": "CFS", "account_nm": "당기순이익", "thstrm_amount": "90", "frmtrm_amount": "70"},
            {"fs_div": "CFS", "account_nm": "자산총계", "thstrm_amount": "2000", "frmtrm_amount": "1800"},
            {"fs_div": "CFS", "account_nm": "부채총계", "thstrm_amount": "800", "frmtrm_amount": "750"},
            {"fs_div": "CFS", "account_nm": "자본총계", "thstrm_amount": "1200", "frmtrm_amount": "1050"},
        ]
        metrics = extract_metrics(rows)
        self.assertEqual(metrics["revenue_growth"], 20.0)
        self.assertEqual(metrics["operating_margin"], 10.0)
        records = [
            {"external_id": "CPR-001", "cohort": "BC70", **metrics},
            {"external_id": "CPR-002", "cohort": "BC70", **{**metrics, "revenue_growth": 0, "operating_margin": 1}},
        ]
        normalized = normalize_cpr(records, 2025)
        by_id = {(row["external_id"], row["axis"]): float(row["score"]) for row in normalized}
        self.assertGreater(by_id[("CPR-001", "G")], by_id[("CPR-002", "G")])
    def test_percentile_direction(self):
        self.assertGreater(percentile([1, 2, 3], 3), percentile([1, 2, 3], 1))
        self.assertLess(percentile([1, 2, 3], 3, False), percentile([1, 2, 3], 1, False))

    def test_gov_grade_mapping(self):
        self.assertEqual(grade("가"), 100.0)
        rows = normalize_gov([{
            "external_id": "GOV-M01", "overall_grade": "가", "strategy_grade": "나",
            "system_grade": "다", "epeople_grade": "가", "satisfaction_grade": "나",
            "performance_grade": "가", "communication_grade": "나", "integrity_grade": "다"
        }])
        self.assertTrue({"B", "I", "D", "G", "E"}.issuperset({r["axis"] for r in rows}))
        self.assertTrue(all(0 <= float(r["score"]) <= 100 for r in rows))

    def test_uni_missing_values_are_not_zero(self):
        rows = normalize_uni([
            {"external_id": "UNI-001", "school_type": "대학교", "region_group": "수도권", "competition_rate": "10", "dropout_rate": "2", "employment_rate": "70"},
            {"external_id": "UNI-002", "school_type": "대학교", "region_group": "수도권", "competition_rate": "5", "dropout_rate": "5", "employment_rate": "60"},
        ])
        by_entity = {}
        for row in rows:
            by_entity.setdefault(row["external_id"], {})[row["axis"]] = float(row["score"])
        self.assertGreater(by_entity["UNI-001"]["B"], by_entity["UNI-002"]["B"])
        self.assertGreater(by_entity["UNI-001"]["D"], by_entity["UNI-002"]["D"])
        self.assertNotIn("I", by_entity["UNI-001"])

    def test_gov_frame_has_no_public_corporations(self):
        targets = [row for row in load_targets() if row["domain"] == "GOV"]
        self.assertEqual(len(targets), 100)
        self.assertFalse(any(row["name"] == "한국전력공사" for row in targets))
        gov_quota = [row for row in target_quota_report() if row["domain"] == "GOV"]
        self.assertTrue(all(row["exact_match"] for row in gov_quota))

    def test_gov_source_accepts_historical_and_prefixed_names(self):
        source = [
            {
                "평가연도": "2025년", "기관유형": "중앙행정기관", "기관명": "기획재정부",
                "종합등급": "가", "민원행정 전략 및 체계": "나", "민원제도운영": "다",
                "국민신문고민원 처리": "가", "고충민원 처리": "", "민원만족도": "나",
            },
            {
                "평가연도": "2025년", "기관유형": "기초자치단체", "기관명": "경기도 수원시",
                "종합등급": "가", "민원행정 전략 및 체계": "가", "민원제도운영": "가",
                "국민신문고민원 처리": "가", "고충민원 처리": "가", "민원만족도": "가",
            },
        ]
        converted, _missing = convert(source)
        ids = {row["external_id"] for row in converted}
        self.assertIn("GOV-M01", ids)
        self.assertIn("GOV-C18", ids)

    def test_uni_aliases_cover_renamed_schools(self):
        targets = [row for row in load_targets() if row["domain"] == "UNI"]
        aliases = {row["name"]: row["aliases"] for row in targets}
        self.assertIn("한국과학기술원", aliases["한국과학기술원(KAIST)"])
        self.assertIn("부산보건대학교", aliases["동주대학교"])

    def test_uni_axis_coverage_reflects_missing_variables(self):
        rows = normalize_uni([{
            "external_id": "UNI-U01", "school_type": "4년제", "region_group": "수도권",
            "competition_rate": "10", "freshman_fill_rate": "100", "international_student_rate": "5",
            "scholarship_per_student": "300", "education_spend_per_student": "1000",
            "dorm_capacity_rate": "20", "faculty_capacity_rate": "90",
            "library_resources_per_student": "50", "employment_rate": "70",
            "disclosure_completeness": "100", "financial_stability": "150",
        }])
        by_axis = {row["axis"]: row for row in rows}
        self.assertEqual(by_axis["B"]["coverage"], "1.00")
        self.assertEqual(by_axis["D"]["coverage"], "0.71")
        self.assertEqual(by_axis["G"]["coverage"], "0.25")
        self.assertEqual(by_axis["E"]["coverage"], "0.67")
        self.assertNotIn("I", by_axis)


if __name__ == "__main__":
    unittest.main()
