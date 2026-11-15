import contextlib
import datetime as dt
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bridge_pipeline.audit_v5 import audit


class AuditDB:
    def __init__(self, domain='CPR', status='shadow', score=60, published='2026-11-14T11:28:49Z'):
        self.rows = {
            'bridge_entities': [{'id': 'e', 'external_id': 'CPR-test', 'name': 'Test', 'domain': domain}],
            'bridge_scores': [{'entity_id': 'e', 'score': score, 'axes_used': ['B'], 'publish_status': status,
                               'confidence_score': 50, 'trust_grade': 'D', 'diagnostics': {}}],
            'bridge_axis_observations': [{'entity_id': 'e', 'axis': 'B', 'score': 60, 'status': 'measured', 'diagnostics': {}}],
            'bridge_rankings': [{'entity_id': 'e', 'domain': domain, 'score': 60,
                                'ranking_type': 'T100', 'published_at': published}],
        }

    def select(self, table, query):
        return self.rows.get(table, [])


class OperationalLineageTests(unittest.TestCase):
    def check(self, db):
        with tempfile.TemporaryDirectory() as tmp, patch('bridge_pipeline.audit_v5.ROOT', Path(tmp)), contextlib.redirect_stdout(io.StringIO()):
            return audit(db, dt.date(2026, 11, 14))

    def test_published_scored_cpr_shadow_uses_existing_panel_policy(self):
        self.assertTrue(self.check(AuditDB())['ok'])

    def test_unpublished_cpr_panel_candidate_is_validated(self):
        db = AuditDB(published=None)
        db.rows['bridge_rankings'][0]['score'] = 61
        with self.assertRaises(RuntimeError):
            self.check(db)

    def test_shadow_in_other_domain_still_blocks(self):
        with self.assertRaises(RuntimeError):
            self.check(AuditDB(domain='GOV'))

    def test_withheld_cpr_still_blocks(self):
        with self.assertRaises(RuntimeError):
            self.check(AuditDB(status='withheld'))

    def test_null_score_still_blocks(self):
        with self.assertRaises(RuntimeError):
            self.check(AuditDB(score=None))

    def test_wrong_domain_still_blocks(self):
        db = AuditDB()
        db.rows['bridge_rankings'][0]['domain'] = 'GOV'
        with self.assertRaises(RuntimeError):
            self.check(db)

    def test_missing_signal_still_blocks(self):
        db = AuditDB()
        db.rows['bridge_axis_observations'][0]['diagnostics'] = {'signal_ids': ['missing']}
        with self.assertRaises(RuntimeError):
            self.check(db)

    def test_missing_raw_still_blocks(self):
        db = AuditDB()
        db.rows['bridge_axis_observations'][0]['diagnostics'] = {'raw_item_id': 'missing'}
        with self.assertRaises(RuntimeError):
            self.check(db)


if __name__ == '__main__':
    unittest.main()
