"""Evaluation metrics — register all built-in metrics."""

from evaluation_engine.metrics.answer_relevance import AnswerRelevanceMetric
from evaluation_engine.metrics.base import Metric, MetricRegistry
from evaluation_engine.metrics.faithfulness import FaithfulnessMetric
from evaluation_engine.metrics.groundedness import GroundednessMetric
from evaluation_engine.metrics.llm_judge import LlmAsJudgeMetric

# Global registry with all built-in metrics registered
default_registry = MetricRegistry()
default_registry.register(FaithfulnessMetric)
default_registry.register(AnswerRelevanceMetric)
default_registry.register(GroundednessMetric)
default_registry.register(LlmAsJudgeMetric)

__all__ = [
    "AnswerRelevanceMetric",
    "FaithfulnessMetric",
    "GroundednessMetric",
    "LlmAsJudgeMetric",
    "Metric",
    "MetricRegistry",
    "default_registry",
]
