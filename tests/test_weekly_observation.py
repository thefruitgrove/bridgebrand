import unittest

from bridge_pipeline.weekly_observation import axis_week_state, remediation_stage, weekly_entity_summary


class WeeklyObservationTest(unittest.TestCase):
    def test_state_priority_is_observed_then_maintained(self):
        rows = [
            {"as_of_date": "2026-10-19", "status": "carried", "score": 60},
            {"as_of_date": "2026-10-20", "status": "measured", "score": 61},
        ]
        self.assertEqual(axis_week_state(rows, "success")["state"], "O")
        self.assertEqual(axis_week_state(rows[:1], "success")["state"], "M")

    def test_reference_requires_successful_check(self):
        self.assertEqual(axis_week_state([], "success")["state"], "R")
        self.assertEqual(axis_week_state([], "failed")["state"], "F")
        self.assertEqual(axis_week_state([], "not_observed")["state"], "F")

    def test_summary_never_manufactures_missing_axis(self):
        summary = weekly_entity_summary({"B": [{"as_of_date": "2026-10-20", "status": "measured", "score": 70}]}, "success")
        self.assertEqual(summary["available_axes"], 1)
        self.assertEqual(summary["state_codes"]["B"], "O")
        self.assertEqual(summary["state_codes"]["R"], "R")
        self.assertTrue(summary["collection_complete"])

    def test_failure_and_reference_remediation(self):
        summary = weekly_entity_summary({}, "failed")
        self.assertFalse(summary["collection_complete"])
        self.assertEqual(summary["failed_axes"], list("BRIDGE"))
        self.assertEqual(remediation_stage(1), "normal_reference")
        self.assertEqual(remediation_stage(2), "supplementary_source_search")
        self.assertEqual(remediation_stage(4), "operational_definition_review")
        self.assertEqual(remediation_stage(6), "measurement_design_review")


if __name__ == "__main__":
    unittest.main()
