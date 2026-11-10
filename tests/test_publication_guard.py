import datetime as dt
import inspect
import unittest

from bridge_pipeline.run import publish_daily_beta, score_day


# Regression contract: fixed T100 publication scope must not regress to score-level eligibility filtering.
class PublicationGuardTest(unittest.TestCase):
    def test_daily_beta_publishes_only_current_configured_ranking_scope(self):
        class DB:
            def __init__(self):
                self.calls = []

            def select(self, table, query):
                self.assert_scope(query)
                if table == "bridge_rankings":
                    self.assert_scope(query)
                    self_query = query
                    assert "select=id&" in self_query
                    assert "&limit=1" in self_query
                    return [{"id": "rank"}]
                raise AssertionError(f"unexpected select table: {table}")

            @staticmethod
            def assert_scope(query):
                assert "as_of_date=eq.2026-10-14" in query
                assert "methodology_version=eq." in query
                assert "domain=in.(" in query
                assert "ranking_type=in.(" in query
                assert "entity_id=in." not in query

            def patch(self, table, values, query):
                self.assert_scope(query)
                self.calls.append((table, values, query))

        db = DB()
        publish_daily_beta(db, dt.date(2026, 10, 14))

        self.assertEqual(len(db.calls), 2)
        self.assertEqual(db.calls[0][0], "bridge_rankings")
        self.assertEqual(db.calls[0][1], {"published_at": None})
        self.assertEqual(db.calls[1][0], "bridge_rankings")
        self.assertIsNotNone(db.calls[1][1]["published_at"])
        self.assertEqual(db.calls[0][2], db.calls[1][2])

    def test_no_current_eligible_scores_blocks_publication(self):
        class DB:
            def select(self, *args):
                return []

            def patch(self, *args):
                raise AssertionError("must not publish")

        with self.assertRaises(RuntimeError):
            publish_daily_beta(DB(), dt.date(2026, 10, 14))

    def test_scoring_never_resets_existing_publication_state(self):
        """A retry may refresh scores, but only publish commands own published_at."""
        self.assertNotIn('"published_at": None', inspect.getsource(score_day))
