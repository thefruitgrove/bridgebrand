"""Live BRIDGE rank integrity: matching snapshot IDs cannot hide tampering."""
import copy
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.verify_live import content_integrity, verify


def sample():
    rows = []
    for domain in ("CPR", "STAR", "GOV", "UNI"):
        for rank in range(1, 101):
            rows.append({
                "domain": domain, "external_id": f"{domain}-{rank:03d}",
                "rank": rank, "score": 99 - 0.1 * rank,
                "trust_grade": "B", "axis_scores": {"B": 80.0, "R": 75.0},
                "axis_evidence_dates": {"B": "2026-11-27"},
                "axis_status": {"B": "observed"},
                "methodology_version": "2026.10-v5-beta1",
            })
    return {"asOfDate": "2026-11-27", "recordCount": 400,
            "dataStatus": "published", "snapshotId": "same-id", "rankings": rows}


class FullContentIntegrityTests(unittest.TestCase):
    def test_400_identical_records_pass(self):
        src = sample()
        self.assertEqual(content_integrity(src, copy.deepcopy(src)), [])

    def test_reordered_records_still_pass(self):
        src = sample()
        live = copy.deepcopy(src)
        live["rankings"] = list(reversed(live["rankings"]))
        self.assertEqual(content_integrity(src, live), [])

    def test_same_snapshot_id_but_changed_score_fails(self):
        src = sample()
        live = copy.deepcopy(src)
        live["rankings"][0]["score"] = 99
        self.assertIn("live_ranking_content_mismatch", content_integrity(src, live))

    def test_same_snapshot_id_but_changed_axis_evidence_date_fails(self):
        src = sample()
        live = copy.deepcopy(src)
        live["rankings"][0]["axis_evidence_dates"]["B"] = "2026-11-25"
        self.assertIn("live_ranking_content_mismatch", content_integrity(src, live))

    def test_duplicate_rank_and_duplicate_entity_are_detected(self):
        src = sample()
        live = copy.deepcopy(src)
        live["rankings"][101]["rank"] = 1
        live["rankings"][102]["external_id"] = live["rankings"][101]["external_id"]
        issues = content_integrity(src, live)
        self.assertIn("invalid_live_domain_ranks:STAR", issues)
        self.assertIn("duplicate_or_missing_live_entities:STAR", issues)

    def test_missing_domain_and_field_failure(self):
        src = sample()
        live = copy.deepcopy(src)
        live["rankings"][0]["domain"] = "GOV"
        live["rankings"][200]["trust_grade"] = None
        issues = content_integrity(src, live)
        self.assertIn("invalid_live_domain_quota:CPR", issues)
        self.assertIn("invalid_live_domain_quota:GOV", issues)
        self.assertIn("incomplete_live_ranking_fields:GOV", issues)

    def test_current_site_verification_is_fail_closed_on_content_diff(self):
        source = sample()
        deployed = copy.deepcopy(source)
        deployed["rankings"][0]["score"] += 2
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "latest.json"
            path.write_text(json.dumps(source, ensure_ascii=False), encoding="utf-8")
            def fake_fetch(origin, name):
                if name == "data/latest.json":
                    return json.dumps(deployed, ensure_ascii=False).encode()
                return b"2026-11-27 \xea\xb8\xb0\xec\xa4\x80"
            with patch("tools.verify_live.fetch", side_effect=fake_fetch):
                result = verify("https://bridgebrand.co.kr", path,
                                dt.date(2026, 11, 27), max_age_days=0)
        self.assertEqual(result["status"], "failure")
        self.assertIn("live_ranking_content_mismatch", result["issues"])


if __name__ == "__main__":
    unittest.main()
