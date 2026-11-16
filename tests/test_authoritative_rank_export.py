"""Published rank integrity must survive DB -> public export.

Two published subjects can share a rounded score while the authoritative
ranking order uses an independent tiebreaker. The export layer is not allowed
to re-rank these subjects by external_id.
"""
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bridge_pipeline import run as pipeline


METHOD = "2026.10-v5-beta1"
DATE = dt.date(2026, 11, 14)


class AuthoritativeRankExportTests(unittest.TestCase):
    def rows(self):
        return [
            dict(
                external_id="STAR-096", domain="ENT", ranking_type="T100",
                as_of_date=DATE.isoformat(), methodology_version=METHOD,
                score=53.65, rank=1, previous_rank=3, rank_change=2,
                axes_available=2, axis_status={"B": "observed", "R": "maintained"},
            ),
            dict(
                external_id="STAR-016", domain="ENT", ranking_type="T100",
                as_of_date=DATE.isoformat(), methodology_version=METHOD,
                score=53.65, rank=2, previous_rank=6, rank_change=4,
                axes_available=2, axis_status={"B": "observed", "R": "maintained"},
            ),
        ]

    def export(self, rows):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "site" / "data").mkdir(parents=True)
            (root / "data").mkdir()
            def write_history(_db, _date):
                (root / "site" / "data" / "history.json").write_text(
                    json.dumps({"rankings": rows}, ensure_ascii=False), encoding="utf-8"
                )
            with (
                patch.object(pipeline, "ROOT", root),
                patch.object(pipeline, "export_history", side_effect=write_history),
                patch.object(pipeline, "load_methodology", return_value={
                    "version": METHOD, "minimum_publishable_axes": 2,
                }),
            ):
                pipeline.export_latest(object(), DATE)
            return json.loads((root / "site" / "data" / "latest.json").read_text(encoding="utf-8"))

    def test_db_tie_order_and_rank_changes_remain_authoritative(self):
        payload = self.export(self.rows())
        self.assertEqual(
            [(r["external_id"], r["rank"], r["rank_change"]) for r in payload["rankings"]],
            [("STAR-096", 1, 2), ("STAR-016", 2, 4)]
        )

    def test_duplicate_rank_blocks_publication(self):
        rows = self.rows()
        rows[1]["rank"] = 1
        with self.assertRaisesRegex(RuntimeError, "duplicate published ranks"):
            self.export(rows)

    def test_score_order_conflict_blocks_publication(self):
        rows = self.rows()
        rows[0]["score"] = 40
        rows[1]["score"] = 60
        with self.assertRaisesRegex(RuntimeError, "rank/score order inconsistent"):
            self.export(rows)


if __name__ == "__main__":
    unittest.main()
