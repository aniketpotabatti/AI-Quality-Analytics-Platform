"""Tests for evaluation pipeline."""

import pytest

from evaluation_engine.core.pipeline import EvaluationPipeline
from evaluation_engine.metrics.base import Metric
from evaluation_engine.schemas import EvaluationInput, MetricName, MetricResult


class StubMetric(Metric):
    name = MetricName.FAITHFULNESS

    async def evaluate(self, evaluation_input: EvaluationInput) -> MetricResult:
        _ = evaluation_input
        return MetricResult(
            metric=self.name,
            score=0.85,
            passed=True,
            rationale="Stub metric",
        )


@pytest.mark.asyncio
async def test_pipeline_averages_metric_scores() -> None:
    pipeline = EvaluationPipeline(metrics=[StubMetric()])
    result = await pipeline.run(
        EvaluationInput(
            prompt="What is the capital of France?",
            response="Paris is the capital of France.",
        )
    )

    assert result.overall_score == 0.85
    assert len(result.metrics) == 1
    assert result.metrics[0].passed is True
