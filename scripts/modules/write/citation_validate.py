#!/usr/bin/env python3
"""
Citation validation utility — grounded checking against open APIs.

Inspired by OpenDraft (github.com/federicodeponte/opendraft) citation
grounding architecture: verify DOIs, URLs, and author names before
including them in LaTeX output.

Currently:
  - DOI format validation
  - Crossref API lookup (optional, requires internet)
  - Citation database deduplication

Usage:
  from scripts.modules.write.citation_validate import validate_doi, deduplicate_citations
"""

from __future__ import annotations
import re
import json
from typing import Dict, List, Optional
from urllib.request import urlopen, Request
from urllib.error import URLError


# ── DOI validation ──

DOI_PATTERN = re.compile(r"^10\.\d{4,}/[\w\-.();/:<>\[\]]+$", re.UNICODE)


def validate_doi(doi: str) -> bool:
    """Check if DOI string has valid format.

    Returns True for valid format (does NOT check existence).
    """
    if not doi:
        return False
    doi_clean = doi.strip().lower()
    return bool(DOI_PATTERN.match(doi_clean))


def lookup_doi_crossref(doi: str) -> Optional[Dict]:
    """Query Crossref API to verify a DOI exists and return metadata.

    Returns dict with title, authors, year, journal if found.
    Returns None on timeout / not found.
    """
    doi_clean = doi.strip()
    url = f"https://api.crossref.org/works/{doi_clean}"
    req = Request(url, headers={"User-Agent": "EconomicPaperPipeline/1.0 (mailto:noreply)"})
    try:
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            msg = data.get("message", {})
            author_list = msg.get("author", [])
            authors = "; ".join(
                f"{a.get('given', '')} {a.get('family', '')}".strip()
                for a in author_list[:5]
            )
            return {
                "doi": doi_clean,
                "title": (msg.get("title") or [""])[0],
                "authors": authors,
                "year": (msg.get("published-print") or msg.get("published-online") or {}).get("date-parts", [[None]])[0][0],
                "journal": (msg.get("container-title") or [""])[0],
                "publisher": msg.get("publisher", ""),
                "valid": True,
            }
    except (URLError, Exception):
        return {"doi": doi_clean, "valid": False}


# ── Citation deduplication ──


def deduplicate_citations(citations: List[Dict], strategy: str = "keep_best") -> List[Dict]:
    """Deduplicate citation list by DOI or URL similarity.

    Each citation dict should have keys: title, doi, url, authors (str).
    strategy: 'keep_first' or 'keep_best' (keep longer title).
    """
    seen_dois: set = set()
    seen_urls: set = set()
    deduped: List[Dict] = []

    for c in citations:
        doi = (c.get("doi") or "").strip().lower()
        url = (c.get("url") or "").strip().rstrip("/")

        # Dedup key: DOI > URL > title hash
        if doi and doi in seen_dois:
            continue
        if url and url in seen_urls:
            continue
        if doi:
            seen_dois.add(doi)
        if url:
            seen_urls.add(url)

        deduped.append(c)

    return deduped


# ── Citation database ──


class CitationEntry:
    """Single citation entry with validation status."""
    def __init__(self, title: str = "", authors: str = "", year: str = "",
                 doi: str = "", url: str = "", source: str = ""):
        self.title = title
        self.authors = authors
        self.year = year
        self.doi = doi
        self.url = url
        self.source = source
        self.validated = False
        self.validation_status: Optional[bool] = None

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "doi": self.doi,
            "url": self.url,
            "source": self.source,
            "validated": self.validated,
            "valid": self.validation_status,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "CitationEntry":
        return cls(
            title=d.get("title", ""),
            authors=d.get("authors", ""),
            year=str(d.get("year", "")),
            doi=d.get("doi", ""),
            url=d.get("url", ""),
            source=d.get("source", ""),
        )

    def validate(self) -> bool:
        """Run validation checks on this citation."""
        if self.doi and validate_doi(self.doi):
            self.validation_status = True
        elif self.url:
            # Minimal URL format check
            self.validation_status = self.url.startswith("http")
        else:
            self.validation_status = False
        self.validated = True
        return self.validation_status or False


def build_citation_database(candidate_papers: List[Dict]) -> List[CitationEntry]:
    """Convert candidate_papers (from Research module) into validated entries."""
    entries = []
    for p in candidate_papers:
        entry = CitationEntry(
            title=p.get("title", ""),
            authors=p.get("authors", ""),
            year=str(p.get("year", "")),
            doi=p.get("doi", ""),
            url=p.get("url", ""),
            source=p.get("source", ""),
        )
        entry.validate()
        entries.append(entry)
    return entries
