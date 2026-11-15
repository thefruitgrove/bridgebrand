import copy
import datetime as dt
import json
import unittest
from pathlib import Path

from tools.dry_run_public_export import ReadOnlyDB, validate

ROOT=Path(__file__).resolve().parents[1]


class SyntheticDB:
    def __init__(self, payload):
        self.entities=[]
        self.ranks=[]
        for i,r in enumerate(payload['rankings']):
            uid=f'fake-entity-{i:03d}'
            self.entities.append({'id':uid,'external_id':r['external_id']})
            self.ranks.append({
                'entity_id':uid,'domain':'STAR' if r['domain']=='ENT' else r['domain'],
                'ranking_type':r['ranking_type'],'rank':r['rank'],'score':r['score'],
                'trust_grade':r['trust_grade'],'methodology_version':payload['methodologyVersion']
            })
    def select(self, table, query):
        if table=='bridge_entities':
            return self.entities
        if table=='bridge_rankings':
            return self.ranks
        raise AssertionError('unexpected table '+table)


class ReadOnlyExportGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=json.loads((ROOT/'site/data/latest.json').read_text(encoding='utf-8'))
        cls.day=dt.date.fromisoformat(cls.fixture['asOfDate'])

    def test_actual_400_row_snapshot_passes_fixed_input_contract(self):
        result=validate(self.fixture, ReadOnlyDB(SyntheticDB(self.fixture)),self.day)
        self.assertEqual(result['row_count'],400)
        self.assertEqual(result['diff_count'],0)
        self.assertEqual(result['snapshot_id'],self.fixture['snapshotId'])

    def test_different_trust_grade_is_blocked(self):
        altered=copy.deepcopy(self.fixture)
        altered['rankings'][0]['trust_grade']='NOT_A_GRADE'
        with self.assertRaises(RuntimeError):
            validate(altered,ReadOnlyDB(SyntheticDB(self.fixture)),self.day)

    def test_wrong_target_set_is_blocked(self):
        altered=copy.deepcopy(self.fixture)
        altered['rankings'].pop()
        altered['recordCount']-=1
        with self.assertRaises(RuntimeError):
            validate(altered,ReadOnlyDB(SyntheticDB(self.fixture)),self.day)

    def test_read_only_wrapper_cannot_write(self):
        db=ReadOnlyDB(SyntheticDB(self.fixture))
        with self.assertRaisesRegex(RuntimeError,'forbidden'):
            db.patch('bridge_rankings',{},'id=eq.fake')
        with self.assertRaisesRegex(RuntimeError,'forbidden'):
            db.upsert('bridge_scores',[], 'id')


if __name__=='__main__':
    unittest.main()
