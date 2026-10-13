import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from bridge_pipeline.run import export_latest

class PublicExportTest(unittest.TestCase):
    def run_export(self, rows):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'site/data').mkdir(parents=True)
            def history(db, day):
                (root/'site/data/history.json').write_text(json.dumps({'rankings':rows}))
            with patch('bridge_pipeline.run.ROOT', root), patch('bridge_pipeline.run.export_history', history):
                export_latest(None, dt.date(2026,10,14))
            return json.loads((root/'site/data/latest.json').read_text())
    def test_current_date_only_and_contiguous_ranks(self):
        rows=[{'domain':'CPR','ranking_type':'T100','external_id':'A','as_of_date':'2026-10-14','score':70,'rank':9,'previous_rank':3},
              {'domain':'CPR','ranking_type':'T100','external_id':'B','as_of_date':'2026-10-14','score':80,'rank':6,'previous_rank':1},
              {'domain':'CPR','ranking_type':'T100','external_id':'A','as_of_date':'2026-10-13','score':99,'rank':1}]
        out=self.run_export(rows)
        self.assertEqual([(r['external_id'],r['rank'],r['rank_change']) for r in out['rankings']], [('B',1,0),('A',2,1)])
    def test_duplicate_aborts_publication(self):
        row={'domain':'CPR','ranking_type':'T100','external_id':'A','as_of_date':'2026-10-14','score':70,'rank':1}
        with self.assertRaisesRegex(RuntimeError,'duplicate public ranking blocked'):
            self.run_export([row,dict(row,score=80)])
