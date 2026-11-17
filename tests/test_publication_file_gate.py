"""Ensure daily release validates the actual on-disk export before deployment."""
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.verify_export_file import verify_file
from tests.test_read_only_export_gate import SyntheticDB
from tools.dry_run_public_export import ReadOnlyDB

class PublicationFileGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = json.loads(Path("site/data/latest.json").read_text(encoding="utf-8"))
        cls.day = dt.date.fromisoformat(cls.p["asOfDate"])

    def check(self, payload, day=None):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"latest.json"
            path.write_text(json.dumps(payload,ensure_ascii=False),encoding="utf-8")
            return verify_file(path,day or self.day,ReadOnlyDB(SyntheticDB(self.p)))

    def test_exact_real_fixture_matches_400(self):
        self.assertEqual(self.check(self.p)["diff_count"],0)

    def test_old_date_cannot_be_relabelled(self):
        with self.assertRaisesRegex(RuntimeError,"date differs"):
            self.check(self.p,self.day+dt.timedelta(days=1))

    def test_partial_record_fails(self):
        data=json.loads(json.dumps(self.p))
        data["rankings"]=data["rankings"][:-1]
        data["recordCount"]=399
        with self.assertRaises(RuntimeError):
            self.check(data)

    def test_unpublished_file_fails(self):
        data=json.loads(json.dumps(self.p))
        data["dataStatus"]="no-published-snapshot"
        with self.assertRaisesRegex(RuntimeError,"not marked published"):
            self.check(data)

if __name__=="__main__":unittest.main()
