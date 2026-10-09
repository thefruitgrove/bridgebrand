import unittest

from bridge_pipeline.baseline import grade, normalize_gov, normalize_uni, percentile


class OfficialBaselineTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
