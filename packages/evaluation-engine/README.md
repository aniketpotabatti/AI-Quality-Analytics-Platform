# Evaluation Engine

Pure Python library for hallucination and grounding metrics.

Consumed by `apps/api` workers and orchestrator. Has no web framework dependencies.

## Structure

```
src/evaluation_engine/
  core/        Pipeline orchestration
  metrics/     Pluggable metric implementations
  detectors/   Hallucination detection strategies
  schemas/     Input/output models
```

## Development

```bash
uv sync --dev
uv run pytest
```
