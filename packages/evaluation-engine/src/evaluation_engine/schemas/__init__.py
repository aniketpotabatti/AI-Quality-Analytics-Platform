"""Shared schemas for evaluation inputs and outputs."""

from enum import StrEnum

from pydantic import BaseModel, Field


class MetricName(StrEnum):
    FAITHFULNESS = "faithfulness"
    ANSWER_RELEVANCE = "answer_relevance"
    GROUNDEDNESS = "groundedness"
    LLM_AS_JUDGE = "llm_as_judge"


class EvaluationInput(BaseModel):
    """Single test case passed to the evaluation pipeline."""

    prompt: str = Field(min_length=1)
    response: str = Field(min_length=1)
    context: str | None = None
    ground_truth: str | None = None


class MetricResult(BaseModel):
    metric: MetricName
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    rationale: str | None = None
    metadata: dict[str, str | float | bool] = Field(default_factory=dict)


class EvaluationResult(BaseModel):
    """Aggregated result for a single test case."""

    input: EvaluationInput
    metrics: list[MetricResult]
    overall_score: float = Field(ge=0.0, le=1.0)
