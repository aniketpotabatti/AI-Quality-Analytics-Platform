"""Faithfulness metric: checks if response claims are grounded in the context."""

from __future__ import annotations

from evaluation_engine.metrics.base import Metric
from evaluation_engine.schemas import EvaluationInput, MetricName, MetricResult


class FaithfulnessMetric(Metric):
    """
    Faithfulness measures whether all claims in the response are supported
    by the provided context (RAG grounding check).

    When no context is provided, returns a neutral 0.5 score.
    Uses keyword overlap as a lightweight proxy for claim-context alignment.
    """

    name = MetricName.FAITHFULNESS

    async def evaluate(self, evaluation_input: EvaluationInput) -> MetricResult:
        if evaluation_input.context is None:
            return MetricResult(
                metric=self.name,
                score=0.5,
                passed=True,
                rationale="No context provided — faithfulness check skipped",
            )

        score = _keyword_overlap_score(
            evaluation_input.response,
            evaluation_input.context,
        )
        threshold = 0.4
        return MetricResult(
            metric=self.name,
            score=score,
            passed=score >= threshold,
            rationale=f"Keyword overlap between response and context: {score:.2f}",
            metadata={"threshold": threshold, "method": "keyword_overlap"},
        )


def _keyword_overlap_score(text: str, reference: str) -> float:
    """Jaccard-like keyword overlap as a faithfulness proxy."""
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
        "to", "for", "of", "and", "or", "but", "with", "by", "from", "as",
        "that", "this", "it", "its", "be", "been", "being", "have", "has",
        "had", "do", "does", "did", "will", "would", "could", "should",
    }

    def tokenize(s: str) -> set[str]:
        tokens = s.lower().split()
        return {t.strip(".,;:!?\"'()[]{}") for t in tokens if t not in stop_words and len(t) > 2}

    resp_tokens = tokenize(text)
    ctx_tokens = tokenize(reference)

    if not resp_tokens:
        return 0.0

    overlap = resp_tokens & ctx_tokens
    return min(len(overlap) / len(resp_tokens), 1.0)
