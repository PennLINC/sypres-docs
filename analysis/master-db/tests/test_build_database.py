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

    def test_split_list_ignores_separators_inside_parens(self):
        # controlled-vocabulary labels may contain the separator character
        self.assertEqual(bd._split_list("Acute; Persisting (PEQ; not HPPD)"),
                         ["Acute", "Persisting (PEQ; not HPPD)"])
        self.assertEqual(bd._split_list("vitals (HR, HRV, BP, etc.)"),
                         ["vitals (HR, HRV, BP, etc.)"])

    def test_to_int(self):
        self.assertEqual(bd._to_int("Other: 10"), 10)
        self.assertEqual(bd._to_int("4"), 4)
        self.assertIsNone(bd._to_int(""))
        self.assertIsNone(bd._to_int("none"))

    def test_derive_drug(self):
        self.assertEqual(bd._derive(bd.DRUG_PATTERNS, "lysergic acid diethylamide"), "LSD")
        self.assertEqual(bd._derive(bd.DRUG_PATTERNS, "effects of MDMA (ecstasy)"), "MDMA")
        self.assertEqual(bd._derive(bd.DRUG_PATTERNS, "psilocybin for OCD"), "Psilocybin")
        self.assertIsNone(bd._derive(bd.DRUG_PATTERNS, "a study of aspirin"))

    def test_derive_all_returns_every_match(self):
        # multi-drug comparison studies must not collapse to a single agent
        self.assertEqual(bd._derive_all(bd.DRUG_PATTERNS, "2C-B compared with MDMA and psilocybin"),
                         ["MDMA", "Psilocybin", "2C-B"])
        # MDA must not be swallowed by MDMA, and vice versa
        self.assertEqual(bd._derive_all(bd.DRUG_PATTERNS, "effects of MDA"), ["MDA"])
        self.assertEqual(bd._derive_all(bd.DRUG_PATTERNS, "effects of MDMA"), ["MDMA"])
        self.assertEqual(bd._derive_all(bd.DRUG_PATTERNS, "aspirin"), [])

    def test_norm_drugs(self):
        # order follows the reviewer's cell, not the vocabulary
        self.assertEqual(bd._norm_drugs("2C-B; MDMA; psilocybin"), ["2C-B", "MDMA", "Psilocybin"])
        self.assertEqual(bd._norm_drugs("salvinorin A"), ["Salvinorin A"])
        self.assertEqual(bd._norm_drugs("Other: MDA"), ["MDA"])
        # outside the vocabulary → kept verbatim rather than dropped
        self.assertEqual(bd._norm_drugs("Other: 4-Fluoroamphetamine"), ["4-Fluoroamphetamine"])
        self.assertEqual(bd._norm_drugs("Other: harmine"), ["Harmine"])
        # ayahuasca is its own facet, not folded into DMT
        self.assertEqual(bd._norm_drugs("ayahuasca"), ["Ayahuasca"])
        self.assertEqual(bd._norm_drugs(""), [])

    def test_indication_from_prefers_clinical_over_healthy(self):
        self.assertEqual(bd._indication_from("healthy volunteers"), "Healthy volunteers")
        self.assertEqual(bd._indication_from("psychedelic-naïve healthy volunteers"),
                         "Healthy volunteers")
        self.assertEqual(bd._indication_from("alcohol use disorder (AUD)"), "Alcohol use")
        self.assertEqual(bd._indication_from("opioid use disorder"), "Opioid use")
        # a named condition wins even when listed after a non-clinical descriptor
        self.assertEqual(
            bd._indication_from("depression; Other: frontline clinicians during COVID-19"),
            "Depression")
        self.assertEqual(bd._indication_from(""), "")

    def test_is_healthy(self):
        self.assertTrue(bd._is_healthy("healthy volunteers"))
        self.assertTrue(bd._is_healthy("psychedelic-naïve healthy volunteers"))
        self.assertFalse(bd._is_healthy("depression; Other: frontline clinicians"))
        self.assertFalse(bd._is_healthy("PTSD"))
        self.assertFalse(bd._is_healthy(""))

    def test_phase(self):
        self.assertEqual(bd._phase("1"), "Phase 1")
        self.assertEqual(bd._phase("3"), "Phase 3")
        self.assertEqual(bd._phase("Not Applicable"), "N/A")
        self.assertEqual(bd._phase("Unregistered"), "")   # not a phase — see _registration_status
        self.assertEqual(bd._phase(""), "")
        # same helper normalizes ClinicalTrials.gov enums
        self.assertEqual(bd._phase("PHASE2"), "Phase 2")
        self.assertEqual(bd._phase("NA"), "N/A")
        self.assertEqual(bd._phase("EARLY_PHASE1"), "Early Phase 1")

    def test_registration_status(self):
        self.assertEqual(bd._registration_status("1", "NCT123"), "registered")
        self.assertEqual(bd._registration_status("Unregistered", ""), "unregistered")
        # a registry id outranks the sentinel if both are somehow present
        self.assertEqual(bd._registration_status("Unregistered", "NCT123"), "registered")
        # a phase with no registry is a contradiction → unknown (build() warns)
        self.assertEqual(bd._registration_status("1", ""), "unknown")
        self.assertEqual(bd._registration_status("", ""), "unknown")

    def test_comparator_types(self):
        self.assertEqual(bd._comparator_types("placebo (niacin, mannitol, sugar pill, etc.)"),
                         ["Placebo"])
        # a study can be both placebo- and active-controlled
        self.assertEqual(
            bd._comparator_types("placebo (niacin, mannitol, sugar pill, etc.); d-amphetamine"),
            ["Placebo", "Active drug"])
        self.assertEqual(bd._comparator_types("low-dose intervention drug"), ["Low-dose active"])
        self.assertEqual(bd._comparator_types("waitlist/care as usual"), ["Waitlist / care as usual"])
        self.assertEqual(bd._comparator_types(""), [])

    def test_outcomes_from_category_columns(self):
        row = {"Cognitive": "social cognition; memory",
               "Drug experience questionnaires": "Acute; Persisting (PEQ; not HPPD)",
               "PK/PD": "PK", "Neuroimaging": ""}
        domains, measures = bd._outcomes(row)
        # domains follow template order, blanks excluded
        self.assertEqual(domains, ["Cognitive", "Drug experience questionnaires", "PK/PD"])
        self.assertEqual(measures, [
            "Cognitive: social cognition", "Cognitive: memory",
            "Drug experience questionnaires: Acute",
            "Drug experience questionnaires: Persisting (PEQ; not HPPD)",
            "PK/PD: PK"])
        self.assertEqual(bd._outcomes({}), ([], []))

    def test_norm_doi(self):
        self.assertEqual(bd._norm_doi("https://doi.org/10.1/X "), "10.1/x")
        self.assertEqual(bd._norm_doi(" 10.1007/s00213-011-2470-6 "), "10.1007/s00213-011-2470-6")
        self.assertEqual(bd._norm_doi("doi: 10.1/x."), "10.1/x")
        self.assertEqual(bd._norm_doi(""), "")

    def test_registry_url(self):
        self.assertEqual(bd._registry_url("NCT04865653"),
                         "https://clinicaltrials.gov/study/NCT04865653")
        self.assertEqual(bd._registry_url("ClinicalTrials.gov/NCT03790358"),
                         "https://clinicaltrials.gov/study/NCT03790358")
        self.assertEqual(bd._registry_url(""), "")

    def test_registry_url_non_nct(self):
        """Every recognized registry gets a link; unlinkable ones fall back to ICTRP."""
        self.assertEqual(bd._registry_url("ISRCTN14080164"),
                         "https://www.isrctn.com/ISRCTN14080164")
        self.assertEqual(bd._registry_url("ACTRN12621000436875"),
                         "https://www.anzctr.org.au/ACTRN12621000436875.aspx")
        self.assertEqual(bd._registry_url("DRKS00013279"),
                         "https://drks.de/search/en/trial/DRKS00013279")
        # Dutch cells list the ABR number first, but only the OMON id resolves
        self.assertEqual(bd._registry_url("NL70508.068.1; NL-OMON55178"),
                         "https://onderzoekmetmensen.nl/en/trial/55178")
        # recognized but unlinkable → WHO ICTRP federated search
        self.assertEqual(bd._registry_url("ChiCTR2000034567"),
                         "https://trialsearch.who.int/?TrialID=ChiCTR2000034567")
        # not a registry at all → still no link
        self.assertEqual(bd._registry_url("WOS:000645683800249"), "")

    def test_study_url(self):
        self.assertEqual(bd._study_url("10.1/x", ""), "https://doi.org/10.1/x")
        self.assertEqual(bd._study_url("https://doi.org/10.1/x", ""), "https://doi.org/10.1/x")
        self.assertEqual(bd._study_url("", "123"), "https://pubmed.ncbi.nlm.nih.gov/123/")
        self.assertEqual(bd._study_url("", ""), "")

    def test_classify(self):
        self.assertEqual(bd._classify("x_included_csv.csv",
                                      ["Title", "Abstract", "Covidence #", "Study"]), "included")
        self.assertEqual(bd._classify("x.csv",
                                      ["Covidence #", "Reviewer Name", "Trial Phase"]), "extraction")
        self.assertIsNone(bd._classify("x_screen_csv.csv",
                                       ["Title", "Abstract", "Covidence #"]))

    def test_classify_survives_template_revisions(self):
        """Regression: the classifier must not key on volatile template columns.

        It once required a `Study type` column; when a template revision deleted
        that column the whole extraction export stopped being recognized and
        n_extracted silently fell to 0.
        """
        minimal = ["Covidence #", "Study ID", "Title", "Reviewer Name", "DOI"]
        self.assertEqual(bd._classify("review_1_2026.csv", minimal), "extraction")
        # and the real export on disk is classified
        import csv as _csv
        import glob as _glob
        hits = []
        for path in _glob.glob(os.path.join(bd.DATA_DIR, "*.csv")):
            with open(path, newline="", encoding="utf-8-sig") as fh:
                if bd._classify(path, next(_csv.reader(fh))) == "extraction":
                    hits.append(path)
        self.assertTrue(hits, "no extraction export recognized in data/")

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
        self.assertEqual(bd._norm_registry("ACTRN12621000436875"), "ACTRN12621000436875")
        self.assertEqual(bd._norm_registry("WOS:000645683800249"), "")  # not a registry
        self.assertEqual(bd._norm_registry("CT03019822,"), "")          # typo'd NCT → not a registry
        self.assertEqual(bd._norm_registry(""), "")

    def test_link_trials_groups_shared_registry(self):
        studies = [
            {"covidence_id": 1, "doi": "10.1/primary", "registry": "NCT999", "parent_study_doi": ""},
            {"covidence_id": 2, "doi": "10.2/secondary", "registry": "ClinicalTrials.gov/NCT999",
             "parent_study_doi": ""},
            # registry-less secondary analysis linked to #1 via parent DOI
            {"covidence_id": 3, "doi": "10.3/reanalysis", "registry": "",
             "parent_study_doi": "https://doi.org/10.1/primary"},
            # unrelated, unregistered, uncited → no trial key
            {"covidence_id": 4, "doi": "10.4/solo", "registry": "", "parent_study_doi": ""},
        ]
        by_key = bd._link_trials(studies)
        self.assertEqual(sorted(by_key["NCT999"]), [1, 2, 3])
        self.assertEqual(set(studies[0]["connected_ids"]), {2, 3})
        self.assertEqual(studies[2]["trial_key"], "NCT999")   # inherits parent's registry
        self.assertEqual(studies[2]["trial_key_source"], "parent-registry")
        self.assertIsNone(studies[3]["trial_key"])            # unregistered singleton
        self.assertEqual(studies[3]["connected_ids"], [])

    def test_link_trials_groups_unregistered_reports_by_parent_doi(self):
        """Reports of one UNREGISTERED trial group on the source paper's DOI."""
        studies = [
            # the source paper: unregistered, cited as parent by the two below
            {"covidence_id": 1, "doi": "10.1/source", "registry": "", "parent_study_doi": ""},
            {"covidence_id": 2, "doi": "10.2/report-a", "registry": "",
             "parent_study_doi": "10.1/SOURCE "},          # case + whitespace noise
            {"covidence_id": 3, "doi": "10.3/report-b", "registry": "",
             "parent_study_doi": "https://doi.org/10.1/source"},
            # a report whose parent is NOT in the database still gets a trial key
            {"covidence_id": 4, "doi": "10.4/orphan", "registry": "",
             "parent_study_doi": "10.9/absent"},
        ]
        by_key = bd._link_trials(studies)
        self.assertEqual(sorted(by_key["doi:10.1/source"]), [1, 2, 3])
        self.assertEqual(studies[0]["trial_key_source"], "source-paper")
        self.assertEqual(studies[1]["trial_key_source"], "parent-doi")
        self.assertEqual(set(studies[0]["connected_ids"]), {2, 3})
        self.assertEqual(studies[3]["trial_key"], "doi:10.9/absent")
        self.assertEqual(studies[3]["connected_ids"], [])

    def test_prospective_registration(self):
        self.assertEqual(bd._ym("2009-01-15"), "2009-01")
        self.assertEqual(bd._ym("2009-01"), "2009-01")
        self.assertEqual(bd._ym(""), "")
        # registered before enrolment started
        self.assertTrue(bd._prospective("2017-12-06", "2019-01-07"))
        # registered after — retrospective
        self.assertFalse(bd._prospective("2018-12-21", "2018-05-01"))
        # same month counts as prospective (start dates are often month-only)
        self.assertTrue(bd._prospective("2009-01-14", "2009-01"))
        # unknown must not read as retrospective
        self.assertIsNone(bd._prospective("", "2019-01"))
        self.assertIsNone(bd._prospective("2019-01", ""))

    def test_parse_ctgov(self):
        raw = {
            "hasResults": True,
            "protocolSection": {
                "identificationModule": {"officialTitle": "A Trial", "briefTitle": "AT"},
                "statusModule": {"overallStatus": "COMPLETED",
                                 "startDateStruct": {"date": "2020-01-01"},
                                 "studyFirstSubmitDate": "2019-06-03",
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
        self.assertEqual(d["registered"], "2019-06-03")
        self.assertTrue(d["prospective"])
        self.assertIsNone(bd._parse_ctgov(None))
        self.assertIsNone(bd._parse_ctgov({}))

    def test_registry_qc_flags_design_contradictions(self):
        def trial(model, alloc, arms=1, per_arm=1):
            return {"trial_key": "NCT1", "details": {
                "model": model, "allocation": alloc,
                "n_arm_groups": arms, "max_interventions_per_arm": per_arm}}
        # a single group has nothing to randomise between
        w = bd._registry_qc([trial("Single Group", "Randomized", 1, 2)])
        self.assertEqual(len(w), 1)
        self.assertIn("mislabelled crossover", w[0])
        # one arm holding several drugs, model not crossover → check it
        w = bd._registry_qc([trial("Parallel", "Randomized", 1, 3)])
        self.assertTrue(any("check whether it is a crossover" in x for x in w))
        # correctly labelled crossover with everything in one arm is fine
        self.assertEqual(bd._registry_qc([trial("Crossover", "Randomized", 1, 4)]), [])
        # missing allocation is reported on its own
        w = bd._registry_qc([trial("Crossover", "", 2, 1)])
        self.assertEqual(len(w), 1)
        self.assertIn("no allocation recorded", w[0])
        # ordinary trials produce nothing, and trials with no details are skipped
        self.assertEqual(bd._registry_qc([trial("Parallel", "Randomized", 2, 1)]), [])
        self.assertEqual(bd._registry_qc([{"trial_key": "X", "details": None}]), [])

    def test_build_trials_offline(self):
        # fetch=False → never hits the network; uses cache only if present
        studies = [
            {"covidence_id": 1, "trial_key": "NCT01211405", "registry_norm": "NCT01211405"},
            {"covidence_id": 2, "trial_key": "NL123", "registry_norm": "NL123"},
            {"covidence_id": 3, "trial_key": None, "registry_norm": ""},        # no identifier
            {"covidence_id": 4, "trial_key": "doi:10.1/src", "registry_norm": ""},
        ]
        trials = bd.build_trials(studies, fetch=False)
        self.assertEqual({t["trial_key"] for t in trials},
                         {"NCT01211405", "NL123", "doi:10.1/src"})  # excludes #3
        nl = next(t for t in trials if t["trial_key"] == "NL123")
        self.assertEqual(nl["fetch_status"], "unsupported_registry")
        self.assertIsNone(nl["details"])
        unreg = next(t for t in trials if t["trial_key"] == "doi:10.1/src")
        self.assertEqual(unreg["fetch_status"], "unregistered")
        self.assertEqual(unreg["registry_url"], "https://doi.org/10.1/src")
        self.assertIsNone(unreg["details"])
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
        core = {"covidence_id", "study_id", "title", "drug", "drugs", "indication",
                "extracted", "outcome_domains", "outcome_measures", "phase",
                "registration_status", "n_randomized", "n_analyzed", "url"}
        for s in self.studies:
            self.assertTrue(core <= set(s), f"missing keys in {s.get('study_id')}")

    def test_extracted_studies_are_complete(self):
        for s in self.studies:
            if not s["extracted"]:
                continue
            self.assertTrue(s["reviewer"], f"{s['study_id']} extracted w/o reviewer")
            # an extracted drug cell must drive the facet
            if s["drugs_raw"]:
                self.assertEqual(s["drug_source"], "extracted")
                self.assertTrue(s["drugs"])
            # outcome domains come from the controlled column set only
            self.assertTrue(set(s["outcome_domains"]) <= set(bd.OUTCOME_DOMAINS))
            self.assertEqual(len(s["outcome_measures"]) >= len(s["outcome_domains"]), True)

    def test_only_consensus_rows_populate_the_database(self):
        """One row per study, all from the configured consensus reviewer."""
        if not bd.CONSENSUS_REVIEWER:
            self.skipTest("consensus filtering disabled")
        ext = [s for s in self.studies if s["extracted"]]
        self.assertTrue(ext, "no extracted studies")
        for s in ext:
            self.assertEqual(s["reviewer"], bd.CONSENSUS_REVIEWER)
        ids = [s["covidence_id"] for s in ext]
        self.assertEqual(len(ids), len(set(ids)))
        cov = self.meta["extraction_coverage"]
        self.assertEqual(cov["studies_with_consensus_row"], len(ext))
        # the other reviewers' rows are counted, not discarded silently
        self.assertGreaterEqual(cov["rows"], cov["studies_with_any_extraction"])
        self.assertGreaterEqual(cov["studies_with_any_extraction"], len(ext))

    def test_in_progress_rows_are_tracked_not_warned(self):
        """Rows with blank outcome columns are extraction progress, not errors.

        Only the consensus reviewer's rows are verified complete; everyone else's
        are legitimately mid-extraction. The count is tracked so outcome-domain
        figures can be computed over verified rows, but it must never be reported
        as a data-quality warning.
        """
        cov = self.meta["extraction_coverage"]
        self.assertIn("rows_missing_outcomes", cov)
        total = sum(cov["rows_missing_outcomes"].values())
        self.assertLessEqual(total, cov["rows"])
        for who, n in cov["rows_missing_outcomes"].items():
            self.assertLessEqual(n, cov["reviewers"][who])
        self.assertFalse([w for w in self.meta["warnings"] if "outcome column" in w],
                         "in-progress rows must not be raised as data-quality warnings")

    def test_consensus_rows_have_outcomes(self):
        """The rows that reach the database are the verified-complete ones."""
        if not bd.CONSENSUS_REVIEWER:
            self.skipTest("consensus filtering disabled")
        ext = [s for s in self.studies if s["extracted"]]
        blank = [s["study_id"] for s in ext if not s["outcome_domains"]]
        self.assertEqual(blank, [], f"consensus rows with no outcome domains: {blank}")

    def test_pending_studies_carry_no_extraction_fields(self):
        for s in self.studies:
            if not s["extracted"]:
                self.assertEqual(s["outcome_domains"], [])
                self.assertEqual(s["reviewer"], "")
                self.assertIn(s["drug_source"], ("auto", "unknown"))

    def test_sample_size_coalesces(self):
        for s in self.studies:
            if s["n_randomized"] is not None:
                self.assertEqual((s["n"], s["n_source"]), (s["n_randomized"], "randomized"))
            elif s["n_analyzed"] is not None:
                self.assertEqual((s["n"], s["n_source"]), (s["n_analyzed"], "analyzed"))
            else:
                self.assertIsNone(s["n"])

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

    def test_meta_facet_vocabularies_match_the_studies(self):
        self.assertEqual(set(self.meta["outcome_domains"]),
                         {d for s in self.studies for d in s["outcome_domains"]})
        # domain facet keeps template order, not alphabetical
        self.assertEqual(self.meta["outcome_domains"],
                         [d for d in bd.OUTCOME_DOMAINS if d in self.meta["outcome_domains"]])
        self.assertEqual(set(self.meta["outcome_measures"]),
                         {m for s in self.studies for m in s["outcome_measures"]})
        self.assertEqual(set(self.meta["drugs"]), {d for s in self.studies for d in s["drugs"]})
        self.assertEqual(set(self.meta["phases"]), {s["phase"] for s in self.studies if s["phase"]})

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
            # a registered study keys on its registry id
            if s["registry_norm"]:
                self.assertEqual(s["trial_key"], s["registry_norm"])
        # every trial key is represented in trials[]
        keys = {s["trial_key"] for s in self.studies if s["trial_key"]}
        self.assertEqual(keys, {t["trial_key"] for t in self.out["trials"]})
        self.assertEqual(self.meta["registries"],
                         sorted({s["registry_norm"] for s in self.studies if s["registry_norm"]}))
        self.assertLessEqual(self.meta["n_trials"], self.meta["n_included"])
        self.assertEqual(self.meta["n_registered_trials"] + self.meta["n_unregistered_trials"],
                         len(self.out["trials"]))

    def test_registration_status_is_consistent(self):
        for s in self.studies:
            self.assertIn(s["registration_status"], ("registered", "unregistered", "unknown"))
            self.assertEqual(s["registration_status"] == "registered", bool(s["registry_norm"]))

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
        for k in ("records_identified", "duplicates_removed", "auto_marked_ineligible",
                  "excluded_title_abstract", "records_screened",
                  "removed_before_screening", "complete", "reconciles"):
            self.assertIn(k, m)

    def test_prisma_manual_reconciles(self):
        """The committed upstream numbers must agree with the stage exports."""
        m = self.prisma["manual"]
        if not m["complete"]:
            self.skipTest("upstream PRISMA counts not yet entered")
        self.assertEqual(m["removed_before_screening"],
                         m["duplicates_removed"] + m["auto_marked_ineligible"])
        # PRISMA 2020 counts automation removals BEFORE screening, so `screened`
        # excludes them and equals identified − removed = in-review + excluded-at-TA.
        self.assertEqual(m["records_screened"],
                         self.prisma["records_in_review"] + m["excluded_title_abstract"])
        self.assertEqual(m["records_screened"],
                         m["records_identified"] - m["removed_before_screening"])
        self.assertEqual(m["reconcile_delta"], 0)
        self.assertTrue(m["reconciles"])

    def _prisma_with(self, payload):
        """build_prisma() against a temporary prisma_manual.json."""
        import json
        import tempfile
        orig = bd.MANUAL_PATH
        tmp = None
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
                json.dump(payload, fh)
                tmp = fh.name
            bd.MANUAL_PATH = tmp
            return bd.build_prisma(4)
        finally:
            bd.MANUAL_PATH = orig
            if tmp:
                os.unlink(tmp)

    def test_prisma_manual_when_supplied(self):
        n = self.prisma["records_in_review"]
        m = self._prisma_with({"records_identified": n + 5820, "duplicates_removed": 900,
                               "auto_marked_ineligible": 4920,
                               "excluded_title_abstract": 0})["manual"]
        self.assertTrue(m["complete"])
        self.assertEqual(m["removed_before_screening"], 5820)
        self.assertEqual(m["records_screened"], n)
        self.assertTrue(m["reconciles"])

    def test_prisma_manual_accepts_hyphenated_keys(self):
        """A hand-edited file may write `auto-marked-ineligible`; both forms work."""
        n = self.prisma["records_in_review"]
        m = self._prisma_with({"records_identified": n + 30, "duplicates_removed": 10,
                               "auto-marked-ineligible": 20,
                               "excluded_title_abstract": 0})["manual"]
        self.assertEqual(m["auto_marked_ineligible"], 20)
        self.assertTrue(m["reconciles"])

    def test_prisma_mismatch_is_reported_not_hidden(self):
        n = self.prisma["records_in_review"]
        m = self._prisma_with({"records_identified": n + 107, "duplicates_removed": 100,
                               "auto_marked_ineligible": 0,
                               "excluded_title_abstract": 0})["manual"]
        self.assertFalse(m["reconciles"])
        self.assertEqual(m["reconcile_delta"], 7)

    def test_prisma_incomplete_when_a_number_is_missing(self):
        m = self._prisma_with({"records_identified": 100, "duplicates_removed": 10,
                               "excluded_title_abstract": 5})["manual"]   # no automation count
        self.assertFalse(m["complete"])
        self.assertIsNone(m["removed_before_screening"])
        self.assertIsNone(m["reconciles"])


    # ---- current-fixture counts (update when the Covidence exports change) ----
    def test_current_counts(self):
        self.assertEqual(self.meta["n_included"], 95)
        self.assertEqual(self.meta["n_extracted"], 16)
        self.assertEqual(self.meta["consensus_reviewer"], "Parker Singleton")
        self.assertEqual(self.meta["extraction_coverage"]["rows"], 61)
        self.assertEqual(self.meta["extraction_coverage"]["studies_with_any_extraction"], 45)
        p = self.prisma
        self.assertEqual(p["records_in_review"], 2186)
        self.assertEqual(p["in_screening"], 1270)
        self.assertEqual(p["advanced_to_fulltext"], 916)
        self.assertEqual(p["included"], 95)
        self.assertEqual(p["fulltext_excluded"], 11)
        self.assertEqual(p["fulltext_in_review"], 810)


if __name__ == "__main__":
    unittest.main(verbosity=2)
