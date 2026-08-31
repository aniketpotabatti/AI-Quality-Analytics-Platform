"""ARQ async worker definitions for evaluation jobs."""

from __future__ import annotations

import structlog
from arq.connections import RedisSettings

from has_api.config import get_settings

logger = structlog.get_logger()


async def run_evaluation(ctx: dict, run_id: str) -> dict[str, str]:
    """Execute an evaluation run against all test cases."""
    log = logger.bind(run_id=run_id)
    log.info("evaluation_worker_start")

    try:
        from uuid import UUID

        from has_api.domain.value_objects import EvaluationRunStatus
        from has_api.infrastructure.database.repository_factory import RepositoryContainer
        from has_api.infrastructure.database.session import get_session_factory

        from evaluation_engine.core.pipeline import EvaluationPipeline
        from evaluation_engine.metrics import default_registry
        from evaluation_engine.schemas import EvaluationInput, MetricName

        session_factory = get_session_factory()
        run_uuid = UUID(run_id)

        async with session_factory() as session:
            repos = RepositoryContainer(session)

            # Load run
            # We don't have workspace_id here; use raw query
            from sqlalchemy import select
            from has_api.infrastructure.database.models.evaluations import EvaluationRunModel
            from has_api.infrastructure.database.mappers.evaluations import evaluation_run_to_domain

            result = await session.execute(
                select(EvaluationRunModel).where(EvaluationRunModel.id == run_uuid)
            )
            run_model = result.scalar_one_or_none()
            if run_model is None:
                log.error("evaluation_worker_run_not_found")
                return {"run_id": run_id, "status": "not_found"}

            run = evaluation_run_to_domain(run_model)

            # Update status to running
            from datetime import UTC, datetime
            run.status = EvaluationRunStatus.RUNNING
            run.started_at = datetime.now(UTC)
            run = await repos.evaluation_runs.save(run)
            await session.commit()

            # Load test cases
            test_cases = await repos.test_cases.list_by_dataset(
                run.dataset_id, limit=10000
            )
            run.total_cases = len(test_cases)
            run = await repos.evaluation_runs.save(run)
            await session.commit()

            # Build pipeline from metrics_config
            metrics_config = run.metrics_config
            metric_names_raw = metrics_config.get("metrics", [])
            if not metric_names_raw:
                metric_names_raw = [m.value for m in MetricName]

            metrics = []
            for name in metric_names_raw:
                try:
                    metric_cls = default_registry.get(MetricName(name))
                    metrics.append(metric_cls())
                except (KeyError, ValueError):
                    log.warning("metric_not_found", metric=name)

            if not metrics:
                metrics = default_registry.create_all()

            pipeline = EvaluationPipeline(metrics)

            # Run pipeline for each test case
            completed = 0
            failed = 0

            from has_api.domain.entities import EvaluationResult, MetricScore
            from has_api.domain.value_objects import (
                EvaluationResultStatus,
                MetricType,
            )

            for tc in test_cases:
                eval_input = EvaluationInput(
                    prompt=tc.prompt,
                    response=tc.response,
                    context=tc.context,
                    ground_truth=tc.ground_truth,
                )
                try:
                    eval_result = await pipeline.run(eval_input)

                    # Save EvaluationResult
                    domain_result = EvaluationResult(
                        run_id=run.id,
                        test_case_id=tc.id,
                        status=EvaluationResultStatus.COMPLETED,
                        overall_score=eval_result.overall_score,
                    )
                    domain_result = await repos.evaluation_results.save(domain_result)

                    # Save each MetricScore
                    for mr in eval_result.metrics:
                        score_entity = MetricScore(
                            result_id=domain_result.id,
                            metric_type=MetricType(mr.metric.value),
                            score=mr.score,
                            passed=mr.passed,
                            rationale=mr.rationale,
                            metadata=dict(mr.metadata),
                        )
                        await repos.evaluation_results.save_score(score_entity)

                    completed += 1
                except Exception as exc:
                    log.error("test_case_evaluation_failed", test_case_id=str(tc.id), error=str(exc))
                    domain_result = EvaluationResult(
                        run_id=run.id,
                        test_case_id=tc.id,
                        status=EvaluationResultStatus.FAILED,
                        error_message=str(exc)[:500],
                    )
                    await repos.evaluation_results.save(domain_result)
                    failed += 1

                # Update progress every 10 cases
                if (completed + failed) % 10 == 0:
                    run.completed_cases = completed
                    run.failed_cases = failed
                    await repos.evaluation_runs.save(run)
                    await session.commit()

            # Final update
            run.status = EvaluationRunStatus.COMPLETED
            run.completed_cases = completed
            run.failed_cases = failed
            run.completed_at = datetime.now(UTC)
            await repos.evaluation_runs.save(run)
            await session.commit()

            log.info("evaluation_worker_done", completed=completed, failed=failed)
            return {"run_id": run_id, "status": "completed", "completed": str(completed), "failed": str(failed)}

    except Exception as exc:
        log.exception("evaluation_worker_error", error=str(exc))
        return {"run_id": run_id, "status": "error", "error": str(exc)}


class WorkerSettings:
    """ARQ worker configuration."""

    functions = [run_evaluation]

    @staticmethod
    def redis_settings() -> RedisSettings:
        settings = get_settings()
        return RedisSettings.from_dsn(str(settings.redis_url))
