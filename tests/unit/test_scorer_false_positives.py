"""Regression tests for scorer false positives (D5).

Ensures version strings, URLs, and other non-path tokens are NOT penalized
by the freshness scorer, while real missing/present file paths are handled
correctly.
"""

from __future__ import annotations

import pytest

from agentmd.detectors.context_completeness import (
    _is_path_candidate,
    score_freshness,
    score_specificity,
)


# ---------------------------------------------------------------------------
# _is_path_candidate unit tests
# ---------------------------------------------------------------------------

class TestIsPathCandidate:
    @pytest.mark.parametrize("s", [
        "v1.0.0",
        "1.2.3",
        "3.10",
        ">=3.10",
        "^2.0",
        "~1.5",
        "!=1.0",
        "12.0.1",
        "0.9.8",
        "v2.0.0-rc1",
        "1.0.0+build",
    ])
    def test_version_strings_are_not_paths(self, s: str) -> None:
        assert not _is_path_candidate(s), f"Expected {s!r} to NOT be a path candidate"

    @pytest.mark.parametrize("s", [
        "https://example.com/file.txt",
        "http://docs.python.org/3.10",
        "https://github.com/user/repo",
    ])
    def test_urls_are_not_paths(self, s: str) -> None:
        assert not _is_path_candidate(s), f"Expected {s!r} to NOT be a path candidate"

    @pytest.mark.parametrize("s", [
        "user@example.com",
        "me@host.org",
    ])
    def test_emails_are_not_paths(self, s: str) -> None:
        assert not _is_path_candidate(s), f"Expected {s!r} to NOT be a path candidate"

    @pytest.mark.parametrize("s", [
        "src/main.py",
        "tests/unit/test_scorer.py",
        "README.md",
        "pyproject.toml",
        "./setup.cfg",
        "lib/utils.js",
        "agentmd/scorer.py",
    ])
    def test_real_paths_are_candidates(self, s: str) -> None:
        assert _is_path_candidate(s), f"Expected {s!r} to be a path candidate"


# ---------------------------------------------------------------------------
# score_freshness false positive tests
# ---------------------------------------------------------------------------

class TestFreshnessVersionStrings:
    """Version strings must NOT trigger stale-reference penalties."""

    VERSION_HEAVY_CONTENT = """
# Setup

Requires Python >=3.10 and poetry ^1.2.

Install:

    pip install mypackage==1.0.0

Tested with pytest 7.4.3 and mypy 1.5.1.

Version history: v1.0.0, v0.9.8, v0.9.0.
"""

    def test_no_project_root_returns_50(self) -> None:
        score, _ = score_freshness(self.VERSION_HEAVY_CONTENT, project_root=None)
        assert score == 50.0

    def test_version_strings_dont_penalize_freshness(self, tmp_path) -> None:
        """With a real project root but no actual file refs, should NOT score 0."""
        score, suggestions = score_freshness(self.VERSION_HEAVY_CONTENT, project_root=str(tmp_path))
        # Should be neutral (50) — no real path refs found, not penalized
        assert score == 50.0, f"Expected 50.0, got {score}. Suggestions: {suggestions}"

    def test_semver_range_no_penalty(self, tmp_path) -> None:
        content = "Use Python >=3.10. Also works with 3.11 and 3.12."
        score, suggestions = score_freshness(content, project_root=str(tmp_path))
        assert score == 50.0, f"Version ranges should not be flagged. Got {score}"

    def test_caret_range_no_penalty(self, tmp_path) -> None:
        content = "Requires node ^18.0 and npm ^9.0."
        score, suggestions = score_freshness(content, project_root=str(tmp_path))
        assert score == 50.0, f"Caret ranges should not be flagged. Got {score}"


class TestFreshnessUrls:
    """URLs must NOT trigger stale-reference penalties."""

    def test_https_urls_dont_penalize(self, tmp_path) -> None:
        content = """
See https://docs.python.org/3.10/library/re.html for details.
Also https://github.com/psf/black for formatting.
"""
        score, suggestions = score_freshness(content, project_root=str(tmp_path))
        assert score == 50.0, f"URLs should not be flagged as stale. Got {score}"


class TestFreshnessRealPaths:
    """Real file paths that exist should score well; missing ones should score lower."""

    def test_existing_paths_score_high(self, tmp_path) -> None:
        # Create real files
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("# main")
        (tmp_path / "README.md").write_text("# readme")

        content = "See `src/main.py` and `README.md` for more."
        score, suggestions = score_freshness(content, project_root=str(tmp_path))
        assert score >= 80.0, f"Existing paths should score well. Got {score}"
        assert not any("stale" in s.lower() for s in suggestions)

    def test_missing_paths_score_lower(self, tmp_path) -> None:
        content = "See `src/nonexistent.py` and `lib/ghost.ts` for details."
        score, suggestions = score_freshness(content, project_root=str(tmp_path))
        assert score < 80.0, f"Missing paths should lower the score. Got {score}"

    def test_mixed_paths_partial_score(self, tmp_path) -> None:
        (tmp_path / "real.py").write_text("exists")
        content = "Files: `real.py` and `missing.py`."
        score, suggestions = score_freshness(content, project_root=str(tmp_path))
        # 1 of 2 exist → 50%
        assert 40.0 <= score <= 60.0, f"Mixed paths should give ~50. Got {score}"


# ---------------------------------------------------------------------------
# score_specificity false positive tests
# ---------------------------------------------------------------------------

class TestSpecificityVersionStrings:
    """Version strings should not be the sole reason specificity passes."""

    def test_pure_version_content_low_specificity(self) -> None:
        """Content with only version numbers should not get path-presence credit."""
        content = "Requires 3.10 or 1.2.3 or v2.0.0."
        score, suggestions = score_specificity(content)
        # Without actual paths, code blocks, inline code, or concrete names,
        # should score 0
        assert score == 0.0, f"Pure version strings should not pass specificity. Got {score}"

    def test_real_path_gets_specificity_credit(self) -> None:
        content = "See `src/main.py` for the entry point."
        score, _ = score_specificity(content)
        # Should pass path check (1/4) + inline code check (1/4) = 50
        assert score >= 50.0, f"Real path reference should boost specificity. Got {score}"
