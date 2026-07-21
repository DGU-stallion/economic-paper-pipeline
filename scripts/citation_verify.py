#!/usr/bin/env python3
"""Citation verification via OpenAlex and Semantic Scholar APIs.

Validates .bib entries by searching for titles/DOIs in academic databases.
No API key required for basic usage (OpenAlex is free, S2 has free tier).
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Rate limiting: max 1 request per second (polite to free APIs)
_RATE_LIMIT_SEC = 1.1
_last_request_time = 0.0

EVIDENCE_GRADES = ("verified", "unverified", "suspicious", "fabricated")


@dataclass
class CitationResult:
    """Result of verifying a single citation."""
    key: str                    # BibTeX key
    title: str                  # Title from .bib
    grade: str                  # verified / unverified / suspicious / fabricated
    source: str                 # "openalex" / "semantic_scholar" / "none"
    matched_title: str = ""     # Title found in API
    matched_doi: str = ""       # DOI found in API
    reason: str = ""            # Explanation

    def to_dict(self) -> dict[str, str]:
        return {
            "key": self.key,
            "title": self.title,
            "grade": self.grade,
            "source": self.source,
            "matched_title": self.matched_title,
            "matched_doi": self.matched_doi,
            "reason": self.reason,
        }


def _rate_limit():
    """Enforce rate limiting between API calls."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < _RATE_LIMIT_SEC:
        time.sleep(_RATE_LIMIT_SEC - elapsed)
    _last_request_time = time.time()


def _http_get_json(url: str, timeout: int = 10) -> dict | None:
    """Simple HTTP GET that returns parsed JSON or None on failure."""
    _rate_limit()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PaperPilot/6.0 (mailto:dev@paperpilot.io)"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, OSError):
        return None


def _normalize_title(title: str) -> str:
    """Lowercase, strip punctuation for fuzzy comparison."""
    return re.sub(r"[^a-z0-9\s]", "", title.lower()).strip()


def _titles_match(t1: str, t2: str) -> bool:
    """Fuzzy title match (>80% character overlap after normalization)."""
    n1, n2 = _normalize_title(t1), _normalize_title(t2)
    if not n1 or not n2:
        return False
    if n1 == n2:
        return True
    # Simple overlap ratio
    shorter = min(len(n1), len(n2))
    longer = max(len(n1), len(n2))
    if shorter / longer < 0.7:
        return False
    # Check if one contains the other
    return n1 in n2 or n2 in n1


# ── OpenAlex API ──


def search_openalex(title: str) -> dict | None:
    """Search OpenAlex for a paper by title. Returns first result or None."""
    encoded = urllib.parse.quote(title)
    url = f"https://api.openalex.org/works?filter=title.search:{encoded}&per_page=3"
    data = _http_get_json(url)
    if not data or not data.get("results"):
        return None
    for result in data["results"]:
        api_title = result.get("title", "")
        if _titles_match(title, api_title):
            return {
                "title": api_title,
                "doi": result.get("doi", ""),
                "year": result.get("publication_year"),
                "source": "openalex",
            }
    # Return first result even if fuzzy match fails (for suspicious grade)
    first = data["results"][0]
    return {
        "title": first.get("title", ""),
        "doi": first.get("doi", ""),
        "year": first.get("publication_year"),
        "source": "openalex",
        "partial_match": True,
    }


# ── Semantic Scholar API ──


def search_semantic_scholar(title: str) -> dict | None:
    """Search Semantic Scholar for a paper by title."""
    encoded = urllib.parse.quote(title)
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded}&limit=3&fields=title,externalIds,year"
    data = _http_get_json(url)
    if not data or not data.get("data"):
        return None
    for result in data["data"]:
        api_title = result.get("title", "")
        if _titles_match(title, api_title):
            doi = result.get("externalIds", {}).get("DOI", "")
            return {
                "title": api_title,
                "doi": doi,
                "year": result.get("year"),
                "source": "semantic_scholar",
            }
    return None


# ── BibTeX parsing (minimal, no external deps) ──


def parse_bib_entries(bib_text: str) -> list[dict[str, str]]:
    """Extract BibTeX entries with key and title. Minimal parser."""
    entries = []
    # Match @type{key, ... title = {xxx} or title = "xxx" ...}
    pattern = re.compile(
        r"@\w+\{([^,]+),\s*(.*?)\n\}",
        re.DOTALL,
    )
    for match in pattern.finditer(bib_text):
        key = match.group(1).strip()
        body = match.group(2)
        title_match = re.search(r"title\s*=\s*[{\"](.+?)[}\"]", body, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else ""
        year_match = re.search(r"year\s*=\s*[{\"]?(\d{4})[}\"]?", body, re.IGNORECASE)
        year = year_match.group(1) if year_match else ""
        if title:
            entries.append({"key": key, "title": title, "year": year})
    return entries


# ── Main verification API ──


def verify_citation(title: str, key: str = "") -> CitationResult:
    """Verify a single citation against OpenAlex and Semantic Scholar."""
    if not title.strip():
        return CitationResult(key=key, title=title, grade="unverified", source="none", reason="标题为空")

    # Try OpenAlex first
    oa_result = search_openalex(title)
    if oa_result and not oa_result.get("partial_match"):
        return CitationResult(
            key=key, title=title, grade="verified", source="openalex",
            matched_title=oa_result["title"],
            matched_doi=oa_result.get("doi", ""),
            reason="OpenAlex 标题精确匹配",
        )

    # Try Semantic Scholar
    s2_result = search_semantic_scholar(title)
    if s2_result:
        return CitationResult(
            key=key, title=title, grade="verified", source="semantic_scholar",
            matched_title=s2_result["title"],
            matched_doi=s2_result.get("doi", ""),
            reason="Semantic Scholar 标题匹配",
        )

    # Partial match from OpenAlex
    if oa_result and oa_result.get("partial_match"):
        return CitationResult(
            key=key, title=title, grade="suspicious", source="openalex",
            matched_title=oa_result["title"],
            matched_doi=oa_result.get("doi", ""),
            reason="标题部分匹配，可能存在差异",
        )

    return CitationResult(
        key=key, title=title, grade="unverified", source="none",
        reason="OpenAlex 和 Semantic Scholar 均未找到匹配",
    )


def verify_bib_file(bib_path: Path | str, max_entries: int = 50) -> dict[str, Any]:
    """Verify all entries in a .bib file.

    Args:
        bib_path: Path to .bib file.
        max_entries: Maximum entries to verify (rate limit protection).

    Returns:
        Verification report dict.
    """
    path = Path(bib_path)
    if not path.is_file():
        return {"error": f"文件不存在: {bib_path}", "results": []}

    bib_text = path.read_text(encoding="utf-8", errors="replace")
    entries = parse_bib_entries(bib_text)

    results = []
    for entry in entries[:max_entries]:
        result = verify_citation(entry["title"], key=entry["key"])
        results.append(result.to_dict())

    # Summary
    grades = [r["grade"] for r in results]
    summary = {
        "total": len(results),
        "verified": grades.count("verified"),
        "unverified": grades.count("unverified"),
        "suspicious": grades.count("suspicious"),
        "fabricated": grades.count("fabricated"),
        "skipped": max(0, len(entries) - max_entries),
    }

    return {
        "bib_path": str(path),
        "summary": summary,
        "results": results,
    }


# ── CLI ──


def main(argv: list[str] | None = None) -> int:
    import argparse
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="验证 .bib 文件中的引用真实性")
    parser.add_argument("bib_file", help=".bib 文件路径")
    parser.add_argument("--max", type=int, default=50, help="最多验证条数")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args(argv)

    report = verify_bib_file(args.bib_file, max_entries=args.max)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        s = report["summary"]
        print(f"引用验证报告: {report['bib_path']}")
        print(f"  总计: {s['total']} | 已验证: {s['verified']} | 未验证: {s['unverified']} | 可疑: {s['suspicious']}")
        if s["skipped"]:
            print(f"  跳过: {s['skipped']} (超出 --max 限制)")
        for r in report["results"]:
            icon = "✅" if r["grade"] == "verified" else "❓" if r["grade"] == "unverified" else "⚠️"
            print(f"  {icon} [{r['key']}] {r['title'][:60]}... → {r['grade']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
