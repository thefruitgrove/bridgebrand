import datetime as dt
import unittest
from bridge_pipeline.run import healthcheck

DAY=dt.date(2026,11,17)
class FakeDB:
    def __init__(self, rows): self.rows=rows; self.query=None
    def select(self, table, query): self.query=query; return self.rows

def row(src,status="success",finished=True):
    return dict(source_id=src,status=status,started_at="2026-11-17T05:15:00+09:00",
                finished_at="2026-11-17T05:30:00+09:00" if finished else None)

class DateScopedHealth(unittest.TestCase):
    def test_same_day_required_succeeded(self):
        db=FakeDB([row("google_news_rss"),row("opendart"),row("google_news_discovery",status="failed")])
        healthcheck(db,DAY)
        self.assertIn("started_at=gte.2026-11-17T00:00:00+09:00",db.query)
    def test_missing_news_fails(self):
        with self.assertRaises(SystemExit): healthcheck(FakeDB([row("opendart")]),DAY)
    def test_running_source_fails(self):
        with self.assertRaises(SystemExit): healthcheck(FakeDB([row("google_news_rss","running",False),row("opendart")]),DAY)
    def test_latest_failure_overrides_older_success(self):
        with self.assertRaises(SystemExit): healthcheck(FakeDB([row("google_news_rss","failed"),row("google_news_rss"),row("opendart")]),DAY)
