#!/usr/bin/env python3
"""Tests for citation verification (unit tests with mocked API)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.citation_verify import (
    CitationResult,
    _normalize_title,
    _titles_match,
    parse_bib_entries,
    verify_bib_file,
    verify_citation,
)


class TitleMatchTests(unittest.TestCase):
    def test_exact_match(self):
        self.assertTrue(_titles_match(
            "Digital Economy and Employment",
            "digital economy and employment",
        ))

    def test_partial_overlap(self):
        self.assertTrue(_titles_match(
            "The Impact of Digital Economy on Employment Structure",
            "The Impact of Digital Economy on Employment Structure: Evidence from China",
        ))

    def test_no_match(self):
        self.assertFalse(_titles_match(
            "Machine Learning for Finance",
            "Quantum Computing in Healthcare",
        ))

    def test_empty_title(self):
        self.assertFalse(_titles_match("", "something"))


class BibParserTests(unittest.TestCase):
    def test_parse_basic_entries(self):
        bib = '''@article{smith2020,
  title = {Digital Economy and Employment},
  author = {Smith, John},
  year = {2020},
  journal = {JDE}
}

@inproceedings{jones2021,
  title = "Machine Learning in Economics",
  author = "Jones, Alice",
  year = "2021"
}
'''
        entries = parse_bib_entries(bib)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["key"], "smith2020")
        self.assertEqual(entries[0]["title"], "Digital Economy and Employment")
        self.assertEqual(entries[0]["year"], "2020")
        self.assertEqual(entries[1]["key"], "jones2021")

    def test_parse_empty_bib(self):
        entries = parse_bib_entries("")
        self.assertEqual(entries, [])


class VerifyCitationTests(unittest.TestCase):
    @patch("scripts.citation_verify.search_openalex")
    @patch("scripts.citation_verify.search_semantic_scholar")
    def test_verified_via_openalex(self, mock_s2, mock_oa):
        mock_oa.return_value = {
            "title": "Digital Economy and Employment",
            "doi": "10.1234/test",
            "source": "openalex",
        }
        mock_s2.return_value = None

        result = verify_citation("Digital Economy and Employment", key="test1")
        self.assertEqual(result.grade, "verified")
        self.assertEqual(result.source, "openalex")
        self.assertEqual(result.matched_doi, "10.1234/test")

    @patch("scripts.citation_verify.search_openalex")
    @patch("scripts.citation_verify.search_semantic_scholar")
    def test_verified_via_semantic_scholar(self, mock_s2, mock_oa):
        mock_oa.return_value = None
        mock_s2.return_value = {
            "title": "Causal Inference Methods",
            "doi": "10.5678/s2",
            "source": "semantic_scholar",
        }

        result = verify_citation("Causal Inference Methods", key="ci1")
        self.assertEqual(result.grade, "verified")
        self.assertEqual(result.source, "semantic_scholar")

    @patch("scripts.citation_verify.search_openalex")
    @patch("scripts.citation_verify.search_semantic_scholar")
    def test_unverified_when_no_api_match(self, mock_s2, mock_oa):
        mock_oa.return_value = None
        mock_s2.return_value = None

        result = verify_citation("Completely Fabricated Paper Title", key="fake")
        self.assertEqual(result.grade, "unverified")

    @patch("scripts.citation_verify.search_openalex")
    @patch("scripts.citation_verify.search_semantic_scholar")
    def test_suspicious_on_partial_match(self, mock_s2, mock_oa):
        mock_oa.return_value = {
            "title": "Something Else Entirely",
            "doi": "",
            "source": "openalex",
            "partial_match": True,
        }
        mock_s2.return_value = None

        result = verify_citation("My Paper Title", key="p1")
        self.assertEqual(result.grade, "suspicious")

    def test_empty_title_is_unverified(self):
        result = verify_citation("", key="empty")
        self.assertEqual(result.grade, "unverified")


class VerifyBibFileTests(unittest.TestCase):
    @patch("scripts.citation_verify.verify_citation")
    def test_verify_bib_file_produces_report(self, mock_verify):
        mock_verify.return_value = CitationResult(
            key="test", title="Test Paper", grade="verified",
            source="openalex", matched_title="Test Paper",
            matched_doi="10.1/x", reason="matched",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
            f.write('@article{test,\n  title = {Test Paper},\n  year = {2024}\n}\n')
            f.flush()
            report = verify_bib_file(f.name)

        self.assertEqual(report["summary"]["total"], 1)
        self.assertEqual(report["summary"]["verified"], 1)
        self.assertEqual(report["results"][0]["grade"], "verified")

    def test_nonexistent_file_returns_error(self):
        report = verify_bib_file("/nonexistent/path.bib")
        self.assertIn("error", report)


if __name__ == "__main__":
    unittest.main()
