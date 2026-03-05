"""Context scoring engine."""

from __future__ import annotations

from dataclasses import dataclass, field

from agentmd.detectors.context_completeness import (
    score_agent_awareness,
    score_clarity,
    score_completeness,
    score_freshness,
    score_specificity,
)


@dataclass
class DimensionResult:
    """Score and suggestions for one scoring dimension."""

    name: str
    score: float          # 0-100
    weight: float         # 0-1
    suggestions: list[str] = field(default_factory=list)

    @property
    def weighted_score(self) -> float:
        return self.score * self.weight


@dataclass
class ScoringResult:
    """Full scoring result for a context file."""

    file_path: str
    dimensions: list[DimensionResult] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    @property
    def composite_score(self) -> float:
        """Weighted composite score 0-100."""
        return sum(d.weighted_score for d in self.dimensions)

    def to_dict(self) -> dict[str, object]:
        return {
            "file_path": self.file_path,
            "composite_score": round(self.composite_score, 1),
            "dimensions": [
                {
                    "name": d.name,
                    "score": round(d.score, 1),
                    "weight": d.weight,
                    "weighted_score": round(d.weighted_score, 1),
                    "suggestions": d.suggestions,
                }
                for d in self.dimensions
            ],
            "suggestions": self.suggestions,
        }


class ContextScorer:
    """Score a context file on five quality dimensions."""

    WEIGHTS = {
        "completeness": 0.30,
        "specificity": 0.25,
        "clarity": 0.20,
        "agent_awareness": 0.15,
        "freshness": 0.10,
    }

    def score(
        self,
        content: str,
        file_path: str = "",
        project_root: str | None = None,
        *,
        minimal: bool = False,
    ) -> ScoringResult:
        """Score *content* and return a :class:`ScoringResult`."""
        result = ScoringResult(file_path=file_path)
        all_suggestions: list[str] = []

        scorers = [
            ("completeness", lambda c: score_completeness(c, minimal=minimal)),
            ("specificity", lambda c: score_specificity(c)),
            ("clarity", lambda c: score_clarity(c)),
            ("agent_awareness", lambda c: score_agent_awareness(c, minimal=minimal)),
            ("freshness", lambda c: score_freshness(c, project_root)),
        ]

        for name, fn in scorers:
            score_val, suggestions = fn(content)
            dim = DimensionResult(
                name=name,
                score=score_val,
                weight=self.WEIGHTS[name],
                suggestions=suggestions,
            )
            result.dimensions.append(dim)
            all_suggestions.extend(suggestions)

        result.suggestions = all_suggestions
        return result

    def score_file(self, file_path: str, project_root: str | None = None) -> ScoringResult:
        """Read *file_path* and score it."""
        from pathlib import Path

        content = Path(file_path).read_text(encoding="utf-8")
        return self.score(content, file_path=file_path, project_root=project_root)
