import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class DailyWorkflowIntegrity(unittest.TestCase):
    def test_critical_collection_before_optional_candidate_discovery(self):
        s=(ROOT/'.github/workflows/bridge-daily.yml').read_text()
        self.assertLess(s.index("Collect registered targets' verified daily evidence (required)"),s.index("Discover unregistered challenger candidates (advisory only)"))
        self.assertIn('continue-on-error: true',s)
        self.assertIn('test_google_rate_limit.py',s)
        self.assertIn('Hard gate — verify today\'s mandatory collectors before scoring',s)
        self.assertIn('Stale export blocked:',s)
        self.assertIn('exit 1',s)
        self.assertIn('python -m unittest discover -s tests -p "$spec" -v',s)
    def test_fallback_dispatches_only_if_stale_and_inactive(self):
        s=(ROOT/'.github/workflows/bridge-daily-fallback.yml').read_text()
        for k in ('15 22 * * *','"Today\'s verified publication is already in GitHub; no duplicate collection."','Official collector or recovery is active','inputs[as_of_date]','$TODAY'):
            self.assertIn(k,s)

if __name__=='__main__':unittest.main()
