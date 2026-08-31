"""Evaluation pipeline orchestration."""

from evaluation_engine.metrics.base import Metric
from evaluation_engine.schemas import EvaluationInput, EvaluationResult, MetricResult


class EvaluationPipeline:
    """Runs a set of metrics against a single evaluation input."""

    def __init__(self, metrics: list[Metric]) -> None:
        self._metrics = metrics

    async def run(self, evaluation_input: EvaluationInput) -> EvaluationResult:
        results: list[MetricResult] = []
        for metric in self._metrics:
            results.append(await metric.evaluate(evaluation_input))

        overall = sum(r.score for r in results) / len(results) if results else 0.0
        return EvaluationResult(input=evaluation_input, metrics=results, overall_score=overall)
