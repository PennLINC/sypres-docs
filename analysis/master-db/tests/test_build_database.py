"""Tests for build_database.py (stdlib unittest — no dependencies).

Run from the repo root:

    python3 -m unittest discover -s analysis/master-db/tests
    # or
    python3 analysis/master-db/tests/test_build_database.py

Two kinds of tests:
  * Unit tests of the pure helpers (parsing, normalization, derivation).
  * Integration tests of build() against the real exports in ../data, split into
    structural INVARIANTS (must always hold) and CURRENT-FIXTURE counts (update
    these when the Covidence exports change).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build_database as bd  # noqa: E402


class TestHelpers(unittest.TestCase):
    def test_norm_covidence(self):
        self.assertEqual(bd._norm_covidence("#28318"), 28318)
        self.assertEqual(bd._norm_covidence("28318"), 28318)
        self.assertIsNone(bd._norm_covidence(""))
        self.assertIsNone(bd._norm_covidence(None))

    def test_parse_pages(self):
        self.assertEqual(bd._parse_pages("2152-2162"), ("2152", "2162"))
        self.assertEqual(bd._parse_pages("236-44"), ("236", "44"))
        self.assertEqual(bd._parse_pages("S105-S105"), ("S105", "S105"))
        self.assertEqual(bd._parse_pages("694-701"), ("694", "701"))
        self.assertEqual(bd._parse_pages("2152–2162"), ("2152", "2162"))  # en dash
        self.assertEqual(bd._parse_pages("20494637251371626"), ("20494637251371626", ""))
        self.assertEqual(bd._parse_pages(""), ("", ""))

    def test_split_list(self):
        self.assertEqual(bd._split_list("a; b ;c"), ["a", "b", "c"])
        self.assertEqual(bd._split_list(""), [])

    def test_to_int(self):
        self.assertEqual(bd._to_int("Other: 10"), 10)
        self.assertEqual(bd._to_int("4"), 4)
        self.assertIsNone(bd._to_int(""))
        self.assertIsNone(bd._to_int("none"))

    def test_yes_no(self):
        self.assertEqual(bd._yes_no("yes"), "yes")
        self.assertEqual(bd._yes_no("No"), "no")
        self.assertEqual(bd._yes_no(""), "unknown")
        self.assertEqual(bd._yes_no("maybe"), "unknown")

    def test_derive_drug(self):
        self.assertEqual(bd._derive(bd.DRUG_PATTERNS, "lysergic acid diethylamide"), "LSD")
        self.assertEqual(bd._derive(bd.DRUG_PATTERNS, "effects of MDMA (ecstasy)"), "MDMA")
        self.assertEqual(bd._derive(bd.DRUG_PATTERNS, "psilocybin for OCD"), "Psilocybin")
        self.assertIsNone(bd._derive(bd.DRUG_PATTERNS, "a study of aspirin"))

    def test_derive_indication(self):
        self.assertEqual(bd._derive(bd.INDICATION_PATTERNS, "treatment of PTSD"), "PTSD")
        self.assertEqual(bd._derive(bd.INDICATION_PATTERNS, "major depression"), "Depression")
        self.assertEqual(bd._derive(bd.INDICATION_PATTERNS, "alcoholism trial"), "Alcohol use")

    def test_registry_url(self):
        self.assertEqual(bd._registry_url("NCT04865653"),
                         "https://clinicaltrials.gov/study/NCT04865653")
        self.assertEqual(bd._registry_url("ClinicalTrials.gov/NCT03790358"),
                         "https://clinicaltrials.gov/study/NCT03790358")
        self.assertEqual(bd._registry_url("NL70508.068.1"), "")  # non-NCT → no link
        self.assertEqual(bd._registry_url(""), "")

    def test_study_url(self):
        self.assertEqual(bd._study_url("10.1/x", ""), "https://doi.org/10.1/x")
        self.assertEqual(bd._study_url("https://doi.org/10.1/x", ""), "https://doi.org/10.1/x")
        self.assertEqual(bd._study_url("", "123"), "https://pubmed.ncbi.nlm.nih.gov/123/")
        self.assertEqual(bd._study_url("", ""), "")

    def test_classify(self):
        self.assertEqual(bd._classify("x_included_csv.csv",
                                      ["Title", "Abstract", "Covidence #", "Study"]), "included")
        self.assertEqual(bd._classify("x.csv",
                                      ["Covidence #", "Reviewer Name", "Study type"]), "extraction")
        self.assertIsNone(bd._classify("x_screen_csv.csv",
                                       ["Title", "Abstract", "Covidence #"]))

    def test_stage_path_disambiguates_included_excluded(self):
        inc, exc = bd._stage_path("included"), bd._stage_path("excluded")
        self.assertIsNotNone(inc)
        self.assertIn("included", os.path.basename(inc).lower())
        self.assertNotIn("excluded", os.path.basename(inc).lower())
        if exc:
            self.assertIn("excluded", os.path.basename(exc).lower())


class TestBuildIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = bd.build()
        cls.studies = cls.out["studies"]
        cls.prisma = cls.out["prisma"]
        cls.meta = cls.out["meta"]

    # ---- structural invariants (should always hold) ----
    def test_shape(self):
        self.assertEqual(set(self.out), {"meta", "prisma", "studies"})
        self.assertGreater(len(self.studies), 0)

    def test_every_study_has_core_keys(self):
        core = {"covidence_id", "study_id", "title", "drug", "indication",
                "extracted", "outcomes", "url"}
        for s in self.studies:
            self.assertTrue(core <= set(s), f"missing keys in {s.get('study_id')}")

    def test_extracted_studies_are_complete(self):
        for s in self.studies:
            if s["extracted"]:
                self.assertTrue(s["reviewer"], f"{s['study_id']} extracted w/o reviewer")
                self.assertTrue(s["outcomes"], f"{s['study_id']} extracted w/o outcomes")
                self.assertEqual(s["drug_source"], "extracted")

    def test_doi_coalesce_and_url_fallback(self):
        for s in self.studies:
            # DOI-less records must still get a URL when a PMID exists, and none otherwise.
            if not s["doi"] and s["pmid"]:
                self.assertEqual(s["url"], f"https://pubmed.ncbi.nlm.nih.gov/{s['pmid']}/")
            if not s["doi"] and not s["pmid"]:
                self.assertEqual(s["url"], "")

    def test_sorted_newest_first(self):
        years = [s["year"] or 0 for s in self.studies]
        self.assertEqual(years, sorted(years, reverse=True))

    def test_meta_outcomes_is_superset(self):
        all_outcomes = {o for s in self.studies for o in s["outcomes"]}
        self.assertEqual(set(self.meta["outcomes"]), all_outcomes)
        self.assertEqual(self.meta["outcomes"], sorted(self.meta["outcomes"]))

    def test_prisma_reconciles(self):
        p = self.prisma
        # records flow conserves: screening + advanced == total
        self.assertEqual(p["records_in_review"],
                         p["in_screening"] + p["advanced_to_fulltext"])
        # everything that advanced is included, excluded, or still under review
        self.assertEqual(p["advanced_to_fulltext"],
                         p["included"] + p["fulltext_excluded"] + p["fulltext_in_review"])
        self.assertLessEqual(p["extracted"], p["included"])
        self.assertEqual(sum(p["fulltext_excluded_reasons"].values()), p["fulltext_excluded"])

    def test_prisma_manual_block_present(self):
        m = self.prisma["manual"]
        for k in ("records_identified", "duplicates_removed",
                  "excluded_title_abstract", "records_screened", "complete"):
            self.assertIn(k, m)
        # committed prisma_manual.json ships with nulls → incomplete, no screened total
        self.assertFalse(m["complete"])
        self.assertIsNone(m["records_screened"])

    def test_prisma_manual_when_supplied(self):
        import json
        import tempfile
        orig = bd.MANUAL_PATH
        tmp = None
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
                json.dump({"records_identified": 6000, "duplicates_removed": 900,
                           "excluded_title_abstract": 4920}, fh)
                tmp = fh.name
            bd.MANUAL_PATH = tmp
            pr = bd.build_prisma(4)
            self.assertTrue(pr["manual"]["complete"])
            # records screened = records still in review + those excluded at title/abstract
            self.assertEqual(pr["manual"]["records_screened"],
                             pr["records_in_review"] + 4920)
        finally:
            bd.MANUAL_PATH = orig
            if tmp:
                os.unlink(tmp)

    # ---- current-fixture counts (update when the Covidence exports change) ----
    def test_current_counts(self):
        self.assertEqual(self.meta["n_included"], 19)
        self.assertEqual(self.meta["n_extracted"], 4)
        self.assertEqual(self.meta["drugs"], ["LSD", "MDMA", "Psilocybin"])
        p = self.prisma
        self.assertEqual(p["records_in_review"], 4563)
        self.assertEqual(p["in_screening"], 4426)
        self.assertEqual(p["advanced_to_fulltext"], 137)
        self.assertEqual(p["included"], 19)
        self.assertEqual(p["fulltext_excluded"], 2)
        self.assertEqual(p["fulltext_in_review"], 116)


if __name__ == "__main__":
    unittest.main(verbosity=2)
