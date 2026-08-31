"""Base metric interface and registry."""

from abc import ABC, abstractmethod

from evaluation_engine.schemas import EvaluationInput, MetricName, MetricResult


class Metric(ABC):
    """Pluggable evaluation metric."""

    name: MetricName

    @abstractmethod
    async def evaluate(self, evaluation_input: EvaluationInput) -> MetricResult: ...


class MetricRegistry:
    """Registry for discovering and instantiating metrics by name."""

    def __init__(self) -> None:
        self._metrics: dict[MetricName, type[Metric]] = {}

    def register(self, metric_cls: type[Metric]) -> type[Metric]:
        self._metrics[metric_cls.name] = metric_cls
        return metric_cls

    def get(self, name: MetricName) -> type[Metric]:
        if name not in self._metrics:
            raise KeyError(f"Metric not registered: {name}")
        return self._metrics[name]

    def create_all(self) -> list[Metric]:
        return [cls() for cls in self._metrics.values()]
