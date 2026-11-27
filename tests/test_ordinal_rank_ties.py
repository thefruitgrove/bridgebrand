"""Regression tests for BRIDGE T100 unique rank contract."""
import unittest
from bridge_pipeline.core import robust_rank


class OrdinalRankingTests(unittest.TestCase):
    def test_exact_ties_have_stable_unique_rank(self):
        rows = [
            {"external_id": "UNI-U55", "score": 56.79, "confidence_score": 69.27},
            {"external_id": "UNI-U08", "score": 56.79, "confidence_score": 69.27},
            {"external_id": "UNI-U90", "score": 54.11, "confidence_score": 72.0},
        ]
        result = robust_rank(rows)
        self.assertEqual([r["external_id"] for r in result], ["UNI-U08", "UNI-U55", "UNI-U90"])
        self.assertEqual([r["rank"] for r in result], [1, 2, 3])
        self.assertEqual(result[0]["score"], result[1]["score"])

    def test_confidence_breaks_score_tie_before_id(self):
        rows = [
            {"external_id": "B", "score": 70, "confidence_score": 65},
            {"external_id": "A", "score": 70, "confidence_score": 80},
        ]
        self.assertEqual([r["external_id"] for r in robust_rank(rows)], ["A", "B"])
        self.assertEqual([r["rank"] for r in robust_rank(rows)], [1, 2])


if __name__ == "__main__":
    unittest.main()
