"""Production release safety: reject partial, tied, and unlinked panels."""
import copy
import datetime as dt
import unittest

from tools.prepublish_contract import validate_rows


DAY = dt.date(2026, 11, 27)
DOMAINS = ["CPR", "STAR", "GOV", "UNI"]
VERSION = "2026.10-v5-beta1"


def fixture():
    rankings, scores, metrics = [], [], []
    for domain in DOMAINS:
        for rank in range(1, 101):
            entity = f"{domain}-{rank:03d}"
            score = round(99 - rank * 0.4, 2)
            rankings.append({"entity_id": entity, "domain": domain, "ranking_type": "T100",
                             "rank": rank, "score": score, "trust_grade": "B",
                             "methodology_version": VERSION})
            scores.append({"entity_id": entity, "score": score, "trust_grade": "B",
                           "methodology_version": VERSION})
            metrics.append({"entity_id": entity})
    return rankings, scores, metrics


class PrepublicationContractTests(unittest.TestCase):
    def check(self, rankings=None, scores=None, metrics=None):
        full = fixture()
        return validate_rows(rankings if rankings is not None else full[0],
                             scores if scores is not None else full[1],
                             metrics if metrics is not None else full[2], DOMAINS, DAY)

    def test_valid_four_domains(self):
        result = self.check()
        self.assertTrue(result["ok"])
        self.assertEqual(result["actual_total"], 400)

    def test_uni_duplicate_rank_is_blocked_before_publish(self):
        ranks, scores, metrics = fixture()
        rows = [r for r in ranks if r["domain"] == "UNI"]
        rows[40]["rank"] = 40
        with self.assertRaisesRegex(RuntimeError, "non-contiguous or duplicate ranks"):
            self.check(ranks, scores, metrics)

    def test_missing_domain_rank_is_blocked(self):
        ranks, scores, metrics = fixture()
        ranks.pop()
        with self.assertRaisesRegex(RuntimeError, "ranking count"):
            self.check(ranks, scores, metrics)

    def test_wrong_score_and_trust_grade_are_blocked(self):
        ranks, scores, metrics = fixture()
        ranks[0]["trust_grade"] = "A"
        with self.assertRaisesRegex(RuntimeError, "score/trust mismatch"):
            self.check(ranks, scores, metrics)

    def test_missing_metrics_are_blocked(self):
        ranks, scores, metrics = fixture()
        with self.assertRaisesRegex(RuntimeError, "metrics count"):
            self.check(ranks, scores, metrics[:-1])

    def test_inverted_score_order_is_blocked(self):
        ranks, scores, metrics = fixture()
        ranks[1]["score"] = 100
        with self.assertRaisesRegex(RuntimeError, "ascending score"):
            self.check(ranks, scores, metrics)


if __name__ == "__main__":
    unittest.main()
