import datetime as dt
import unittest
from tools.verify_live import classify
class LiveSnapshotVersionTest(unittest.TestCase):
    def test_same_day_different_snapshot_fails(self):
        src=dict(asOfDate="2026-11-17",dataStatus="published",recordCount=400,rankings=[{}]*400,snapshotId="a"*20)
        deployed=dict(src,snapshotId="b"*20)
        result=classify(src,deployed,"2026-11-17 기준",dt.date(2026,11,17),max_age_days=0)
        self.assertIn("same_date_snapshot_id_mismatch",result["issues"])
        self.assertEqual(result["status"],"failure")
    def test_same_snapshot_passes(self):
        src=dict(asOfDate="2026-11-17",dataStatus="published",recordCount=400,rankings=[{}]*400,snapshotId="a"*20)
        self.assertEqual(classify(src,src,"2026-11-17 기준",dt.date(2026,11,17),max_age_days=0)["status"],"healthy")
