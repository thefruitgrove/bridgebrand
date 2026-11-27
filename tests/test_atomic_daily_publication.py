"""Fail-closed contract for atomic daily promotion; no legacy PATCH calls."""
import datetime as dt
import unittest
from unittest.mock import patch

from bridge_pipeline.run import publish_daily_beta


class DatabaseStub:
    def __init__(self, result=None, error=None):
        self.result = result or {
            "status": "published", "verifiedRows": 400, "affectedRows": 400
        }
        self.error = error
        self.calls = []
    def select(self, table, query):
        self.calls.append(("select", table, query))
        return [{"id": "candidate"}]
    def request(self, method, resource, payload=None, **kwargs):
        self.calls.append(("request", method, resource, payload))
        if self.error:
            raise self.error
        return self.result
    def patch(self, *args, **kwargs):
        raise AssertionError("Legacy multi-request PATCH publishing is forbidden")


class AtomicDailyPublicationTests(unittest.TestCase):
    def test_calls_single_rpc_after_readonly_precheck(self):
        db = DatabaseStub()
        with patch("tools.prepublish_contract.check", return_value={"ok": True}) as check:
            publish_daily_beta(db, dt.date(2026, 11, 27))
        self.assertEqual(check.call_count, 1)
        rpc = [c for c in db.calls if c[0] == "request"]
        self.assertEqual(len(rpc), 1)
        self.assertEqual(rpc[0][1:3], ("POST", "rpc/bridge_publish_daily_atomic"))
        self.assertEqual(rpc[0][3]["p_date"], "2026-11-27")
        self.assertEqual(rpc[0][3]["p_version"], "2026.10-v5-beta1")

    def test_precheck_failure_prevents_db_write(self):
        db = DatabaseStub()
        with patch("tools.prepublish_contract.check", side_effect=RuntimeError("invalid rank")):
            with self.assertRaisesRegex(RuntimeError, "invalid rank"):
                publish_daily_beta(db, dt.date(2026, 11, 27))
        self.assertFalse(any(c[0] == "request" for c in db.calls))

    def test_rpc_error_never_uses_partial_patch(self):
        db = DatabaseStub(error=RuntimeError("DB promotion failed"))
        with patch("tools.prepublish_contract.check", return_value={"ok": True}):
            with self.assertRaisesRegex(RuntimeError, "DB promotion failed"):
                publish_daily_beta(db, dt.date(2026, 11, 27))
        self.assertEqual(len([c for c in db.calls if c[0] == "request"]), 1)

    def test_incomplete_rpc_response_blocks_release(self):
        db = DatabaseStub(result={"status": "published", "verifiedRows": 399, "affectedRows": 399})
        with patch("tools.prepublish_contract.check", return_value={"ok": True}):
            with self.assertRaisesRegex(RuntimeError, "invalid result"):
                publish_daily_beta(db, dt.date(2026, 11, 27))

    def test_idempotent_publication_response(self):
        db = DatabaseStub(result={"status": "already_published", "verifiedRows": 400, "affectedRows": 400})
        with patch("tools.prepublish_contract.check", return_value={"ok": True}):
            publish_daily_beta(db, dt.date(2026, 11, 27))


if __name__ == "__main__":
    unittest.main()
