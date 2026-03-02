"""Tests for the context scorer (D3)."""

from __future__ import annotations

import pytest

from agentmd.scorer import ContextScorer, ScoringResult, DimensionResult
from agentmd.detectors.context_completeness import (
    score_completeness,
    score_specificity,
    score_clarity,
    score_agent_awareness,
    score_freshness,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

RICH_CONTENT = """
# Project Overview

This project uses Python with pytest and ruff.

## Build

```bash
pip install -e .
```

## Testing

```bash
pytest tests/ -q
```

## Linting

```bash
ruff check .
```

## Directory Structure

- `src/` — main source
- `tests/` — unit tests
- `docs/` — documentation

## Conventions

- Follow PEP8 naming conventions
- Import order: stdlib, third-party, local

## Agent Notes

Claude Code users: run `/init` to bootstrap context.
Codex sandbox: bash tool is available. Use AGENTS.md for notes.
"""

POOR_CONTENT = "This project is great. It does stuff."


# ---------------------------------------------------------------------------
# Completeness
# ---------------------------------------------------------------------------

class TestCompletenessScorer:
    def test_rich_content_scores_high(self):
        score, _ = score_completeness(RICH_CONTENT)
        assert score >= 80

    def test_poor_content_scores_low(self):
        score, suggestions = score_completeness(POOR_CONTENT)
        assert score <= 40
        assert suggestions  # should have suggestions

    def test_missing_tests_flagged(self):
        content = "# Project\n\nRun `make build` to build.\n\nCode style: PEP8."
        score, suggestions = score_completeness(content)
        joined = " ".join(suggestions).lower()
        assert "test" in joined

    def test_all_present_scores_100(self):
        content = (
            "pytest jest build make ruff structure src/ tests/ convention naming format"
        )
        score, _ = score_completeness(content)
        assert score == 100.0


# ---------------------------------------------------------------------------
# Specificity
# ---------------------------------------------------------------------------

class TestSpecificityScorer:
    def test_rich_content_scores_high(self):
        score, _ = score_specificity(RICH_CONTENT)
        assert score >= 75

    def test_no_code_blocks_penalised(self):
        content = "# Heading\n\nRun pytest to test things. Use ruff for linting.\n"
        score, suggestions = score_specificity(content)
        joined = " ".join(suggestions).lower()
        assert "code block" in joined

    def test_inline_code_detected(self):
        content = "Run `pytest` and `ruff check .`"
        score, _ = score_specificity(content)
        assert score >= 50


# ---------------------------------------------------------------------------
# Clarity
# ---------------------------------------------------------------------------

class TestClarityScorer:
    def test_rich_content_scores_high(self):
        score, _ = score_clarity(RICH_CONTENT)
        assert score >= 75

    def test_no_headings_penalised(self):
        score, suggestions = score_clarity(POOR_CONTENT)
        joined = " ".join(suggestions).lower()
        assert "heading" in joined

    def test_wall_of_text_penalised(self):
        wall = "\n".join(["Some text line."] * 20)
        score, suggestions = score_clarity(wall)
        joined = " ".join(suggestions).lower()
        assert "wall" in joined or "paragraph" in joined

    def test_bullet_lists_rewarded(self):
        content = "# Heading\n\n## Sub\n\n### More\n\n- item 1\n- item 2\n"
        score, _ = score_clarity(content)
        assert score == 100.0


# ---------------------------------------------------------------------------
# Agent-Awareness
# ---------------------------------------------------------------------------

class TestAgentAwarenessScorer:
    def test_rich_content_scores_high(self):
        score, _ = score_agent_awareness(RICH_CONTENT)
        assert score >= 40

    def test_no_agent_mentions_zero(self):
        score, suggestions = score_agent_awareness(POOR_CONTENT)
        assert score == 0.0
        assert suggestions

    def test_multiple_agents_mentioned(self):
        content = "claude code /init codex agents.md cursor copilot sandbox mcp"
        score, _ = score_agent_awareness(content)
        assert score == 100.0


# ---------------------------------------------------------------------------
# Freshness
# ---------------------------------------------------------------------------

class TestFreshnessScorer:
    def test_no_paths_returns_50(self):
        score, _ = score_freshness("No file references here.", project_root=None)
        assert score == 50.0

    def test_no_project_root_returns_50(self):
        score, _ = score_freshness("See `src/main.py` for details.")
        assert score == 50.0

    def test_existing_files_score_high(self, tmp_path):
        (tmp_path / "main.py").write_text("x = 1")
        content = "See `main.py` for details."
        score, suggestions = score_freshness(content, project_root=str(tmp_path))
        assert score == 100.0
        assert not suggestions

    def test_missing_files_penalised(self, tmp_path):
        content = "See `missing.py` and `gone.py` for details."
        score, suggestions = score_freshness(content, project_root=str(tmp_path))
        assert score < 100.0
        assert suggestions


# ---------------------------------------------------------------------------
# ContextScorer integration
# ---------------------------------------------------------------------------

class TestContextScorer:
    def test_returns_scoring_result(self):
        scorer = ContextScorer()
        result = scorer.score(RICH_CONTENT, file_path="CLAUDE.md")
        assert isinstance(result, ScoringResult)

    def test_five_dimensions(self):
        scorer = ContextScorer()
        result = scorer.score(RICH_CONTENT)
        assert len(result.dimensions) == 5

    def test_dimension_names(self):
        scorer = ContextScorer()
        result = scorer.score(RICH_CONTENT)
        names = {d.name for d in result.dimensions}
        assert names == {"completeness", "specificity", "clarity", "agent_awareness", "freshness"}

    def test_weights_sum_to_one(self):
        total = sum(ContextScorer.WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9

    def test_composite_score_in_range(self):
        scorer = ContextScorer()
        result = scorer.score(RICH_CONTENT)
        assert 0 <= result.composite_score <= 100

    def test_rich_content_composite_higher_than_poor(self):
        scorer = ContextScorer()
        rich = scorer.score(RICH_CONTENT)
        poor = scorer.score(POOR_CONTENT)
        assert rich.composite_score > poor.composite_score

    def test_to_dict_structure(self):
        scorer = ContextScorer()
        d = scorer.score(RICH_CONTENT, file_path="test.md").to_dict()
        assert "composite_score" in d
        assert "dimensions" in d
        assert "suggestions" in d
        assert "file_path" in d

    def test_score_file(self, tmp_path):
        md = tmp_path / "CLAUDE.md"
        md.write_text(RICH_CONTENT)
        scorer = ContextScorer()
        result = scorer.score_file(str(md))
        assert result.file_path == str(md)
        assert result.composite_score > 0
