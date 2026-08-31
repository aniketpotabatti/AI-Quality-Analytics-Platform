"""Answer relevance metric: checks if the response is relevant to the prompt."""

from __future__ import annotations

from evaluation_engine.metrics.base import Metric
from evaluation_engine.schemas import EvaluationInput, MetricName, MetricResult


class AnswerRelevanceMetric(Metric):
    """
    Answer relevance measures how well the response addresses the prompt.

    Uses keyword overlap between response and prompt as a proxy for relevance.
    Higher overlap with key prompt terms = more relevant answer.
    """

    name = MetricName.ANSWER_RELEVANCE

    async def evaluate(self, evaluation_input: EvaluationInput) -> MetricResult:
        score = _relevance_score(
            evaluation_input.response,
            evaluation_input.prompt,
        )
        threshold = 0.3
        return MetricResult(
            metric=self.name,
            score=score,
            passed=score >= threshold,
            rationale=f"Response-to-prompt keyword overlap: {score:.2f}",
            metadata={"threshold": threshold, "method": "keyword_overlap"},
        )


def _relevance_score(response: str, prompt: str) -> float:
    """Measure how much of the prompt's key terms appear in the response."""
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
        "to", "for", "of", "and", "or", "but", "with", "by", "from", "as",
        "that", "this", "it", "its", "what", "how", "why", "when", "where",
        "who", "which", "do", "does", "did", "can", "could", "please",
    }

    def tokenize(s: str) -> set[str]:
        tokens = s.lower().split()
        return {t.strip(".,;:!?\"'()[]{}?") for t in tokens if t not in stop_words and len(t) > 2}

    prompt_tokens = tokenize(prompt)
    resp_tokens = tokenize(response)

    if not prompt_tokens:
        return 1.0  # No meaningful prompt — vacuously relevant

    overlap = prompt_tokens & resp_tokens
    coverage = len(overlap) / len(prompt_tokens)

    # Also reward non-trivially long responses
    length_bonus = min(len(response) / 200, 0.2)  # up to 0.2 bonus for length
    return min(coverage + length_bonus, 1.0)
