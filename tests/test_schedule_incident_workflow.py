"""Static regression for fail-safe GitHub schedule alert notification gates."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class ScheduleIncidentWorkflowTests(unittest.TestCase):
    def test_alert_creation_and_closure_are_independent_from_publication_status(self):
        text=(ROOT/'.github/workflows/bridge-7day-reliability.yml').read_text()
        self.assertIn("steps.verdict.outputs.schedule_risk == 'true'",text)
        self.assertIn("steps.verdict.outputs.schedule_risk == 'false'",text)
        self.assertIn("steps.verdict.outputs.schedule_covered == 'true'",text)
        self.assertIn('BRIDGE SCHEDULE: scheduled pipeline late or not started',text)
        self.assertIn("gh issue create",text)
        self.assertIn("gh issue close",text)
    def test_alert_does_not_touch_scores_or_invent_results(self):
        text=(ROOT/'.github/workflows/bridge-7day-reliability.yml').read_text()
        self.assertIn("Do not invent current-date records",text)
        self.assertIn("allowed={'정규 수집','근거 복구','재수집 판단','실서비스 검증'}",text)
if __name__=='__main__':unittest.main()
