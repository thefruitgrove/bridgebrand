import unittest

from bridge_pipeline.gov_youtube import (
    approved_identity_score, percentile_scores, score_cohorts, title_matches_entity,
)


class GovYoutubeTest(unittest.TestCase):
    def test_percentiles_keep_ties_equal(self):
        result = percentile_scores({"a": 10, "b": 10, "c": 20})
        self.assertEqual(result["a"], result["b"])
        self.assertEqual(result["c"], 100)

    def test_scores_are_cohort_specific(self):
        rows = {
            "GOV-M01": {"metrics": {"views": 100, "median_views_per_day": 10, "engagement_per_1000_views": 2}},
            "GOV-M02": {"metrics": {"views": 200, "median_views_per_day": 20, "engagement_per_1000_views": 4}},
            "GOV-C01": {"metrics": {"views": 5, "median_views_per_day": 1, "engagement_per_1000_views": 1}},
        }
        result = score_cohorts(rows)
        self.assertEqual(result["GOV-M02"]["B"], 100)
        self.assertEqual(result["GOV-C01"]["B"], 50)

    def test_identity_penalty_requires_approval_and_evidence(self):
        pending = {"reviews": {"GOV-C35": {"status": "pending", "penalty": 15, "evidence_urls": ["x"]}}}
        approved = {"reviews": {"GOV-C35": {"status": "approved", "penalty": 15, "evidence_urls": ["x"]}}}
        self.assertIsNone(approved_identity_score("GOV-C35", pending))
        self.assertEqual(approved_identity_score("GOV-C35", approved), 85)

    def test_title_verification_accepts_public_short_name(self):
        entity = {"name": "서울특별시", "aliases": []}
        self.assertTrue(title_matches_entity("서울시 공식 유튜브", entity))
        self.assertFalse(title_matches_entity("서울 맛집 개인 채널", entity))


if __name__ == "__main__":
    unittest.main()
