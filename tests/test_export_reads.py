import datetime as dt
import unittest
from bridge_pipeline.export_reads import public_observations
from bridge_pipeline.evidence_v5 import profile


D = dt.date(2026, 11, 14)


def row(i, **kw):
    return dict(id=f'{i:08d}', entity_id='e', as_of_date=str(D), axis='B', score=0,
                status='measured', methodology_version='v', **kw)


class ExportReadsTests(unittest.TestCase):
    def test_projection_preserves_profile_and_zero(self):
        class DB:
            def select(self, table, query):
                self.query = query
                return [row(1, evidence_date=None, flow_evidence_date='2026-11-13')]
        db = DB()
        rows = list(public_observations(db, D, D, ['v']))
        expected = dict(rows[0], diagnostics={'flow': {'evidence_date': '2026-11-13'}, 'large_private_payload': ['unused']})
        self.assertEqual(profile(rows, D), profile([expected], D))
        self.assertEqual(rows[0]['score'], 0)
        self.assertIn('evidence_date:diagnostics->>evidence_date', db.query)
        self.assertNotIn(',diagnostics,', db.query)
        self.assertNotIn('id', rows[0])

    def test_keyset_has_no_offset_and_keeps_every_page(self):
        class DB:
            def __init__(self): self.calls = []
            def select(self, table, query):
                self.calls.append(query)
                return [row(i) for i in range(1, 501)] if len(self.calls) == 1 else [row(501)]
        db = DB()
        self.assertEqual(len(list(public_observations(db, D, D, ['v']))), 501)
        self.assertIn('id=gt.00000500', db.calls[1])
        self.assertTrue(all('offset=' not in q for q in db.calls))

    def test_timeout_retries_same_cursor_with_smaller_read(self):
        class DB:
            def __init__(self): self.calls = []
            def select(self, table, query):
                self.calls.append(query)
                if len(self.calls) == 1: raise RuntimeError('{"code": "57014"}')
                return [row(1)]
        db = DB()
        self.assertEqual(len(list(public_observations(db, D, D, ['v']))), 1)
        self.assertIn('limit=500', db.calls[0]); self.assertIn('limit=250', db.calls[1])
        self.assertTrue(all('id=gt.' not in q for q in db.calls))

    def test_permanent_timeout_is_bounded(self):
        class DB:
            def __init__(self): self.calls = 0
            def select(self, *args):
                self.calls += 1
                raise RuntimeError('{"code":"57014"}')
        db = DB()
        with self.assertRaises(RuntimeError): list(public_observations(db, D, D, ['v']))
        self.assertEqual(db.calls, 10)  # 5 global attempts and 5 date-scoped attempts


    def test_persistent_broad_timeout_falls_back_to_indexed_dates(self):
        class DB:
            def __init__(self):
                self.calls = []
            def select(self, table, query):
                self.calls.append(query)
                if '&as_of_date=gte.' in query:
                    raise RuntimeError('{"code":"57014"}')
                if '&as_of_date=eq.2026-11-13' in query:
                    return [dict(row(1),as_of_date='2026-11-13')]
                if '&as_of_date=eq.2026-11-14' in query:
                    return [row(2)]
                return []
        # row() defaults to November 14, so build a compatible special row.
        # Do not rely on client-side sorting of different observation dates.
        db = DB()
        result = list(public_observations(db, D - dt.timedelta(days=1), D, ['v']))
        self.assertEqual(len(result), 2)
        self.assertEqual([r['as_of_date'] for r in result], ['2026-11-13', '2026-11-14'])
        self.assertTrue(any('as_of_date=eq.2026-11-14' in q for q in db.calls))
        self.assertTrue(all('offset=' not in q for q in db.calls))

    def test_fallback_after_published_pages_never_repeats_earlier_id(self):
        class DB:
            def __init__(self):
                self.calls = []
            def select(self, table, query):
                self.calls.append(query)
                if '&as_of_date=gte.' in query:
                    if len(self.calls) == 1:
                        return [row(i) for i in range(1, 501)]
                    raise RuntimeError('{"code":"57014"}')
                # The completed first page used IDs through 00000500.
                if '&as_of_date=eq.2026-11-14' in query and '&id=gt.00000500' in query:
                    return [row(501)]
                return []
        db=DB()
        result=list(public_observations(db,D,D,['v']))
        self.assertEqual(len(result),501)
        self.assertEqual(result[-1]['score'],0)
        self.assertTrue(any('&as_of_date=eq.2026-11-14' in q and '&id=gt.00000500' in q for q in db.calls))

    def test_wrong_day_in_date_fallback_blocks_export(self):
        class DB:
            def select(self, table, query):
                if '&as_of_date=gte.' in query:
                    raise RuntimeError('{"code":"57014"}')
                return [row(1, as_of_date='2026-11-13')]
        with self.assertRaisesRegex(RuntimeError, 'out-of-window'):
            list(public_observations(DB(),D,D,['v']))

    def test_non_timeout_is_not_retried(self):
        class DB:
            def select(self, *args): raise RuntimeError('forbidden')
        with self.assertRaisesRegex(RuntimeError, 'forbidden'):
            list(public_observations(DB(), D, D, ['v']))

    def test_non_monotonic_ids_block_export(self):
        class DB:
            def select(self, *args): return [row(2), row(1)]
        with self.assertRaisesRegex(RuntimeError, 'non-monotonic'):
            list(public_observations(DB(), D, D, ['v']))
