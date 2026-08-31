"""Groundedness metric: compares response against ground truth."""

from __future__ import annotations

from evaluation_engine.metrics.base import Metric
from evaluation_engine.schemas import EvaluationInput, MetricName, MetricResult


class GroundednessMetric(Metric):
    """
    Groundedness measures similarity between the model response and a
    known ground-truth answer when one is provided.

    When no ground truth is available, returns a neutral 0.5 score.
    Uses normalized token overlap (F1-like) as the similarity measure.
    """

    name = MetricName.GROUNDEDNESS

    async def evaluate(self, evaluation_input: EvaluationInput) -> MetricResult:
        if evaluation_input.ground_truth is None:
            return MetricResult(
                metric=self.name,
                score=0.5,
                passed=True,
                rationale="No ground truth provided — groundedness check skipped",
            )

        score = _f1_token_overlap(
            evaluation_input.response,
            evaluation_input.ground_truth,
        )
        threshold = 0.35
        return MetricResult(
            metric=self.name,
            score=score,
            passed=score >= threshold,
            rationale=f"Token-level F1 vs ground truth: {score:.2f}",
            metadata={"threshold": threshold, "method": "token_f1"},
        )


def _f1_token_overlap(prediction: str, reference: str) -> float:
    """Compute token-level F1 score between prediction and reference."""

    def tokenize(s: str) -> list[str]:
        return s.lower().split()

    pred_tokens = tokenize(prediction)
    ref_tokens = tokenize(reference)

    if not pred_tokens or not ref_tokens:
        return 0.0

    pred_set = set(pred_tokens)
    ref_set = set(ref_tokens)

    common = pred_set & ref_set
    if not common:
        return 0.0

    precision = len(common) / len(pred_set)
    recall = len(common) / len(ref_set)
    f1 = 2 * precision * recall / (precision + recall)
    return f1
