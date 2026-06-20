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

    def test_norm_registry(self):
        self.assertEqual(bd._norm_registry("NCT04865653"), "NCT04865653")
        self.assertEqual(bd._norm_registry("ClinicalTrials.gov/NCT03790358"), "NCT03790358")
        self.assertEqual(bd._norm_registry("NL70508.068.1; NL-OMON55178"), "NL70508.068.1")
        self.assertEqual(bd._norm_registry("WOS:000645683800249"), "")  # not a registry
        self.assertEqual(bd._norm_registry(""), "")

    def test_link_trials_groups_shared_registry(self):
        studies = [
            {"covidence_id": 1, "doi": "10.1/primary", "registry": "NCT999", "parent_study_doi": ""},
            {"covidence_id": 2, "doi": "10.2/secondary", "registry": "ClinicalTrials.gov/NCT999",
             "parent_study_doi": ""},
            # registry-less secondary analysis linked to #1 via parent DOI
            {"covidence_id": 3, "doi": "10.3/reanalysis", "registry": "",
             "parent_study_doi": "https://doi.org/10.1/primary"},
            # unrelated, unregistered → its own (singleton) trial
            {"covidence_id": 4, "doi": "10.4/solo", "registry": "", "parent_study_doi": ""},
        ]
        by_key = bd._link_trials(studies)
        self.assertEqual(sorted(by_key["NCT999"]), [1, 2, 3])
        self.assertEqual(set(studies[0]["connected_ids"]), {2, 3})
        self.assertEqual(studies[2]["trial_key"], "NCT999")   # via parent DOI
        self.assertIsNone(studies[3]["trial_key"])            # unregistered singleton
        self.assertEqual(studies[3]["connected_ids"], [])

    def test_parse_ctgov(self):
        raw = {
            "hasResults": True,
            "protocolSection": {
                "identificationModule": {"officialTitle": "A Trial", "briefTitle": "AT"},
                "statusModule": {"overallStatus": "COMPLETED",
                                 "startDateStruct": {"date": "2020-01-01"},
                                 "completionDateStruct": {"date": "2022-01-01"}},
                "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Acme", "class": "INDUSTRY"}},
                "designModule": {"studyType": "INTERVENTIONAL", "phases": ["PHASE2"],
                                 "designInfo": {"allocation": "RANDOMIZED", "interventionModel": "PARALLEL",
                                                "maskingInfo": {"masking": "TRIPLE",
                                                                "whoMasked": ["PARTICIPANT", "INVESTIGATOR"]}},
                                 "enrollmentInfo": {"count": 42, "type": "ACTUAL"}},
                "conditionsModule": {"conditions": ["PTSD"]},
                "armsInterventionsModule": {"armGroups": [{"label": "High dose", "type": "EXPERIMENTAL"}]},
                "outcomesModule": {"primaryOutcomes": [{"measure": "CAPS-5", "timeFrame": "8 weeks"}]},
                "contactsLocationsModule": {"locations": [{"country": "United States"},
                                                          {"country": "United States"}, {"country": "Canada"}]},
            },
        }
        d = bd._parse_ctgov(raw)
        self.assertEqual(d["title"], "A Trial")
        self.assertEqual(d["status"], "Completed")
        self.assertEqual(d["study_type"], "Interventional")
        self.assertEqual(d["phase"], "Phase 2")
        self.assertEqual([d["allocation"], d["model"]], ["Randomized", "Parallel"])
        self.assertTrue(d["masking"].startswith("Triple (participant, investigator"))
        self.assertEqual(d["enrollment"], 42)
        self.assertEqual(d["arms"], ["High dose — Experimental"])
        self.assertTrue(d["industry"])
        self.assertEqual(d["countries"], ["United States", "Canada"])  # de-duped
        self.assertEqual(d["primary_outcomes"], ["CAPS-5 — 8 weeks"])
        self.assertTrue(d["results_posted"])
        self.assertIsNone(bd._parse_ctgov(None))
        self.assertIsNone(bd._parse_ctgov({}))

    def test_build_trials_offline(self):
        # fetch=False → never hits the network; uses cache only if present
        studies = [
            {"covidence_id": 1, "trial_key": "NCT01211405", "registry_norm": "NCT01211405"},
            {"covidence_id": 2, "trial_key": "NL123", "registry_norm": "NL123"},
            {"covidence_id": 3, "trial_key": None, "registry_norm": ""},  # unregistered
        ]
        trials = bd.build_trials(studies, fetch=False)
        self.assertEqual({t["trial_key"] for t in trials}, {"NCT01211405", "NL123"})  # excludes #3
        nl = next(t for t in trials if t["trial_key"] == "NL123")
        self.assertEqual(nl["fetch_status"], "unsupported_registry")
        self.assertIsNone(nl["details"])
        nct = next(t for t in trials if t["trial_key"] == "NCT01211405")
        self.assertEqual(nct["paper_ids"], [1])
        self.assertIn(nct["fetch_status"], ("ok", "not_fetched"))  # cache-dependent, never network


class TestBuildIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = bd.build()
        cls.studies = cls.out["studies"]
        cls.prisma = cls.out["prisma"]
        cls.meta = cls.out["meta"]

    # ---- structural invariants (should always hold) ----
    def test_shape(self):
        self.assertEqual(set(self.out), {"meta", "prisma", "trials", "studies"})
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

    def test_trial_linkage(self):
        for s in self.studies:
            self.assertIn("registry_norm", s)
            self.assertIn("connected_ids", s)
            # a study never lists itself as connected
            self.assertNotIn(s["covidence_id"], s["connected_ids"])
            # connections are symmetric and share the trial key
            for cid in s["connected_ids"]:
                other = next(x for x in self.studies if x["covidence_id"] == cid)
                self.assertEqual(other["trial_key"], s["trial_key"])
                self.assertIn(s["covidence_id"], other["connected_ids"])
        # meta exposes the registry list + trial counts for the dashboard facet
        self.assertEqual(self.meta["registries"],
                         sorted({s["registry_norm"] for s in self.studies if s["registry_norm"]}))
        self.assertLessEqual(self.meta["n_trials"], self.meta["n_included"])

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
